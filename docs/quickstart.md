# Quick Start Guide

This guide demonstrates obtaining S(Q) and G(r) with minimum input parameters.
 
---

## Load Libraires

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
folder = r"./raw_data/"
data_file      = 'CeO2_10s_0.3mm.dat'
capillary_file = 'quartz_10s_0.3mm_1.dat'

data_processor = XrayDataProcessor(
    sample_path    = folder + data_file,
    container_path = folder + capillary_file)

two_theta, I_raw, I_bkg = data_processor.get_processed_data()
XrayDataPlotter(data_processor).plot()   # inspect raw vs background
```

## Step 2 — Define the Experiment

`ExperimentalInfo` holds all geometry, sample, and beam parameters that are shared across the pipeline.

```python
exp = ExperimentalInfo(
    geometry            = 'cylindrical',  
    sample_composition  = 'CeO2',
    sample_density      = 7.22,            # g cm⁻³ 
    container_composition = 'SiO2',
    container_density   = 2.0,             # g cm⁻³  
    d_inner             = 0.029,           # cm  — inner diameter of capillary
    d_outer             = 0.03,            # cm  — outer diameter of capillary
    wavelength          = 0.247949,        # Å   — synchrotron wavelength
)
```
---

## Step 3 — Compute Atomic Scattering Factors

`AtomicDataProcessor` calculates Q-dependent form factors, the Compton scattering, and the Breit–Dirac recoil factor.

```python
ap = AtomicDataProcessor(exp, two_theta)

# Breit–Dirac recoil factor (E'/E) per Q-point.
# bdr_order in OptSq controls the exponent n in I_comp ∝ (E'/E)^n.
bdr_factor, E_prime_keV = ap.calculate_recoil_factor()

# Retrieve scattering factor arrays:
#   f2  = sum c_i<f_i²>  (mean of squared form factors, FSM)
#   ff  = sum <c_if>²  (squared mean form factor, FMS)
#   cf  = Compton scattering function (CFF)
f2, ff, cf, _ = ap.calculate_SF()
```

---

## Step 4 — Compute Intensity Corrections

`IntensityCorrection` evaluates absorption (Paalman–Pings), secondary scattering, and fluorescence corrections. Each correction is computed once here and reused inside the optimiser.

```python
ic = IntensityCorrection(ap)

ic.compute_absorption()            # → ic.A_s_se, ic.A_container
ic.compute_secondary_scatter()     # → ic.ds
ic.compute_fluorescence_profile()  # → ic._I_f_raw  (scaled later by f_f)
```
---

## Step 5 — Optimise S(Q)

`OptSq` defines the parameter bounds and wraps the correction pipeline. `SqOptimizer` runs L-BFGS-B to minimise a loss function that drives S(Q) → 1 at high Q, F(Q) mean → 0 at high Q, and S(0) → the theoretical Faber–Ziman limit.

```python
SQ_optimizer_rk = OptSq(
    Q              = ap.Q,
    two_theta      = two_theta,
    I_sample       = I_raw,
    I_container    = I_bkg,       

    # Scattering factor arrays from Step 3
    FSM            = f2,          # <f²>
    FMS            = ff,          # <f>²
    CFF            = cf,          # Compton function
    bdr_factor     = bdr_factor,  # Breit–Dirac recoil factor
    rho_0          = 0.0757,     # Atomic number density (atoms Å⁻³)

    corr           = ic,          # IntensityCorrection object from Step 4
    bg_q_range     = [0.5, 2.5],  # Arround the short range order peak of capilarry

    
    high_q_range   = (22, 31.5), # Q range used for high-Q normalisation (S(Q) → 1 target).

    # ── Parameter bounds (lo, hi) ──────────────────────────────────────────
    # Setting lo == hi fixes a parameter at that value.

    polfact_bounds       = (1, 1),           # polarisation factor (fixed at 1 for synchrotron)
    fluorescence_bounds  = (0.0001, 1e5),    # fluorescence scaling factor f_f
    comp_damp_bounds     = (0, 1),           # Compton damping exponent
    bdr_order_bounds     = (2, 2),           # Breit–Dirac recoil exponent (fixed at 2)
    sys_bias       = 'wf', # Systematic error correction mode
    eta2_bounds          = (0, 0),           # wf_bias exponent (inactive; classical krogh-Moe/Normman normalization method)
    scaling_by     = 'integration',
)

optimizer = SqOptimizer(SQ_optimizer_rk)
optimizer.optimize()

SQ_optimizer_rk.report()          # print quality metrics and optimised parameters
sq_results_rk = SQ_optimizer_rk.get_results()
```
---

## Step 6 — Calculate G(r)

`calculate_Gr` Fourier-transforms S(Q) into the pair distribution function G(r).

```python
q  = SQ_optimizer_rk.Q
sq = SQ_optimizer_rk.S_FZ_final

FT_ra = calculate_Gr(
    q           = q,
    sq          = sq,
    r_step      = 0.01,    # Å — real-space grid spacing
    r_max       = 100,     # Å — maximum r
    window_type = 1,       # Lorch modification function (1 = standard Lorch)
)

r, G0, q_interp, Sq_used, fq_initial, fq_used = FT_ra.compute()
```


---

## Step 7 — Post-process G(r)

`PDFPostProcess` applies low-r constraints (G(r) → −4πρ₀r as r → 0), locates the first coordination shell, and refines the number density by matching the first-shell integral.

```python
pp_ra = PDFPostProcess(
    r           = r,
    Gr          = G0,
    atomic_data = ap.prepare_atomic_data(),
)

results = pp_ra.process(
    peak_guess        = 2.34,    # Å — initial guess for first-shell peak position
    peak_search_min   = 2.1,     # Å — search window lower bound
    peak_search_max   = 2.5,     # Å — search window upper bound
    predip_search_min = 1.0,     # Å — pre-peak dip search lower bound
    predip_search_max = 1.9,     # Å — pre-peak dip search upper bound
    density_target    = exp.sample_density,
    do_plot           = True,
)

G1 = pp_ra.Gr_final   # post-processed G(r)
```

---

## Step 9 — Save Results

```python
base_name = data_file.replace('.dat', '')

# G(r) at each refinement stage
np.savetxt(folder + base_name + ".G0", np.column_stack((r, G0)))   # raw FT
np.savetxt(folder + base_name + ".G1", np.column_stack((r, G1)))   # after post-process

# S(Q)
np.savetxt(folder + base_name + ".S0", np.column_stack((q_interp, Sq_used)))  # optimised S(Q)
```

All output files are plain two-column ASCII (space-delimited): `r  G(r)` or `Q  S(Q)`.

---

## Pipeline Summary

```
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
      │
      ▼
Save data
```
