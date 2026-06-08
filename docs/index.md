# PDF-RABBIT

PDF-RABBIT is developed in the [Laboratory of Structural Inorganic Chemistry](https://strchem.eng.hokudai.ac.jp/) at Hokkaido University, under the supervision of Professor [Akira Miura](https://researchmap.jp/amiura).

PDF-RABBIT is an end-to-end framework for X-ray total scattering analysis, covering data reduction to structural refinement.

---

Reducing total scattering data requires several steps:

- Angle dependent intensity corrections — secondary scattering, polarization, absorption, background subtraction, and fluorescence.
- Normalization to electron units.
- Subtraction of incoherent and Laue monotonic scattering.

These steps are usually split across different programs and rely on manual treatment. As a result, for the same total scattering data:

- The resulting `S(Q)` and `g(r)` are hard to reproduce.
- The local structure obtained can depend strongly on the analysis tools used.

```{note}
*Read more:*

1. Gallington, L. C. *et al.* [Review of Current Software for Analyzing Total X-ray Scattering Data from Liquids](https://doi.org/10.3390/qubs7020020). *Quantum Beam Science* **2023**, *7*(2), 20.
2. Stubkjær, R. B. *et al.* [Reliability of Pair Distribution Function Analysis in In Situ Experiments](https://doi.org/10.1107/S1600576725001694). *Journal of Applied Crystallography* **2025**, *58*(2).
```

---

PDF-RABBIT unifies these steps and removes the manual guesswork.
It tunes the correction parameters by automated optimization:

- To ensure accurate normalization to electronic scale.
- Such that the extracted `S(Q)` and `F(Q)` obey known physical limits, then extracts `g(r)` and related functions.

The toolkit works in two steps: **Chapter 1** reduces raw data to `G(r)`;
**Chapter 2** fits a structural model to that `G(r)`.

---

```{toctree}
:maxdepth: 1
:caption: Getting Started

introduction
installation
```

```{toctree}
:maxdepth: 2
:caption: Chapter 1 · Data Reduction

quickstart
theory
examples
```

```{toctree}
:maxdepth: 2
:caption: Chapter 2 · Small-Box Refinement

rquickstart
reference
disorder
comparison
```
