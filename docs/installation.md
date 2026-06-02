# Installation

## Requirements

- **Python 3.14** (the wheel is built for CPython 3.14)
- Dependencies are installed automatically: NumPy, SciPy, Matplotlib, Numba,
  xraydb, tabulate

If you use a different Python version, create a dedicated environment first:

```bash
conda create -n pdf-rabbit python=3.14
conda activate pdf-rabbit
```

## From PyPI

```bash
pip install pdf_rabbit
```

## From a downloaded wheel

Download the latest `.whl` from the
[Releases](https://github.com/Rana-Phy/PDF-RABBIT/releases) page, then:

```bash
pip install pdf_rabbit-<version>-cp314-none-any.whl
```

All required dependencies are resolved and installed automatically.

:::{note}
The wheel is built for CPython 3.14, so it installs only on Python 3.14.
Install it inside a dedicated Python 3.14 environment as shown above.
:::
