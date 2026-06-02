# Quickstart

A minimal end-to-end run looks like this:

```python
from xrd_data_processor import XrayDataProcessor, XrayDataPlotter
from experimental_info import ExperimentalInfo
from atomic_data_processor import AtomicDataProcessor
from intensity_correction import IntensityCorrection
from opt_sq import OptSq, SqOptimizer
from calculate_rpdf import calculate_Gr
from rpdf_postprocess import PDFPostProcess
from rpdf_to_Sq import get_rSq

# 1. Load and preprocess raw data
proc = XrayDataProcessor(
    sample_path="raw_data/CeO2.dat",
    container_path="raw_data/capillary.dat",
    sample_step_positions=[64.115, 70],
    step_window_pts=500,
)
two_theta, I_raw, I_bkg = proc.get_processed_data()

# 2. Describe the experiment
exp = ExperimentalInfo(
    geometry="cylindrical",
    sample_composition="CeO2",
    sample_density=7.22,
    container_composition="SiO2",
    container_density=2.0,
    d_inner=0.029,
    d_outer=0.03,
    wavelength=0.247949,
)

# 3. Corrections, S(Q) optimization, G(r), and post-processing follow.
# See the Example Notebooks for a complete, runnable workflow.
```

<!-- Expand each step with explanation and expected outputs. -->
