// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZExactLPRewardsCanonical as Records, IExactLPOrdinals, IExactLPVaultState, IExactLPMembership}
    from "./base/ZZZExactLPRewardsCanonical.sol";
import {ExactAsset} from "./libraries/ExactAsset.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";

interface IExactLPRewardsParent {
    function assetCount() external view returns(uint256);
    function assets(uint256) external view returns(address);
    function LP_ALLOCATION_VERSION() external view returns(uint256);
    function liabilities(address) external view returns(uint256);
    function orphaned(address) external view returns(uint256);
    function directLiabilities(address) external view returns(uint256);
    function allocationTree(uint256) external view returns(uint256,uint256,uint256);
    function canonicalBarrier() external view;
    function canonicalSeed(uint256) external view returns(Records.CanonicalSeed memory);
    function canonicalNode(uint256) external view returns(Records.CanonicalNode memory);
    function canonicalWrite(uint8,bytes calldata) external;
    function canonicalSend(address,address,uint256) external;
}

/// @notice Immutable V9 raw-tree codec and exact backing transport for Rewards.
/// @dev The constructing Rewards is the only parent. No delegatecall, arbitrary
/// executor, operator-selected accounting or ordinary payout authority exists.
contract ZZZRewardsCanonical is ZZZModule, ReentrancyGuard {
    IExactLPRewardsParent public immutable rewards;
    address[] private assets;
    uint256[] private amounts;
    uint256[] private parentPrefunds;
    uint256[] private childPrefunds;
    mapping(uint256=>bool) private released;
    mapping(uint256=>bool) private accepted;
    uint256 private nftTotal;
    uint256 private bucketTotal;
    uint256 private assetTotal;
    uint256[4] private buckets;
    uint256[2] private expectedDirect;
    uint256[5][2] private expectedTrees;
    uint256 private cursor;
    bool private captured;
    bool private imported;
    error CanonicalState();

    constructor(address controller) ZZZModule(controller) {
        // Parent runtime is still under construction: msg.sender itself is the
        // immutable identity, not an operator-supplied address or mutable setter.
        rewards=IExactLPRewardsParent(msg.sender);
    }
    receive() external payable {}
    function _state() private view returns(uint8) {
        return IZZZCanonicalAccess(address(access)).canonicalState();
    }
    function _tree(uint256 index) private view returns(uint256 weight,uint256 eth,uint256 zzz) {
        return rewards.allocationTree(index==0?0:buckets[index-1]);
    }
    function _identity() private view {
        IExactLPVaultState vault=IExactLPVaultState(access.module(Ids.VAULT));
        if(rewards.LP_ALLOCATION_VERSION()!=1 || vault.ACCOUNTING_VERSION()!=7 ||
            vault.bucketCount()!=bucketTotal || IExactLPOrdinals(access.module(Ids.NFT)).mintedCount()!=nftTotal)
            revert CanonicalState();
        for(uint256 i;i<4;++i)if(buckets[i]!=(i<bucketTotal?vault.bucketAt(i):0))revert CanonicalState();
    }
    function _roots() private view {
        _identity();
        IExactLPVaultState vault=IExactLPVaultState(access.module(Ids.VAULT));
        (uint256 total,,)=_tree(0);
        if(total!=IExactLPMembership(access.module(Ids.MEMBERSHIP)).totalEligible() || total>1000)
            revert CanonicalState();
        for(uint256 i;i<bucketTotal;++i) {
            (total,,)=_tree(i+1);
            if(vault.bucketAt(i)!=buckets[i] || total!=vault.bucketTotalShares(buckets[i]))revert CanonicalState();
        }
    }
    function _books(bool importing) private view {
        if(rewards.assetCount()!=assetTotal)revert CanonicalState();
        for(uint256 a;a<assetTotal;++a) {
            address token=assets[a];
            if(rewards.assets(a)!=token)revert CanonicalState();
            uint256 total=rewards.directLiabilities(token);
            if(importing && total!=expectedDirect[a])revert CanonicalState();
            for(uint256 t;t<=bucketTotal;++t) {
                (,uint256 eth,uint256 zzz)=_tree(t);uint256 pending=a==0?eth:zzz;
                if(importing && pending!=expectedTrees[a][t])revert CanonicalState();
                total+=pending;
            }
            if(total!=rewards.liabilities(token) || (nftTotal==0 && total!=0))revert CanonicalState();
        }
        if(assetTotal==1)for(uint256 t;t<=bucketTotal;++t) {
            (,,uint256 zzz)=_tree(t);if(zzz!=0)revert CanonicalState();
        }
    }
    function canonicalCapture() external onlyHandoff nonReentrant {
        rewards.canonicalBarrier();
        if(_state()!=1)revert CanonicalState();
        for(uint256 i;i<assets.length;++i){delete released[i];delete accepted[i];}
        delete assets;delete amounts;delete parentPrefunds;delete childPrefunds;
        imported=false;
        nftTotal=IExactLPOrdinals(access.module(Ids.NFT)).mintedCount();
        IExactLPVaultState vault=IExactLPVaultState(access.module(Ids.VAULT));
        bucketTotal=vault.bucketCount();assetTotal=rewards.assetCount();
        if(nftTotal>1000 || bucketTotal>4 || assetTotal==0 || assetTotal>2 || rewards.assets(0)!=address(0))
            revert CanonicalState();
        for(uint256 i;i<4;++i)buckets[i]=i<bucketTotal?vault.bucketAt(i):0;
        for(uint256 a;a<assetTotal;++a) {
            address token=rewards.assets(a);uint256 balance=ExactAsset.balance(token,address(rewards));
            if(balance<rewards.liabilities(token)+rewards.orphaned(token))revert CanonicalState();
            assets.push(token);amounts.push(balance);parentPrefunds.push(0);childPrefunds.push(0);
        }
        _roots();_books(false);captured=true;
    }
    /// @notice Only actual parent cutoff intake extends the captured backing.
    function creditCutoff(address token,uint256 amount) external nonReentrant {
        if(msg.sender!=address(rewards) || !captured || _state()!=1 || amount==0 ||
            !IZZZCanonicalAccess(address(access)).canonicalSettling())revert CanonicalState();
        uint256 index=token==address(0)?0:1;
        if(index>=assetTotal || assets[index]!=token || released[index])revert CanonicalState();
        amounts[index]+=amount;
        if(ExactAsset.balance(token,address(rewards))<amounts[index])revert CanonicalState();
    }
    function canonicalSettle() external onlyHandoff {
        if(!captured || _state()!=1)revert CanonicalState();
    }
    function canonicalCount() public view returns(uint256) {
        return 1+assetTotal+nftTotal+(nftTotal==0?0:2023);
    }
    function canonicalExport(uint256 row) external view returns(bytes memory) {
        if(_reentrancyGuardEntered() || !captured || (_state()!=1 && _state()!=3) || row>=canonicalCount())
            revert CanonicalState();
        if(row==0)return abi.encode(Records.CanonicalHeader(1,assetTotal,bucketTotal,nftTotal,buckets));
        --row;
        if(row<assetTotal) {
            Records.CanonicalAsset memory r;address token=assets[row];
            r.asset=token;r.liability=rewards.liabilities(token);r.orphan=rewards.orphaned(token);
            r.backing=amounts[row];r.directExpected=rewards.directLiabilities(token);
            for(uint256 t;t<=bucketTotal;++t) {
                (,uint256 eth,uint256 zzz)=_tree(t);r.treeExpected[t]=row==0?eth:zzz;
            }
            return abi.encode(r);
        }
        row-=assetTotal;
        if(row<nftTotal) {
            uint256 ordinal=row+1;
            IExactLPOrdinals nft=IExactLPOrdinals(access.module(Ids.NFT));
            uint256 id=nft.tokenAtOrdinal(ordinal);
            Records.CanonicalSeed memory r=rewards.canonicalSeed(id);
            IExactLPVaultState vault=IExactLPVaultState(access.module(Ids.VAULT));
            if(r.id!=id || nft.mintOrdinalOf(id)!=ordinal || r.bucket!=vault.nftBucket(id) ||
                r.shares!=vault.sharesOf(id) || r.eligible!=IExactLPMembership(access.module(Ids.MEMBERSHIP)).eligible(id) ||
                (r.shares!=0)!=r.eligible || (r.bucket!=0)!=r.eligible)revert CanonicalState();
            for(uint256 a;a<2;++a)if((!r.eligible || a>=assetTotal) && r.personal[a]+r.shared[a]!=0)
                revert CanonicalState();
            return abi.encode(r);
        }
        Records.CanonicalNode memory r=rewards.canonicalNode(row-nftTotal+1);
        if(r.node!=row-nftTotal+1)revert CanonicalState();
        return abi.encode(r);
    }

    function canonicalImport(uint256 row,bytes calldata record) external onlyHandoff nonReentrant {
        if(_state()!=2 || row!=cursor++)revert CanonicalState();
        if(row==0) {
            if(record.length!=256)revert CanonicalState();
            Records.CanonicalHeader memory h=abi.decode(record,(Records.CanonicalHeader));
            if(h.version!=1 || h.assetTotal==0 || h.assetTotal>2 || h.bucketTotal>4 || h.nftTotal>1000 ||
                (rewards.assetCount()!=1 && rewards.assetCount()!=h.assetTotal))revert CanonicalState();
            assetTotal=h.assetTotal;bucketTotal=h.bucketTotal;nftTotal=h.nftTotal;buckets=h.buckets;
            _identity();
            // All roots must be empty BEFORE any weight seed or node record.
            for(uint256 t;t<=bucketTotal;++t){(uint256 w,uint256 eth,uint256 zzz)=_tree(t);if(w!=0 || eth!=0 || zzz!=0)revert CanonicalState();}
            imported=true;return;
        }
        if(row>=canonicalCount())revert CanonicalState();
        --row;
        if(row<assetTotal) {
            if(record.length!=320)revert CanonicalState();
            Records.CanonicalAsset memory r=abi.decode(record,(Records.CanonicalAsset));
            if((row==0?r.asset!=address(0):r.asset==address(0)) || r.backing<r.liability+r.orphan)
                revert CanonicalState();
            for(uint256 t=bucketTotal+1;t<5;++t)if(r.treeExpected[t]!=0)revert CanonicalState();
            rewards.canonicalWrite(0,record);
            if(rewards.assets(row)!=r.asset)revert CanonicalState();
            assets.push(r.asset);amounts.push(r.backing);
            parentPrefunds.push(ExactAsset.balance(r.asset,address(rewards)));
            childPrefunds.push(ExactAsset.balance(r.asset,address(this)));
            expectedDirect[row]=r.directExpected;expectedTrees[row]=r.treeExpected;
            return;
        }
        row-=assetTotal;
        if(row<nftTotal) {
            if(record.length!=256)revert CanonicalState();
            Records.CanonicalSeed memory r=abi.decode(record,(Records.CanonicalSeed));
            if(IExactLPOrdinals(access.module(Ids.NFT)).tokenAtOrdinal(row+1)!=r.id)revert CanonicalState();
            rewards.canonicalWrite(1,record);return;
        }
        if(record.length!=992)revert CanonicalState();
        Records.CanonicalNode memory r=abi.decode(record,(Records.CanonicalNode));
        if(r.node!=row-nftTotal+1)revert CanonicalState();
        if(r.node==1)_roots(); // ALL weights must exist before ANY pending/phase.
        rewards.canonicalWrite(2,record);
    }
    function canonicalAssetCount() external view returns(uint256){return assets.length;}
    function canonicalBacking(uint256 index) external view returns(address,uint256){return(assets[index],amounts[index]);}
    function canonicalRelease(uint256 index,address destination) external onlyHandoff nonReentrant {
        uint8 state=_state();
        if((state!=1 && state!=4) || index>=assets.length || released[index] || destination==address(0) ||
            (state==1?!captured:!imported || !accepted[index]))revert CanonicalState();
        released[index]=true;rewards.canonicalSend(assets[index],destination,amounts[index]);
    }
    function _accept(uint256 index,bool restore) private {
        if(msg.value!=0 || index>=assets.length || (!restore && accepted[index]))revert CanonicalState();
        address token=assets[index];uint256 amount=amounts[index];
        if(ExactAsset.balance(token,address(this))<(restore?0:childPrefunds[index])+amount)revert CanonicalState();
        if(!restore)accepted[index]=true;
        ExactAsset.push(token,address(rewards),amount);
        if(ExactAsset.balance(token,address(rewards))<amount+(restore?0:parentPrefunds[index]))revert CanonicalState();
    }
    function canonicalAccept(uint256 index,address) external payable onlyHandoff nonReentrant {
        if(_state()!=2 || !imported)revert CanonicalState();_accept(index,false);
    }
    function canonicalRestore(uint256 index,address) external payable onlyHandoff nonReentrant {
        if(_state()!=1 || !captured || !released[index])revert CanonicalState();
        _accept(index,true);released[index]=false;
    }
    function canonicalValidate() external view {
        if(_reentrancyGuardEntered() || (!captured && !imported) ||
            (_state()==2 && cursor!=canonicalCount()))revert CanonicalState();
        _roots();_books(_state()==2);
        for(uint256 a;a<assets.length;++a)if(ExactAsset.balance(assets[a],address(rewards))<
            amounts[a]+(_state()==2?parentPrefunds[a]:0))revert CanonicalState();
    }
    function canonicalActivate() external onlyHandoff {
        if(_state()!=2 || !imported || cursor!=canonicalCount())revert CanonicalState();
    }
}
