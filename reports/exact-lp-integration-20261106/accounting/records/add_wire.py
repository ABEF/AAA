from pathlib import Path
p=Path('test/ExactLPRewards.t.sol');s=p.read_bytes().decode().replace('import {Test}', 'import {Vm} from "forge-std/Vm.sol";\nimport {Test}',1)
s=s.replace('    event ExactLPColdGas(','''    event ExactLPWire(uint8 indexed stage,bytes logs,bytes snapshot);
    struct WireSnapshot {
        address nft;address vault;address membership;address rewards;address fees;address zzz;
        uint256 id;uint256 bucket;uint256 shares;uint256 eligible;
        uint256 individualETH;uint256 collectiveETH;uint256 individualZZZ;uint256 collectiveZZZ;
        uint256 bucketWeight;uint256 bucketETH;uint256 bucketZZZ;
        uint256 globalWeight;uint256 globalETH;uint256 globalZZZ;
        uint256 directETH;uint256 directZZZ;uint256 liabilityETH;uint256 liabilityZZZ;
    }
    event ExactLPColdGas(''',1)
pos=s.rindex('\n}')
s=s[:pos]+'''
    function _wireSnapshot(uint256 id)private view returns(bytes memory){
        WireSnapshot memory w;w.nft=address(nft);w.vault=address(shares);w.membership=address(members);
        w.rewards=address(rewards);w.fees=address(fees);w.zzz=address(token);w.id=id;w.bucket=shares.nftBucket(id);w.shares=shares.sharesOf(id);w.eligible=members.totalEligible();
        (w.individualETH,w.collectiveETH)=rewards.claimableComponents(id,address(0));(w.individualZZZ,w.collectiveZZZ)=rewards.claimableComponents(id,address(token));
        (w.bucketWeight,w.bucketETH,w.bucketZZZ)=rewards.allocationTree(1);(w.globalWeight,w.globalETH,w.globalZZZ)=rewards.allocationTree(0);
        w.directETH=rewards.directLiabilities(address(0));w.directZZZ=rewards.directLiabilities(address(token));w.liabilityETH=rewards.liabilities(address(0));w.liabilityZZZ=rewards.liabilities(address(token));return abi.encode(w);
    }
    function testExactRewardsActualWireProducerBothBooks()public{
        vm.recordLogs();uint256 id=_mint(ALICE,1,101);Vm.Log[] memory records=vm.getRecordedLogs();emit ExactLPWire(0,abi.encode(records),_wireSnapshot(id));
        vm.recordLogs();_fund(1,20,20);records=vm.getRecordedLogs();emit ExactLPWire(1,abi.encode(records),_wireSnapshot(id));
        (uint256 personal,uint256 shared)=rewards.claimableComponents(id,address(0));assertEq(personal,16);assertEq(shared,2);
        vm.recordLogs();assertEq(_claim(ALICE,id,address(0)),18);assertEq(_claim(ALICE,id,address(token)),18);records=vm.getRecordedLogs();emit ExactLPWire(2,abi.encode(records),_wireSnapshot(id));_assertBacking();
    }
'''+s[pos:];p.write_bytes(s.encode());print('Added actual-EVM log/getter producer,24-field canonical static snapshot')
