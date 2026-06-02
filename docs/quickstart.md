# Quick Start Guide

This guide demonstrates how to obtain **S(Q)** and **G(r)** using a minimal set of user-defined parameters.

For most users, the only section that needs to be modified is the **USER INPUTS** block below. The remainder of the workflow can usually be executed without changes.

---

# Step 0 — User Inputs

Edit the variables below according to your experiment.

```python
# ============================================================
# FILES
# ============================================================

folder         = r"./raw_data/"
data_file      = "CeO2_10s_0.3mm.dat"
capillary_file = "quartz_10s_0.3mm_1.dat"

# ============================================================
# SAMPLE INFORMATION
# ============================================================

sample_composition    = "CeO2"
sample_density        = 7.22      # g cm⁻³

container_composition = "SiO2"
container_density     = 2.0       # g cm⁻³

# ============================================================
# EXPERIMENTAL SETUP
# ============================================================

geometry   = "cylindrical"

d_inner    = 0.029    # cm
d_outer    = 0.030    # cm

wavelength = 0.247949 # Å

# ============================================================
# S(Q) OPTIMIZATION
# ============================================================

rho_0          = 0.0757           # atoms Å⁻³

bg_q_range     = [0.5, 2.5]
high_q_range   = (22, 31.5)

# ============================================================
# PDF PARAMETERS
# ============================================================

r_step         = 0.01             # Å
r_max          = 100              # Å

# ============================================================
# FIRST-SHELL SEARCH
# ============================================================

peak_guess        = 2.34

peak_search_min   = 2.1
peak_search_max   = 2.5

predip_search_min = 1.0
predip_search_max = 1.9
```

---

## Input Parameter Description

### Files

| Parameter | Description |
|------------|------------|
| `folder` | Folder containing the diffraction data files |
| `data_file` | Sample diffraction pattern |
| `capillary_file` | Background/container diffraction pattern |

### Sample Information

| Parameter | Description |
|------------|------------|
| `sample_composition` | Chemical formula of the sample |
| `sample_density` | Sample density (g cm⁻³) |

### Container Information

| Parameter | Description |
|------------|------------|
| `container_composition` | Chemical formula of the container |
| `container_density` | Container density (g cm⁻³) |

### Experimental Setup

| Parameter | Description |
|------------|------------|
| `geometry` | Measurement geometry |
| `d_inner` | Inner capillary diameter (cm) |
| `d_outer` | Outer capillary diameter (cm) |
| `wavelength` | X-ray wavelength (Å) |

### S(Q) Optimization

| Parameter | Description |
|------------|------------|
| `rho_0` | Atomic number density (atoms Å⁻³) |
| `bg_q_range` | Q range surrounding the container short-range-order peak |
| `high_q_range` | High-Q normalization region where S(Q) → 1 |

### PDF Parameters

| Parameter | Description |
|------------|------------|
| `r_step` | Real-space grid spacing (Å) |
| `r_max` | Maximum r value (Å) |

### First-Shell Search

| Parameter | Description |
|------------|------------|
| `peak_guess` | Initial estimate of the first-neighbor peak position |
| `peak_search_min` | Lower bound of first-shell peak search |
| `peak_search_max` | Upper bound of first-shell peak search |
| `predip_search_min` | Lower bound of pre-peak dip search |
| `predip_search_max` | Upper bound of pre-peak dip search |

---

# Step 1 — Load Libraries

```python
import numpy as np
import matplotlib.pyplot as plt

from xrd_data_processor import XrayDataProcessor, XrayDataPlotter
from experimental_info import ExperimentalInfo
from atomic_data_processor import AtomicDataProcessor
from intensity_correction import IntensityCorrection
from opt_sq import OptSq, SqOptimizer
from calculate_rpdf import calculate_Gr
from rpdf_postprocess import PDFPostProcess
from rpdf_to_Sq import get_rSq
```

---

# Step 2 — Load Raw Data

```python
data_processor = XrayDataProcessor(
    sample_path    = folder + data_file,
    container_path = folder + capillary_file,
)

two_theta, I_raw, I_bkg = data_processor.get_processed_data()

# Inspect sample and background data
XrayDataPlotter(data_processor).plot()
```

---

# Step 3 — Define the Experiment

`ExperimentalInfo` stores all experimental parameters used throughout the workflow.

```python
exp = ExperimentalInfo(
    geometry              = geometry,
    sample_composition    = sample_composition,
    sample_density        = sample_density,
    container_composition = container_composition,
    container_density     = container_density,
    d_inner               = d_inner,
    d_outer               = d_outer,
    wavelength            = wavelength,
)
```

---

# Step 4 — Compute Atomic Scattering Factors

```python
ap = AtomicDataProcessor(exp, two_theta)

bdr_factor, E_prime_keV = ap.calculate_recoil_factor()
f2, ff, cf, _           = ap.calculate_SF()
```

### Output Variables

| Variable | Meaning |
|----------|----------|
| `bdr_factor` | Breit–Dirac recoil factor (E′/E) |
| `f2` | Mean squared form factor, ⟨f²⟩ (FSM) |
| `ff` | Square of mean form factor, ⟨f⟩² (FMS) |
| `cf` | Compton scattering function (CFF) |

---

# Step 5 — Compute Intensity Corrections

```python
ic = IntensityCorrection(ap)

ic.compute_absorption()
ic.compute_secondary_scatter()
ic.compute_fluorescence_profile()
```

### Corrections Applied

- Paalman–Pings absorption correction
- Double-scattering contribution
- Fluorescence background correction

---

# Step 6 — Optimise S(Q)

`SqOptimizer` uses the L-BFGS-B algorithm to optimize S(Q).

The optimization attempts to satisfy:

- S(Q) → 1 at high Q
- F(Q) → 0 at high Q

```python
SQ_optimizer_rk = OptSq(
    Q           = ap.Q,
    two_theta   = two_theta,
    I_sample    = I_raw,
    I_container = I_bkg,

    FSM         = f2,
    FMS         = ff,
    CFF         = cf,
    bdr_factor  = bdr_factor,

    rho_0       = rho_0,
    corr        = ic,

    bg_q_range   = bg_q_range,
    high_q_range = high_q_range,

    # Parameter bounds
    polfact_bounds      = (1, 1),
    fluorescence_bounds = (0.0001, 1e5),
    comp_damp_bounds    = (0, 1),
    bdr_order_bounds    = (2, 2),
    eta2_bounds         = (0, 0),

    sys_bias            = 'wf',
    scaling_by          = 'integration',
)

optimizer = SqOptimizer(SQ_optimizer_rk)
optimizer.optimize()

SQ_optimizer_rk.report()

sq_results_rk = SQ_optimizer_rk.get_results()
```

---

# Step 7 — Calculate G(r)

```python
q  = SQ_optimizer_rk.Q
sq = SQ_optimizer_rk.S_FZ_final

FT_ra = calculate_Gr(
    q           = q,
    sq          = sq,
    r_step      = r_step,
    r_max       = r_max,
    window_type = 1,      # Standard Lorch modification function
)

r, G0, q_interp, Sq_used, fq_initial, fq_used = FT_ra.compute()
```

### Output Variables

| Variable | Description |
|-----------|------------|
| `r` | Real-space grid |
| `G0` | Raw PDF |
| `q_interp` | Interpolated Q grid |
| `Sq_used` | Optimized S(Q) |
| `fq_initial` | Initial F(Q) |
| `fq_used` | Final F(Q) |

---

# Step 8 — Post-process G(r)

`PDFPostProcess` applies low-r constraints and refines the number density.

```python
pp_ra = PDFPostProcess(
    r=r,
    Gr=G0,
    atomic_data=ap.prepare_atomic_data()
)

results = pp_ra.process(
    peak_guess        = peak_guess,
    peak_search_min   = peak_search_min,
    peak_search_max   = peak_search_max,
    predip_search_min = predip_search_min,
    predip_search_max = predip_search_max,
    density_target    = exp.sample_density,
    do_plot           = True,
)

G1 = pp_ra.Gr_final
```

### Processing Steps

- First-shell peak identification
- Pre-peak dip identification
- Density refinement
- Low-r correction
- Final PDF generation

---

# Step 9 — Save Results

```python
base_name = data_file.replace('.dat', '')

np.savetxt(
    folder + base_name + ".G0",
    np.column_stack((r, G0))
)

np.savetxt(
    folder + base_name + ".G1",
    np.column_stack((r, G1))
)

np.savetxt(
    folder + base_name + ".S0",
    np.column_stack((q_interp, Sq_used))
)
```

Generated files:

| File | Description |
|--------|-------------|
| `.G0` | Raw G(r) |
| `.G1` | Post-processed G(r) |
| `.S0` | Optimized S(Q) |

All files are saved as two-column plain-text files.

---

# Pipeline Summary

```text
Raw .dat files
      │
      ▼
XrayDataProcessor
      │
      ▼
ExperimentalInfo
      │
      ▼
AtomicDataProcessor
      │
      ▼
IntensityCorrection
      │
      ▼
OptSq + SqOptimizer
      │
      ▼
calculate_Gr
      │
      ▼
PDFPostProcess
      │
      ▼
Save G0, G1, S0
```

---

# Example

```python
folder         = r"./raw_data/"
data_file      = "CeO2_10s_0.3mm.dat"
capillary_file = "quartz_10s_0.3mm_1.dat"

sample_composition    = "CeO2"
sample_density        = 7.22

container_composition = "SiO2"
container_density     = 2.0

geometry   = "cylindrical"

d_inner    = 0.029
d_outer    = 0.030

wavelength = 0.247949

rho_0      = 0.0757

bg_q_range   = [0.5, 2.5]
high_q_range = (22, 31.5)

r_step = 0.01
r_max  = 100

peak_guess        = 2.34
peak_search_min   = 2.1
peak_search_max   = 2.5

predip_search_min = 1.0
predip_search_max = 1.9
```

After defining these parameters, the remaining workflow can be executed without modification.
