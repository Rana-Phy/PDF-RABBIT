# Quick Start Guide

This guide demonstrates how to obtain S(Q) and G(r) using a minimal set of input parameters.

---

## Load Libraries

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

## Step 1 — Load Raw Data

```python
folder         = r"./raw_data/"
data_file      = 'CeO2_10s_0.3mm.dat'
capillary_file = 'quartz_10s_0.3mm_1.dat'

data_processor = XrayDataProcessor(
    sample_path    = folder + data_file,
    container_path = folder + capillary_file,
)

two_theta, I_raw, I_bkg = data_processor.get_processed_data()
XrayDataPlotter(data_processor).plot()   # Inspect raw and background data
```

---

## Step 2 — Define the Experiment

`ExperimentalInfo` stores all experimental geometry, sample, and beam parameters used throughout the analysis pipeline.

```python
exp = ExperimentalInfo(
    geometry              = 'cylindrical',
    sample_composition    = 'CeO2',
    sample_density        = 7.22,       # g cm⁻³
    container_composition = 'SiO2',
    container_density     = 2.0,        # g cm⁻³
    d_inner               = 0.029,      # cm — capillary inner diameter
    d_outer               = 0.03,       # cm — capillary outer diameter
    wavelength            = 0.247949,   # Å — synchrotron wavelength
)
```

---

## Step 3 — Compute Atomic Scattering Factors

```python
ap = AtomicDataProcessor(exp, two_theta)

bdr_factor, E_prime_keV = ap.calculate_recoil_factor()
f2, ff, cf, _           = ap.calculate_SF()
```

| Variable     | Meaning                                          |
| ------------ | ------------------------------------------------ |
| `bdr_factor` | Breit–Dirac recoil factor (E′/E) at each Q point |
| `f2`         | Mean squared form factor, ⟨f²⟩ (FSM)             |
| `ff`         | Square of the mean form factor, ⟨f⟩² (FMS)       |
| `cf`         | Compton scattering function (CFF)                |

---

## Step 4 — Compute Intensity Corrections

```python
ic = IntensityCorrection(ap)

ic.compute_absorption()            # Paalman–Pings absorption correction
ic.compute_secondary_scatter()     # Double-scattering contribution
ic.compute_fluorescence_profile()  # Fluorescence background profile
```

---

## Step 5 — Optimise S(Q)

`SqOptimizer` uses the L-BFGS-B algorithm to minimise a loss function that drives S(Q) → 1 and F(Q) → 0 in the high-Q region.

```python
SQ_optimizer_rk = OptSq(
    Q           = ap.Q,
    two_theta   = two_theta,
    I_sample    = I_raw,
    I_container = I_bkg,

    FSM         = f2,           # ⟨f²⟩
    FMS         = ff,           # ⟨f⟩²
    CFF         = cf,           # Compton function
    bdr_factor  = bdr_factor,
    rho_0       = 0.0757,       # Number density (atoms Å⁻³)
    corr        = ic,

    bg_q_range   = [0.5, 2.5],   # Q range surrounding the capillary short-range-order peak
    high_q_range = (22, 31.5),   # High-Q region used for normalisation (target: S(Q) → 1)

    # Parameter bounds: (lower, upper).
    # Setting lower == upper fixes the parameter.
    polfact_bounds      = (1, 1),         # Polarisation factor (fixed at 1 for synchrotron data)
    fluorescence_bounds = (0.0001, 1e5),  # Fluorescence scaling factor, f_f
    comp_damp_bounds    = (0, 1),         # Compton damping exponent
    bdr_order_bounds    = (2, 2),         # Breit–Dirac recoil exponent (fixed at 2)
    eta2_bounds         = (0, 0),         # wf_bias exponent (inactive)
    sys_bias            = 'wf',
    scaling_by          = 'integration',
)

optimizer = SqOptimizer(SQ_optimizer_rk)
optimizer.optimize()

SQ_optimizer_rk.report()
sq_results_rk = SQ_optimizer_rk.get_results()
```

---

## Step 6 — Calculate G(r)

```python
q  = SQ_optimizer_rk.Q
sq = SQ_optimizer_rk.S_FZ_final

FT_ra = calculate_Gr(
    q           = q,
    sq          = sq,
    r_step      = 0.01,   # Å — real-space grid spacing
    r_max       = 100,    # Å — maximum r value
    window_type = 1,      # 1 = standard Lorch modification function
)

r, G0, q_interp, Sq_used, fq_initial, fq_used = FT_ra.compute()
```

---

## Step 7 — Post-process G(r)

`PDFPostProcess` applies low-r constraints (G(r) → −4πρ₀r as r → 0) and refines the number density by matching the first-shell coordination integral.

```python
pp_ra = PDFPostProcess(r=r, Gr=G0, atomic_data=ap.prepare_atomic_data())

results = pp_ra.process(
    peak_guess        = 2.34,  # Å — initial estimate of the first-shell peak position
    peak_search_min   = 2.1,   # Å — lower bound of the peak search window
    peak_search_max   = 2.5,   # Å — upper bound of the peak search window
    predip_search_min = 1.0,   # Å — lower bound of the pre-peak dip search window
    predip_search_max = 1.9,   # Å — upper bound of the pre-peak dip search window
    density_target    = exp.sample_density,
    do_plot           = True,
)

G1 = pp_ra.Gr_final
```

---

## Step 8 — Save Results

```python
base_name = data_file.replace('.dat', '')

np.savetxt(folder + base_name + ".G0", np.column_stack((r, G0)))              # Raw G(r)
np.savetxt(folder + base_name + ".G1", np.column_stack((r, G1)))              # Post-processed G(r)
np.savetxt(folder + base_name + ".S0", np.column_stack((q_interp, Sq_used)))  # Optimised S(Q)
```

All output files are saved as two-column plain-text files (space-delimited) in the format `r  G(r)` or `Q  S(Q)`.

---

## Pipeline Summary

```text
Raw .dat files
      │
      ▼
XrayDataProcessor       ← Load data
      │
      ▼
ExperimentalInfo        ← Geometry, composition, density, wavelength
      │
      ▼
AtomicDataProcessor     ← Scattering factors, recoil factor
      │
      ▼
IntensityCorrection     ← Angle-dependent corrections
      │
      ▼
OptSq + SqOptimizer     ← Optimise S(Q)
      │
      ▼
calculate_Gr            ← Fourier transform → G(r) [G0]
      │
      ▼
PDFPostProcess          ← Low-r correction → G(r) [G1]
      │
      ▼
Save G0, G1, S0
```
