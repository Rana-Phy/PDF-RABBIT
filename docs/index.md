# PDF-RABBIT

PDF-RABBIT was developed in the [Laboratory of Structural Inorganic Chemistry](https://strchem.eng.hokudai.ac.jp/) at Hokkaido University, under the supervision of Professor [Akira Miura](https://researchmap.jp/amiura).

PDF-RABBIT is an end-to-end analysis framework for X-ray total scattering data. It covers the whole process, from data reduction to structural refinement.

In total scattering, turning raw data into a reliable `S(Q)` and `g(r)` needs many corrections — for example absorption, secondary scattering, Compton scattering, polarization, and fluorescence — along with normalization to electron units. At present these steps are spread across several different programs, and many of the choices depend on the user. Because of this, the same measurement can give different results in different hands, and the manual work does not scale to large high-throughput or in-situ datasets.

PDF-RABBIT brings these steps into a single workflow and removes the manual guesswork. It tunes the corrections together with the electron-unit normalization by automated optimization, so that the resulting `S(Q)` and `F(Q)` obey known physical limits (such as `S(Q) → 1` at high `Q`). This makes the reduction objective and reproducible. From the optimized `S(Q)`, PDF-RABBIT then extracts `g(r)` and related functions, and supports the structural refinement that follows.

```{toctree}
:maxdepth: 2
:caption: Contents

installation
quickstart
theory
examples
```
