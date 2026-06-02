# Quick Start Guide

This guide demonstrates how to obtain **S(Q)** and **G(r)** from X-ray diffraction data using PDF-Rabbit.

For most users, only the **USER INPUTS** section needs to be modified. The remainder of the workflow can typically be executed without changes.

---

# Step 0 — User Inputs

Edit only the variables below.

```python
# ============================================================
# FILES
# ============================================================

folder         = r"./raw_data/"             # folder containing diffraction data
data_file      = "CeO2_10s_0.3mm.dat"      # sample diffraction pattern
capillary_file = "quartz_10s_0.3mm_1.dat"  # empty capillary / background pattern

# ============================================================
# SAMPLE INFORMATION
# ============================================================

sample_composition    = "CeO2"  # chemical formula of the sample
sample_density        = 7.22    # mass density of the sample (g/cm³)

container_composition = "SiO2"  # chemical formula of the container
container_density     = 2.0     # mass density of the container (g/cm³)

# ============================================================
# EXPERIMENTAL SETUP
# ============================================================

geometry   = "cylindrical"  # sample geometry

d_inner    = 0.029          # capillary inner diameter (cm)
d_outer    = 0.030          # capillary outer diameter (cm)

wavelength = 0.247949       # X-ray wavelength (Å)

# ============================================================
# S(Q) OPTIMIZATION
# ============================================================

rho_0        = 0.0757       # atomic number density (atoms/Å³)

bg_q_range   = [0.5, 2.5]   # Q range containing the capillary short-range-order peak
high_q_range = (22, 31.5)   # high-Q region used to enforce S(Q) → 1

# ============================================================
# OPTIMIZATION PARAMETERS
# ============================================================

# Bounds are specified as:
# (lower_limit, upper_limit)
#
# Examples:
# (0, 1)  → parameter can vary between 0 and 1
# (2, 5)  → parameter can vary between 2 and 5
# (1, 1)  → parameter is fixed at 1 (not optimized)
# (2, 2)  → parameter is fixed at 2 (not optimized)

polfact_bounds      = (1, 1)         # polarization factor (fixed at 1)
fluorescence_bounds = (0.0001, 1e5)  # fluorescence scaling factor
comp_damp_bounds    = (0, 1)         # Compton damping exponent
bdr_order_bounds    = (2, 2)         # Breit–Dirac recoil exponent (fixed at 2)
eta2_bounds         = (0, 0)         # wf_bias exponent (disabled)

sys_bias            = "wf"           # systematic-error correction model
scaling_by          = "integration"  # normalization method

# ============================================================
# PDF PARAMETERS
# ============================================================

r_step = 0.01      # real-space step size (Å)
r_max  = 100       # maximum r for G(r) calculation (Å)

# ============================================================
# FIRST-SHELL SEARCH
# ============================================================

peak_guess = 2.34  # approximate first-neighbor peak position (Å)

peak_search_min = 2.1  # lower bound for first-shell peak search (Å)
peak_search_max = 2.5  # upper bound for first-shell peak search (Å)

predip_search_min = 1.0  # lower bound for pre-peak dip search (Å)
predip_search_max = 1.9  # upper bound for pre-peak dip search (Å)
```

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

`ExperimentalInfo` stores the experimental parameters used throughout the analysis pipeline.

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

Returned variables:

```python
bdr_factor  # Breit–Dirac recoil factor (E′/E)
f2          # Mean squared form factor ⟨f²⟩ (FSM)
ff          # Square of mean form factor ⟨f⟩² (FMS)
cf          # Compton scattering function (CFF)
```

---

# Step 5 — Compute Intensity Corrections

```python
ic = IntensityCorrection(ap)

ic.compute_absorption()            # Paalman–Pings absorption correction
ic.compute_secondary_scatter()     # double-scattering contribution
ic.compute_fluorescence_profile()  # fluorescence background profile
```

---

# Step 6 — Optimise S(Q)

`SqOptimizer` uses the L-BFGS-B algorithm to optimize S(Q).

The optimization attempts to satisfy:

* S(Q) → 1 at high Q
* F(Q) → 0 at high Q

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

    polfact_bounds      = polfact_bounds,
    fluorescence_bounds = fluorescence_bounds,
    comp_damp_bounds    = comp_damp_bounds,
    bdr_order_bounds    = bdr_order_bounds,
    eta2_bounds         = eta2_bounds,

    sys_bias            = sys_bias,
    scaling_by          = scaling_by,
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
    window_type = 1,   # standard Lorch modification function
)

r, G0, q_interp, Sq_used, fq_initial, fq_used = FT_ra.compute()
```

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

```text
*.S0  → optimized S(Q)
*.G0  → raw G(r)
*.G1  → post-processed G(r)
```

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
