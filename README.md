# PDF-RABBIT

An end-to-end analysis framework for X-ray total scattering data with a fully integrated workflow of physically grounded corrections.  
PDF-RABBIT was developed in the Laboratory of Structural Inorganic Chemistry, Graduate School of Engineering, Hokkaido University, under the supervision of Professor Akira Miura.

---

## Purpose

PDF-RABBIT is designed to analyze changes in local structural features from high-throughput X-ray total scattering measurements collected under external stimuli such as time, temperature, pressure, and chemical or electrochemical environments.

- The framework extracts reliable and reproducible `S(Q)` and `G(r)` functions by optimizing hyperparameters subject to physically meaningful boundary conditions.
- PDF-RABBIT provides an end-to-end workflow covering data reduction, correction, optimization, and structural modeling, particularly for large datasets.

---

## Features

- **Data preprocessing**
- **Intensity corrections**
  - Paalman–Pings absorption correction (cylindrical and flat-plate geometries)
  - Secondary scattering correction
  - Polarization correction
  - Fluorescence correction
  - Breit–Dirac recoil correction
  - Normalization
- **`S(Q)`, `F(Q)`, and `G(r)` optimization**
  - Multi-parameter least-squares optimization
- **`G(r) ↔ S(Q)` reverse transformation**
- **Small-box fitting and refinement**

---

## Examples

Annotated Jupyter notebooks demonstrating typical workflows — including data loading, correction, optimization, `G(r)` extraction, and post-processing — will be provided in the [`notebooks/`](./notebooks) directory of this repository.

---

## Installation

PDF-RABBIT is distributed as a Python wheel (`.whl`).

To request access, please contact the developer (see *Contact* below). Each licensed group receives:

1. A wheel file built specifically for the licensed group
2. A group activation key

After obtaining these files:

```bash
pip install pdf_rabbit_<your_group>-<version>-py3-none-any.whl
```

---

## License

PDF-RABBIT is proprietary software distributed free of charge for academic and commercial research use. See [LICENSE](LICENSE) for the complete terms and conditions.

### Permitted Use

- Installation and use within the licensed group (academic or commercial)
- Analysis of experimental data for research, educational, or commercial purposes
- Publication and reporting of results derived from the software, with appropriate citation where applicable

### Prohibited Use

- Redistribution of the wheel file, activation key, or any part of the software outside the licensed group
- Modification, reverse engineering, or repackaging of the software into a commercial product

Commercial users, including industrial laboratories, CROs, and other for-profit organizations, are encouraged to make a good-faith donation to support continued development and maintenance.

---

## Citation

A peer-reviewed publication and DOI will be released in due course. Users are encouraged to update citations once the formal publication becomes available.

### Recommended acknowledgment for the Methods section

Adapt the following text according to the scope of analysis performed.

**For data reduction and PDF extraction:**

> “Normalization to electron units, structure factor `S(Q)`, and pair distribution function `G(r)` were obtained using PDF-RABBIT, a self-consistent optimization framework for X-ray total scattering analysis.”

**When small-box refinement is performed using the same framework:**

> “Small-box refinement was performed using PDF-RABBIT.”

To promote reproducibility, users are encouraged to report optimized parameters in the Supplementary Information where appropriate.

---

## Contact

### Developer

Rana Hossain  
Postdoctoral Research Associate  
Laboratory of Structural Inorganic Chemistry  
Division of Applied Chemistry, Faculty of Engineering  
Hokkaido University, Sapporo, Japan

### Supervisor

Professor Akira Miura

### Email

- rana.phy.buet@gmail.com
- rana@eng.hokudai.ac.jp  
  cc: amiura@eng.hokudai.ac.jp

For access requests, donation inquiries, or general questions, please include:

- Full name and designation
- Laboratory, company, or institution
- Principal investigator or supervisor (if applicable)
- Research field
