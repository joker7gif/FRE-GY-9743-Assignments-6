# Assignment 6 - Chuyu Wu

## Contents
- `Part_I_Answers.pdf`: FX-forward valuation, fair strike, and curve sufficiency under GBP collateral.
- `Part_I_Answers.md`: editable text of the same answers.
- `hw6_interest_rate_products.ipynb`: the instructor notebook, executed with outputs.
- `fixedincomelib/product/linear_products.py`: RFR-swap and overnight-basis-swap legs.
- `fixedincomelib/product/product_factory.py`: convention-driven swap builders.
- `fixedincomelib/yield_curve/valuation_engine.py`: signed leg PV and cash aggregation.
- `verify_assignment6.py`: additional numerical, convention and settlement checks.
- `VERIFICATION.txt`: verification results.

The original library, data conventions and requirements are included.

## Run
Use Python 3.11. From this folder:

```bash
python -m pip install -r requirements.txt
```

Open `hw6_interest_rate_products.ipynb`, select that Python environment, restart the kernel and run all cells. Save the notebook with its outputs. The library modules are imported by the notebook and do not need to be run individually.

Additional checks:

```bash
python verify_assignment6.py
```

## Example results
| Product | PV (USD) |
|---|---:|
| FRA, receive fixed | 87.090294206882 |
| RFR swap, receive fixed | -2629.679574786293 |
| Overnight basis swap, receive leg 1 | 8446.472471163957 |

The basis quote applies to leg 1 (SOFR), while leg 2 is Fed Funds, as specified in the supplied convention. Each index uses its own projection curve; all cashflows use the selected funding curve. The spread is added outside overnight compounding. Schedules follow the supplied backward-generation and business-day rules.

Verified with Python 3.11.17, NumPy 1.26.4, pandas 2.3.1 and QuantLib 1.41. Small differences in the last decimal places may arise across numerical-library versions.
