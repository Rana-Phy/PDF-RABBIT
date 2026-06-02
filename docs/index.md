# PDF-RABBIT
PDF-RABBIT was developed in the Laboratory of Structural Inorganic Chemistry at Hokkaido University under the supervision of Professor Akira Miura.
PDF-RABBIT is an end-to-end framework for X-ray total scattering analysis, covering the complete workflow from data reduction to structural refinement.
Reducing total scattering data requires several correction and normalization steps, including:
- Angle-dependent intensity corrections (secondary scattering, polarization, absorption, background subtraction, and fluorescence)
- Normalization to electron units
- Subtraction of incoherent and Laue monotonic scattering
These procedures are often distributed across multiple software packages and frequently require manual parameter selection. Consequently, identical total scattering datasets can yield different results depending on the analysis workflow used. Previous studies have shown that:
- The resulting `S(Q)` and `g(r)` can be difficult to reproduce consistently across different software packages [1,2].
- The inferred local structure may depend strongly on the chosen analysis tools and reduction procedures [1,2].

PDF-RABBIT addresses these challenges by integrating the entire reduction workflow into a unified framework and minimizing manual intervention. The software automatically optimizes correction parameters to:
- Achieve accurate normalization to the electronic scattering scale
- Ensure that the extracted `S(Q)` and `F(Q)` satisfy known physical constraints
- Generate reliable `g(r)` and related real-space structural functions
By automating and standardizing the reduction process, PDF-RABBIT improves the reproducibility and reliability of X-ray total scattering analysis.

## References

1. Gallington, L. C. *et al.* *Review of Current Software for Analyzing Total X-ray Scattering Data from Liquids*. *Quantum Beam Science* **2023**, *7*(2), 20.
2. Stubkjær, R. B. *et al.* *Reliability of Pair Distribution Function Analysis in In Situ Experiments*. *Journal of Applied Crystallography* **2025**, *58*(2).
```{toctree}
:maxdepth: 2
:caption: Contents
introduction
installation
quickstart
theory
examples
```
