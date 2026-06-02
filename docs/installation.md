# Installation
### Requirements
- **Python 3.14** (the wheel is built for CPython 3.14)
- If you use a different Python version, create a dedicated environment first:

conda create -n pdf-rabbit python=3.14
conda activate pdf-rabbit

### From a downloaded wheel
Download the latest .whl file from the
[https://github.com/Rana-Phy/PDF-RABBIT/releases](https://github.com/Rana-Phy/PDF-RABBIT/releases) page, then run:

pip install pdf_rabbit-<version>-cp314-none-any.whl

### From PyPI
pip install pdf_rabbit
### Dependencies
If any are missing, install them manually:
pip install numpy scipy matplotlib numba xraydb tabulate
