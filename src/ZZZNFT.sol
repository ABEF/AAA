// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids} from "./libraries/ZZZTypes.sol";

/// @notice The canonical NFT never leaves its home chain. Unclaimed rewards
/// belong to the current owner; selling an NFT transfers those unclaimed rights.
contract ZZZNFT is ERC721, ZZZModule {
    string private metadataBase;
    event MetadataBaseChanged(string newBase);
    constructor(address controller, string memory baseURI)
        ERC721("ZZZ Permanent Liquidity Rights", "ZZZLP") ZZZModule(controller) {
        metadataBase = baseURI;
    }
    function mint(address to, uint256 id) external onlyModule(Ids.VAULT) {
        _safeMint(to, id);
    }
    function setBaseURI(string calldata baseURI) external onlyGovernance {
        metadataBase = baseURI;
        emit MetadataBaseChanged(baseURI);
    }
    function _baseURI() internal view override returns (string memory) { return metadataBase; }
    // No burn or principal-redemption entrypoint. Standard ERC721 safe transfers.
}
