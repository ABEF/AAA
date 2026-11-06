// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";

/// @notice Bounded whole-unit allocation to mutable NFT share weights.
/// @dev Candidate engine only: current Rewards/Vault/canonical profiles do not
/// use it. The host must authenticate immutable NFT ordinals, ETH/fixed-ZZZ
/// books, actual funding, ownership and atomic canonical share synchronization.
/// No token movement, authority or external call is implemented here.
library ExactLPAllocation {
    uint256 internal constant LEAVES = 1024;
    uint256 internal constant MAX_ORDINAL = 1000;
    uint256 internal constant Q = uint256(1) << 128;

    enum Asset { ETH, ZZZ }

    /// @dev Fairness phase only, never money or a fractional reserved claim.
    /// With subtree weight W>0, phase = high/Q + low/(Q*W).
    struct Carry { uint128 high; uint256 low; }
    struct Book {
        mapping(uint256 => uint256) pending;
        mapping(uint256 => Carry) carry;
        uint256 outstanding;
    }
    struct Tree {
        mapping(uint256 => uint256) weights;
        // Both books MUST settle before a shared weight changes. A caller
        // cannot supply an incomplete list or silently introduce another asset.
        Book[2] books;
    }

    error InvalidOrdinal();
    error EmptyCohort();
    error InvalidSplit();

    /// @notice Set one ordinal's weight after settling BOTH old asset paths.
    /// @dev A no-op preserves every pending unit and fairness phase. Genuine
    /// changes retain high phase and rebase only its low remainder, losing less
    /// than 1/Q phase per changed node, not bounding integer payout differences.
    /// Zero weight does not erase previously assigned leaf rights. This generic
    /// operation grants no host permission to deactivate NFTs or reuse ordinals.
    function setWeight(Tree storage tree, uint256 ordinal, uint256 weight)
        internal returns (uint256 total) {
        uint256 leaf = _leaf(ordinal);
        uint256 old = tree.weights[leaf];
        total = tree.weights[1];
        if (old == weight) return total;
        // Reject aggregate overflow before materializing any old pending path.
        total = total - old + weight;
        uint256 incoming = _settlePath(tree, tree.books[0], ordinal);
        if (incoming != 0) tree.books[0].pending[leaf] += incoming;
        incoming = _settlePath(tree, tree.books[1], ordinal);
        if (incoming != 0) tree.books[1].pending[leaf] += incoming;
        tree.weights[leaf] = weight;
        for (uint256 node = leaf >> 1; node != 0; node >>= 1) {
            uint256 beforeWeight = tree.weights[node];
            uint256 afterWeight = tree.weights[node << 1] + tree.weights[(node << 1) | 1];
            tree.weights[node] = afterWeight;
            _rebase(tree.books[0].carry[node], beforeWeight, afterWeight);
            _rebase(tree.books[1].carry[node], beforeWeight, afterWeight);
        }
    }

    /// @notice Assign funded whole units to the current weighted cohort.
    /// @dev Constant tree work; funding and aggregate liabilities belong to the
    /// host. Only outstanding balances are stored, never lifetime counters.
    function credit(Tree storage tree, Asset asset, uint256 amount) internal {
        if (amount == 0) return;
        if (tree.weights[1] == 0) revert EmptyCohort();
        Book storage book = tree.books[uint256(asset)];
        book.outstanding += amount;
        book.pending[1] += amount;
    }

    /// @notice Read one leaf's exact whole units without materialization.
    function claimable(Tree storage tree, Asset asset, uint256 ordinal)
        internal view returns (uint256 amount) {
        _leaf(ordinal);
        Book storage book = tree.books[uint256(asset)];
        uint256 node = 1;
        for (uint256 mask = LEAVES >> 1; mask != 0; mask >>= 1) {
            amount += book.pending[node];
            bool right = ((ordinal - 1) & mask) != 0;
            // Empty dormant subtrees need no division; old whole units may
            // remain at a zero-weight leaf and are read after this loop.
            if (amount != 0) {
                Carry storage c = book.carry[node];
                (uint256 left, uint256 other,,) = split(amount, tree.weights[node << 1],
                    tree.weights[node], c.high, c.low);
                amount = right ? other : left;
            }
            node = (node << 1) | (right ? 1 : 0);
        }
        amount += book.pending[node];
    }

    /// @notice Remove one leaf's whole units for a host-authenticated payout.
    /// @dev At most ten pushes. No owner, receiver or token is chosen here.
    function take(Tree storage tree, Asset asset, uint256 ordinal)
        internal returns (uint256 amount) {
        uint256 leaf = _leaf(ordinal);
        Book storage book = tree.books[uint256(asset)];
        amount = _settlePath(tree, book, ordinal);
        uint256 stored = book.pending[leaf];
        amount += stored;
        if (stored != 0) delete book.pending[leaf];
        if (amount != 0) book.outstanding -= amount;
    }

    function totalWeight(Tree storage tree) internal view returns (uint256) { return tree.weights[1]; }
    function weightOf(Tree storage tree, uint256 ordinal) internal view returns (uint256) { return tree.weights[_leaf(ordinal)]; }
    function outstanding(Tree storage tree, Asset asset) internal view returns (uint256) { return tree.books[uint256(asset)].outstanding; }

    /// @notice Full-precision whole-unit split with bounded fairness phase.
    /// @dev Fixed weights preserve exact batching/materialization behavior.
    /// The two carry folds avoid evaluating an overflowing remainder sum.
    function split(uint256 amount, uint256 leftWeight, uint256 weight, uint128 high, uint256 low)
        internal pure returns (uint256 left, uint256 right, uint128 nextHigh, uint256 nextLow) {
        if (weight == 0 || leftWeight > weight || low >= weight) revert InvalidSplit();
        left = Math.mulDiv(amount, leftWeight, weight);
        uint256 remainder = mulmod(amount, leftWeight, weight);
        uint256 phase = Math.mulDiv(remainder, Q, weight);
        nextLow = mulmod(remainder, Q, weight);
        uint256 gap = weight - low;
        if (nextLow >= gap) {
            ++phase;
            nextLow -= gap;
        } else nextLow += low;
        phase += uint256(high); // <2*Q, even when the low fold made phase=Q.
        if (phase >= Q) { ++left; phase -= Q; }
        nextHigh = uint128(phase);
        right = amount - left;
    }

    /// @dev The selected share stays in memory until its leaf. Only sibling
    /// shares need storage, avoiding temporary selected-child writes/deletes.
    /// No external call can observe this transient in-memory accounting.
    function _settlePath(Tree storage tree, Book storage book, uint256 ordinal)
        private returns (uint256 incoming) {
        uint256 node = 1;
        for (uint256 mask = LEAVES >> 1; mask != 0; mask >>= 1) {
            uint256 stored = book.pending[node];
            incoming += stored;
            if (stored != 0) delete book.pending[node];
            bool goRight = ((ordinal - 1) & mask) != 0;
            if (incoming != 0) {
                Carry storage c = book.carry[node];
                (uint256 left, uint256 right, uint128 high, uint256 low) =
                    split(incoming, tree.weights[node << 1], tree.weights[node], c.high, c.low);
                uint256 sibling = goRight ? left : right;
                if (sibling != 0) book.pending[(node << 1) | (goRight ? 0 : 1)] += sibling;
                c.high = high; c.low = low;
                incoming = goRight ? right : left;
            }
            node = (node << 1) | (goRight ? 1 : 0);
        }
    }

    function _rebase(Carry storage carry, uint256 oldWeight, uint256 newWeight) private {
        uint256 low = carry.low;
        if (low == 0) return;
        // Keep high even through an empty cohort. Clearing it would permit
        // genuine weight changes to repeatedly restart a whole-unit phase.
        carry.low = oldWeight == 0 || newWeight == 0 ? 0 : Math.mulDiv(low, newWeight, oldWeight);
    }

    function _leaf(uint256 ordinal) private pure returns (uint256) {
        if (ordinal == 0 || ordinal > MAX_ORDINAL) revert InvalidOrdinal();
        return LEAVES + ordinal - 1;
    }
}
