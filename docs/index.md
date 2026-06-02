# PDF-RABBIT

PDF-RABBIT was developed in the [Laboratory of Structural Inorganic Chemistry](https://strchem.eng.hokudai.ac.jp/) at Hokkaido University, under the supervision of Professor [Akira Miura](https://researchmap.jp/amiura).

PDF-RABBIT is an end-to-end framework for X-ray total scattering analysis, covering data reduction to structural refinement.

Reducing total scattering data requires several steps:

- angular and intensity corrections — secondary scattering, polarization, absorption, background, and fluorescence
- normalization to electron units
- subtraction of incoherent (Compton) and Laue monotonic scattering

These steps are usually split across different programs and rely on manual treatment. As a result, for the same total scattering data:

- the resulting `S(Q)` and `g(r)` are hard to reproduce
- the local structure obtained can depend strongly on the framework used

PDF-RABBIT unifies these steps and removes the manual guesswork. It tunes the corrections and electron-unit normalization by automated optimization so that `S(Q)` and `F(Q)` obey known physical limits, then extracts `g(r)` and related functions.

## Further reading

1. Gallington, L. C. *et al.* [Review of Current Software for Analyzing Total X-ray Scattering Data from Liquids](https://doi.org/10.3390/qubs7020020). *Quantum Beam Science* **2023**, *7*(2), 20.
2. Stubkjær, R. B. *et al.* [Reliability of Pair Distribution Function Analysis in In Situ Experiments](https://doi.org/10.1107/S1600576725001694). *Journal of Applied Crystallography* **2025**, *58*(2).

```{toctree}
:maxdepth: 2
:caption: Contents

installation
quickstart
theory
examples
```
