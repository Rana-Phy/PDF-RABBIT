# Installation

## Requirements

- **Python 3.14** — the wheel is built for CPython 3.14.
- If you use a different Python version, create a dedicated virtual environment first:

```bash
conda create -n pdf-rabbit python=3.14
conda activate pdf-rabbit
```

---

## Option 1 — From a Downloaded Wheel

1. Download the latest `.whl` file from the **[PDF-RABBIT Releases page](https://github.com/Rana-Phy/PDF-RABBIT/releases)**.
2. Install it with:

```bash
pip install pdf_rabbit-<version>-cp314-none-any.whl
```

> Replace `<version>` with the actual version number of the downloaded file.

---

## Option 2 — Or From PyPI

```bash
pip install pdf_rabbit
```

---

## Dependencies

If any dependencies are missing, install them manually:

```bash
pip install numpy scipy matplotlib numba xraydb tabulate
```
