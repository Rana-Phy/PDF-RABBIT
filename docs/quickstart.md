# Quick Start Guide
This guide demonstrates how to obtain **S(Q)** and **G(r)** from X-ray diffraction data using PDF-Rabbit.
- Only the **Step 0 — User Inputs** section needs to be modified for a particular experiment.
- The remainder of the workflow can typically be executed without changes.
## Step 0 — User Inputs
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
polfact_bounds      = (1, 1)  # polarization factor (fixed at 1)
fluorescence_bounds = (0, 1)  # fluorescence scaling factor (can vary from 0 to 1)
comp_damp_bounds    = (0, 0)  # Compton damping exponent (fixed at 0)
bdr_order_bounds    = (2, 2)  # Breit–Dirac recoil exponent (fixed at 2)
sys_bias            = "wf"           # systematic-error correction model
eta2_bounds         = (0, 0)         # disabled (fixed at 0): Krogh-Moe/Norman normalization
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
## Step 1 — Load Libraries
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
## Step 2 — Load Raw Data
```python
data_processor = XrayDataProcessor(
    sample_path    = folder + data_file,
    container_path = folder + capillary_file,
)
two_theta, I_raw, I_bkg = data_processor.get_processed_data()
# Inspect sample and background data
XrayDataPlotter(data_processor).plot()
```
## Step 3 — Define the Experiment
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
## Step 4 — Compute Atomic Scattering Factors
```python
ap = AtomicDataProcessor(exp, two_theta)
bdr_factor, E_prime_keV = ap.calculate_recoil_factor()
f2, ff, cf, _           = ap.calculate_SF()
```
## Step 5 — Compute Intensity Corrections
```python
ic = IntensityCorrection(ap)
ic.compute_absorption()            # Paalman–Pings absorption correction
ic.compute_secondary_scatter()     # Double-scattering contribution
ic.compute_fluorescence_profile()  # Fluorescence background profile
```
## Step 6 — Optimise S(Q)
`SqOptimizer` uses the L-BFGS-B algorithm to optimize S(Q).
The optimization attempts to enforce:
* S(Q) → 1 at high Q
* F(Q) → 0 at high Q
```python
SQ_optimizer = OptSq(
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
optimizer = SqOptimizer(SQ_optimizer)
optimizer.optimize()
SQ_optimizer.report()
sq_results = SQ_optimizer.get_results()
```
## Step 7 — Calculate G(r)
```python
q  = SQ_optimizer.Q
sq = SQ_optimizer.S_FZ_final
FT_ra = calculate_Gr(
    q           = q,
    sq          = sq,
    r_step      = r_step,
    r_max       = r_max,
    window_type = 1,   # Standard Lorch modification function
)
r, G0, q_interp, Sq_used, fq_initial, fq_used = FT_ra.compute()
```
## Step 8 — Post-process G(r)
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
## Step 9 — Save Results
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
Output files:
```text
*.S0  → optimized S(Q)
*.G0  → raw G(r)
*.G1  → post-processed G(r)
```
All files are saved as two-column plain-text files.
## Pipeline Summary
```text
Raw .dat files
      │
      ▼
XrayDataProcessor       ← Load sample and background data
      │
      ▼
ExperimentalInfo        ← Experimental parameters
      │
      ▼
AtomicDataProcessor     ← Scattering factors and recoil correction
      │
      ▼
IntensityCorrection     ← Absorption and background corrections
      │
      ▼
OptSq + SqOptimizer     ← Optimize S(Q)
      │
      ▼
calculate_Gr            ← Fourier transform
      │
      ▼
PDFPostProcess          ← Low-r correction and density refinement
      │
      ▼
Save G0, G1, S0
```
