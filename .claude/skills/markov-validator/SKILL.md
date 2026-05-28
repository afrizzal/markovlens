---
name: markov-validator
description: Validate a transition matrix against MarkovLens invariants — square shape, non-negative, rows sum to 1.0, minimum observations per cell. Use whenever building, modifying, or accepting a transition matrix from user input/external source.
allowed-tools: Read, Edit, Bash
---

# Markov Matrix Validator

Validate a Markov transition matrix against the project's mandatory invariants before it's used in any computation.

## When to Use

- After building a transition matrix from raw data
- After applying user adjustments (what-if scenarios)
- At the start of any simulation that consumes a matrix
- When loading a cached matrix from DuckDB
- During code review of any function that touches a matrix

## Mandatory Checks

| # | Check | Why |
|---|---|---|
| 1 | `ndim == 2` and shape is square | Markov matrix is N×N |
| 2 | All values `>= 0` | Probabilities cannot be negative |
| 3 | All values `<= 1.0 + tolerance` | Probabilities cannot exceed 1 |
| 4 | Each row sums to `1.0 ± 1e-9` | Row = full probability distribution from state i |
| 5 | Every cell `P[i,j]` estimated from `>= MIN_OBSERVATIONS_PER_CELL` (20) | Sparse cells = noise |
| 6 | No `NaN` or `Inf` values | Bad arithmetic upstream |
| 7 | If symmetric labeling used: state index order matches state name list | Prevent off-by-one in UI |

## Procedure

1. **Read** the target matrix (and optional `transition_counts` for check #5)
2. **Run all 7 checks** — collect failures, don't stop at first
3. **Report:**
   - ✅ Pass: print summary (shape, row-sum range, min/max prob, sparsity stats)
   - ❌ Fail: print specific failures with row/column indices + observed vs expected values
4. **For sparsity warnings (check #5):** suggest concrete remediation (merge states, gather more data, or warn user in UI)

## Reference Implementation

```python
from core.models import validate_transition_matrix
validate_transition_matrix(P, transition_counts=N)
```

This skill should INVOKE that function and interpret its output. If `core/models.py` doesn't yet have the validator, implement it per spec in `.claude/rules/markov-patterns.md`.

## Output Format

```
## Transition Matrix Validation Report

**Matrix:** shape (10, 10), dataset_id=foo, model=m1

| Check | Result |
|---|---|
| Square shape | ✅ 10×10 |
| Non-negative | ✅ min = 0.0000 |
| Bounded ≤ 1.0 | ✅ max = 0.8421 |
| Row sums = 1.0 | ✅ all within 1e-12 |
| Min observations | ⚠️ 3 cells below threshold (rows 7, 8, 9) |
| No NaN/Inf | ✅ |

### Action Items
- Rows 7-9 have insufficient data: consider merging states "Bronze", "Silver", "Other"
```
