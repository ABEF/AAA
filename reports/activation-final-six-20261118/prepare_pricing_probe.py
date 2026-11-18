"""Prepare ONE isolated transient-mark proposal. Does not edit production source."""
from pathlib import Path
import difflib, hashlib, json

R = Path(__file__).resolve().parents[2]
V = Path(r"C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9")
O = V / "activation-final-six-20261118/pricing-marks01"
O.mkdir(parents=True, exist_ok=False)
p = R / "src/ZZZContributionPricing.sol"
raw = p.read_bytes()
source = raw.decode("utf-8").replace("\r\n", "\n")
before = source
source = source.replace("    mapping(address => Mark) private marks;\n    address[] private assets;", """    // Exact captured marks are transaction-scoped, just like Oracle execution.
    // Every operation still explicitly clears them, including within one tx.
    bytes32 private constant MARK_DOMAIN = keccak256("PoPL.ContributionPricing.mark.v1");
    bytes32 private constant ASSET_LIST = keccak256("PoPL.ContributionPricing.assets.v1");""")
assert "mapping(address => Mark) private marks" not in source
source = source.replace("marks[token].lower", "_readMark(token).lower")
source = source.replace("assets.length", "_assetCount()")
source = source.replace("marks[source]", "_readMark(source)")
source = source.replace("Mark memory m = marks[token];", "Mark memory m = _readMark(token);")
source = source.replace("address token = assets[i];", "address token = _assetAt(i);")
source = source.replace("marks[token] = Mark(uint128(lower),uint128(upper),10 ** oracle.tokenDecimals(token),fingerprint);\n        assets.push(token);", "_writeMark(token,Mark(uint128(lower),uint128(upper),10 ** oracle.tokenDecimals(token),fingerprint));\n        _appendAsset(token);")
source = source.replace("for (uint256 i; i < _assetCount(); ++i) delete marks[assets[i]];\n        delete assets; delete basis;", "for (uint256 i; i < _assetCount(); ++i) _writeMark(_assetAt(i),Mark(0,0,0,bytes32(0)));\n        _clearAssets(); delete basis;")
assert "marks[" not in source and "assets[" not in source and "delete assets" not in source
helpers = """
    /// @dev Domain-separated slots; only bounded typed _mark can create records.
    function _markSlot(address token) private pure returns(bytes32 slot) {
        bytes32 domain=MARK_DOMAIN;
        assembly ("memory-safe") {
            mstore(0,and(token,0xffffffffffffffffffffffffffffffffffffffff))
            mstore(32,domain)
            slot:=keccak256(0,64)
        }
    }
    function _readMark(address token) private view returns(Mark memory m) {
        bytes32 slot=_markSlot(token);
        assembly ("memory-safe") {
            let value:=tload(slot)
            mstore(m,and(value,0xffffffffffffffffffffffffffffffff))
            mstore(add(m,32),shr(128,value))
            mstore(add(m,64),tload(add(slot,1)))
            mstore(add(m,96),tload(add(slot,2)))
        }
    }
    function _writeMark(address token,Mark memory m) private {
        bytes32 slot=_markSlot(token);
        assembly ("memory-safe") {
            tstore(slot,or(and(mload(m),0xffffffffffffffffffffffffffffffff),shl(128,mload(add(m,32)))))
            tstore(add(slot,1),mload(add(m,64)))
            tstore(add(slot,2),mload(add(m,96)))
        }
    }
    function _assetCount() private view returns(uint256 count) {
        bytes32 slot=ASSET_LIST;
        assembly ("memory-safe") { count:=tload(slot) }
    }
    function _assetAt(uint256 index) private view returns(address token) {
        bytes32 slot=ASSET_LIST;
        assembly ("memory-safe") { token:=and(tload(add(add(slot,1),index)),0xffffffffffffffffffffffffffffffffffffffff) }
    }
    function _appendAsset(address token) private {
        bytes32 slot=ASSET_LIST;
        assembly ("memory-safe") {
            let count:=tload(slot)
            tstore(add(add(slot,1),count),and(token,0xffffffffffffffffffffffffffffffffffffffff))
            tstore(slot,add(count,1))
        }
    }
    function _clearAssets() private {
        bytes32 slot=ASSET_LIST;
        assembly ("memory-safe") {
            let count:=tload(slot)
            for {let i:=0} lt(i,count) {i:=add(i,1)} {tstore(add(add(slot,1),i),0)}
            tstore(slot,0)
        }
    }
"""
source = source.replace("    function _mark(address token) private {", helpers + "\n    function _mark(address token) private {")
assert source != before
(O / "ZZZContributionPricing.candidate.sol").write_bytes(source.replace("\n", "\r\n").encode())
(O / "CANDIDATE.patch").write_text("".join(difflib.unified_diff(before.splitlines(True),source.splitlines(True),fromfile="baseline/src/ZZZContributionPricing.sol",tofile="candidate/src/ZZZContributionPricing.sol")),encoding="utf-8")
(O / "PLAN.json").write_text(json.dumps({"root_source_sha256":hashlib.sha256(raw).hexdigest(),"candidate_sha256":hashlib.sha256((O/"ZZZContributionPricing.candidate.sol").read_bytes()).hexdigest(),"root_unchanged":p.read_bytes()==raw,"adopted":False,"permanent_basis_and_maintenance_unchanged":True,"explicit_each_operation_clear":True,"target_evidence":"normal host size plus exact host differential and callback/rollback tests required"},indent=2)+"\n",encoding="utf-8")
print(O)
