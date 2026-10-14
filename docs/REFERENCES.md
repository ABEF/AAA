# Primary-source references consulted

Source/reference inspection is not an audit of those upstream projects. Repository `main` references below are mutable; compare them against the actual resolved release before deployment. Direct dependency installation and immutable revision resolution were blocked in the delivery environment.

Uniswap v4 PositionManager: action dispatch, approval restrictions, zero-liquidity fee collection, explicit-liquidity modifications, and deprecated FROM_DELTAS warnings.

```text
https://raw.githubusercontent.com/Uniswap/v4-periphery/main/src/PositionManager.sol
https://raw.githubusercontent.com/Uniswap/v4-periphery/main/src/libraries/Actions.sol
https://raw.githubusercontent.com/Uniswap/v4-periphery/main/src/libraries/PositionInfoLibrary.sol
https://raw.githubusercontent.com/Uniswap/v4-periphery/main/src/interfaces/IPositionManager.sol
https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/collect-fees.md
```

Uniswap StateView and periphery Permit2 getter / typed interfaces.

```text
https://raw.githubusercontent.com/Uniswap/v4-periphery/main/src/lens/StateView.sol
https://raw.githubusercontent.com/Uniswap/v4-periphery/main/src/base/Permit2Forwarder.sol
```

OpenZeppelin Contracts 5.4.0: ERC-721 and timelock inheritance surfaces. Custom protocol code does not inherit an audit merely by using these libraries.

```text
https://raw.githubusercontent.com/OpenZeppelin/openzeppelin-contracts/v5.4.0/contracts/token/ERC721/ERC721.sol
https://raw.githubusercontent.com/OpenZeppelin/openzeppelin-contracts/v5.4.0/contracts/governance/TimelockController.sol
```

Foundry standard test interface and Solidity compiler manifest.

```text
https://raw.githubusercontent.com/foundry-rs/forge-std/v1.9.7/src/Test.sol
https://binaries.soliditylang.org/linux-amd64/list.json
```

Solidity 0.8.26 Linux binary SHA-256 listed by the official manifest (the binary was **not downloaded or run**):

```text
d5f23436f443edb85d8e76906d12f0a86ce0490e7663a9e608efeb7a93f149ef
```

The original package requested OpenZeppelin 5.4.0, v4-core 1.0.2, and v4-periphery 1.0.4. npm does not publish periphery 1.0.4; the CI repair pins the published 1.0.3 release instead. Installation of all three direct packages succeeded with lifecycle scripts disabled. The real `package-lock.json` retains npm tarball URLs and integrity hashes. This dependency resolution does not establish an independent audit or compatibility with every upstream operation.
