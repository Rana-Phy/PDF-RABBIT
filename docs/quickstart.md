# Quick Start Guide

This guide walks through a complete X-ray total scattering analysis from raw data to a refined pair distribution function G(r), using CeO₂ in a 0.3 mm quartz capillary as the worked example.

---

## Prerequisites

```python
import numpy as np
import matplotlib.pyplot as plt

from experimental_info import ExperimentalInfo
from xrd_data_processor import XrayDataProcessor, XrayDataPlotter
from atomic_data_processor import AtomicDataProcessor
from intensity_correction import IntensityCorrection
from opt_sq import OptSq, SqOptimizer
from calculate_rpdf import calculate_Gr
from rpdf_postprocess import PDFPostProcess
from rpdf_to_Sq import get_rSq
```

---

## Step 1 — Load and Pre-process Raw Data

`XrayDataProcessor` loads the sample and container (capillary/background) diffraction files, masks detector dead zones, and optionally extrapolates the low-angle region.

```python
folder = r"./raw_data/"
data_file      = 'CeO2_10s_0.3mm.dat'
capillary_file = 'quartz_10s_0.3mm_1.dat'

data_processor = XrayDataProcessor(
    sample_path    = folder + data_file,
    container_path = folder + capillary_file,

    # Dead-zone / step mask: exclude detector gaps near these 2θ positions.
    # Each value is the centre of a gap; step_window_pts sets the half-width.
    sample_step_positions = [64.115, 70],
    step_window_pts       = 500,

    # Minimum usable 2θ angle (degrees). Data below this are discarded.
    tth_min = 0.8,

    # Extrapolate the low-angle region to reach [0.03°, 0.9°].
    # Useful when the beam-stop cuts off data before the first measured point.
    extrapolate_to = [0.03, 0.9],
)

two_theta, I_raw, I_bkg = data_processor.get_processed_data()
XrayDataPlotter(data_processor).plot()   # inspect raw vs background
```

**Key parameters**

| Parameter | Description |
|---|---|
| `sample_step_positions` | 2θ positions (°) of detector gaps to mask |
| `step_window_pts` | Number of points masked on each side of a gap |
| `tth_min` | Low-angle cut-off (°) |
| `extrapolate_to` | `[tth_start, tth_end]` range to extrapolate toward (°) |

---

## Step 2 — Define the Experiment

`ExperimentalInfo` holds all geometry, sample, and beam parameters that are shared across the pipeline.

```python
exp = ExperimentalInfo(
    geometry            = 'cylindrical',   # 'cylindrical' | 'flat-plate' | 'linear'
    sample_composition  = 'CeO2',
    sample_density      = 7.22,            # g cm⁻³  (set < true density to account for packing)
    container_composition = 'SiO2',
    container_density   = 2.0,             # g cm⁻³  (effective wall density)
    d_inner             = 0.029,           # cm  — inner diameter of capillary
    d_outer             = 0.03,            # cm  — outer diameter of capillary
    wavelength          = 0.247949,        # Å   — synchrotron wavelength
)
```

**Geometry options**

| Value | Use case |
|---|---|
| `'cylindrical'` | Capillary / Debye–Scherrer geometry |
| `'flat-plate'` | Transmission or reflection flat-plate |
| `'linear'` | Simple path-length geometry |

---

## Step 3 — Compute Atomic Scattering Factors

`AtomicDataProcessor` calculates Q-dependent form factors, the Compton (incoherent) scattering function, and the Breit–Dirac recoil factor for the given composition and geometry.

```python
ap = AtomicDataProcessor(exp, two_theta)

# Breit–Dirac recoil factor (E'/E) per Q-point.
# bdr_order in OptSq controls the exponent n in I_comp ∝ (E'/E)^n.
bdr_factor, E_prime_keV = ap.calculate_recoil_factor()

# Retrieve scattering factor arrays:
#   f2  = <f²>  (mean of squared form factors, FSM)
#   ff  = <f>²  (squared mean form factor, FMS)
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

**Two-stage fluorescence API**

For synchrotron data with no fluorescence, calling `compute_fluorescence_profile()` with default arguments (all zeros) is still required so the pipeline has a valid `_I_f_raw` array. When fluorescence is present, set `fluorescence_bounds` in `OptSq` to a non-zero range and the optimiser will scale the profile automatically via `apply_fluorescence(f_f)` at negligible cost per iteration.

For laboratory (tube) sources with Bremsstrahlung, pass `f_Br` and `lab_kwargs`:

```python
ic.compute_fluorescence_profile(
    f_Br       = 0.05,
    lab_kwargs = dict(Ee=60, E0=0.5, w=0.2, L_T=0.1,
                      L_F=0.05, Z_anode=47, Z_filter=45),
)
```

---

## Step 5 — Optimise S(Q)

`OptSq` defines the parameter bounds and wraps the correction pipeline. `SqOptimizer` runs L-BFGS-B to minimise a loss function that drives S(Q) → 1 at high Q, F(Q) mean → 0 at high Q, and S(0) → the theoretical Faber–Ziman limit.

```python
SQ_optimizer_rk = OptSq(
    Q              = ap.Q,
    two_theta      = two_theta,
    I_sample       = I_raw,
    I_container    = I_bkg,       # raw counts — PP correction applied internally

    # Scattering factor arrays from Step 3
    FSM            = f2,          # <f²>
    FMS            = ff,          # <f>²
    CFF            = cf,          # Compton function
    bdr_factor     = bdr_factor,  # Breit–Dirac recoil factor

    corr           = ic,          # IntensityCorrection object from Step 4

    # Background derivation: bgscale = min(I_sample) / max(I_container)
    # over the Q window [bg_q_range[0], bg_q_range[1]].
    bg_q_range     = [0.92, 33],

    # Q range used for high-Q normalisation (S(Q) → 1 target).
    high_q_range   = (22, 31.5),

    # ── Parameter bounds (lo, hi) ──────────────────────────────────────────
    # Setting lo == hi fixes a parameter at that value.

    polfact_bounds       = (1, 1),           # polarisation factor (fixed at 1 for synchrotron)
    fluorescence_bounds  = (0.0001, 1e5),    # fluorescence scaling factor f_f
    comp_damp_bounds     = (0, 1),           # Compton damping exponent
    bdr_order_bounds     = (2, 2),           # Breit–Dirac recoil exponent (fixed at 2)
    eta1_bounds          = (0, 0),           # cs_bias exponent (inactive for sys_bias='wf')
    eta2_bounds          = (0, 0),           # wf_bias exponent (inactive; set range to enable)

    # Number density (atoms Å⁻³). Required for scaling_by='integration'.
    rho_0          = 0.0757,

    # Systematic bias correction mode: 'wf' | 'cs' | 'full'
    sys_bias       = 'wf',

    # Normalisation method: 'mean' (high-Q ratio) | 'integration' (Krogh-Moe / Norman)
    scaling_by     = 'integration',
)

optimizer = SqOptimizer(SQ_optimizer_rk)
optimizer.optimize()

SQ_optimizer_rk.report()          # print quality metrics and optimised parameters
sq_results_rk = SQ_optimizer_rk.get_results()
```

**Key parameter guide**

| Parameter | Typical range | Notes |
|---|---|---|
| `bg_q_range` | `[Q_min, Q_max]` Å⁻¹ | Window for background scale derivation; should sit in a flat, featureless region |
| `high_q_range` | `(Q_lo, Q_hi)` Å⁻¹ | Should span at least ~10 Å⁻¹; avoid artefacts at the data edge |
| `polfact_bounds` | `(0.8, 1.0)` | Only float when lab source with significant polarisation |
| `fluorescence_bounds` | `(0, 0)` → no fluorescence; `(1e-4, 1e5)` → float | Scale with caution: large f_f can distort low-Q |
| `comp_damp_bounds` | `(0, 1)` | Damps Compton function at high Q; useful for noisy data |
| `bdr_order_bounds` | `(2, 2)` fixed; `(2, 3)` float | 2 = energy-integrated detector, 3 = photon-counting |
| `scaling_by` | `'integration'` | Preferred when `rho_0` is known; `'mean'` is robust when density is uncertain |
| `sys_bias` | `'wf'` | Use `'full'` to activate both cs and wf bias terms simultaneously |

**Optimising the background Q-window lower bound**

If the optimal low-Q cutoff for background subtraction is uncertain, pass `bg_q_min_bounds` to run an automatic two-stage coarse/fine grid scan:

```python
SQ_optimizer_rk = OptSq(
    ...
    bg_q_range     = [0.5, 33],       # wide window; lower bound will be refined
    bg_q_min_bounds = (0.5, 5.0),     # search range for the lower bound
)
```

The winning lower bound is the one that minimises `|S(0) − S₀_theoretical| + max(0, S(0) − min(S(Q)))`.

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
    sigma2      = 0,       # Gaussian damping (0 = none)
    window_type = 3,       # Lorch modification function (3 = standard Lorch)
)

r, G0, q_interp, Sq_used, fq_initial, fq_used = FT_ra.compute()
```

**`window_type` options**

| Value | Function |
|---|---|
| `0` | None (rectangular — maximum resolution, highest termination ripple) |
| `1` | Hann |
| `2` | Hamming |
| `3` | Lorch (recommended — suppresses termination ripple with minimal broadening) |

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

## Step 8 — Iterative Back-transform Refinement

`get_rSq` provides Fourier back-transforms to iteratively refine S(Q) and G(r). Each cycle suppresses unphysical low-r oscillations while preserving the high-Q information.

```python
ift = get_rSq(q_arry=q_interp, r_arry=r)

# Cycle 1
S1 = ift.Gr_to_rSq(G1)    # G(r) → S(Q)
G2 = ift.rSq_to_rGr(S1)   # S(Q) → G(r)  (low-r constrained)

# Cycle 2
S2 = ift.Gr_to_rSq(G2)
G3 = ift.rSq_to_rGr(S2)

# Cycle 3
S3 = ift.Gr_to_rSq(G3)
```

Two to three cycles are typically sufficient. More cycles rarely improve the result further.

---

## Step 9 — Save Results

```python
base_name = data_file.replace('.dat', '')

# G(r) at each refinement stage
np.savetxt(folder + base_name + ".G0", np.column_stack((r, G0)))   # raw FT
np.savetxt(folder + base_name + ".G1", np.column_stack((r, G1)))   # after post-process
np.savetxt(folder + base_name + ".G3", np.column_stack((r, G3)))   # after 3 back-transform cycles

# S(Q)
np.savetxt(folder + base_name + ".S0", np.column_stack((q_interp, Sq_used)))  # optimised S(Q)
np.savetxt(folder + base_name + ".S3", np.column_stack((q_interp, S3)))       # after 3 back-transform cycles
```

All output files are plain two-column ASCII (space-delimited): `r  G(r)` or `Q  S(Q)`.

---

## Pipeline Summary

```
Raw .dat files
      │
      ▼
XrayDataProcessor          — mask dead zones, extrapolate low-angle
      │
      ▼
ExperimentalInfo           — geometry, composition, density, wavelength
      │
      ▼
AtomicDataProcessor        — form factors f², Compton CFF, BDR factor
      │
      ▼
IntensityCorrection        — absorption (PP), secondary scatter, fluorescence
      │
      ▼
OptSq + SqOptimizer        — optimise S(Q): background, polarisation, Compton, α
      │
      ▼
calculate_Gr               — Fourier transform S(Q) → G(r)
      │
      ▼
PDFPostProcess             — low-r constraint, density refinement
      │
      ▼
get_rSq                    — iterative back-transform refinement
      │
      ▼
Save .G0/.G1/.G3/.S0/.S3
```
