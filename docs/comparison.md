# PDF Rabbit Fit — Comparison with PDFfit2, PDFgui, and DiffPy-CMI

Where PDF Rabbit Fit sits relative to the established small-box PDF refinement
tools: what it reproduces exactly, what it does differently, and what it does
not (yet) do. The aim is an honest map, not a sales pitch.

All three reference tools share one lineage (the Billinge group): **PDFfit2** is
the C++ refinement engine, **PDFgui** is its GUI front-end, and **DiffPy-CMI**
is the modular modelling framework built on the same `libdiffpy`/`srreal` core.
PDF Rabbit Fit is an independent pure-Python re-implementation of the same
small-box Gaussian PDF model, so most of the *physics* is deliberately
identical — the differences are in scattering-factor handling, the peak-width
model, symmetry/DoF bookkeeping, and the user interface.

---

## The shared physics

PDF Rabbit Fit computes the same quantity as PDFfit2. From a structural model,

```
G_c(r) = (1/r) Σ_i Σ_j [ b_i b_j / ⟨b⟩² ] δ(r − r_ij)  −  4π r ρ₀
```

(Proffen & Billinge, 1999), with each delta convoluted by a Gaussian whose
width comes from the displacement parameters and the Jeong correlated-motion
model. PDF Rabbit Fit reproduces every piece of this:

| Effect | PDFfit2 / PDFgui | PDF Rabbit Fit |
|---|---|---|
| Pair weight | `b_i b_j / ⟨b⟩²` | `f_eff(i)·f_eff(j)`, norm `N·⟨f⟩²` |
| Peak shape | Gaussian | Gaussian (`jeong_rabbit`, Gaussian-only) |
| Resolution damping | `exp(−½ σ_Q² r²)` | `exp(−½(qdamp·r)²)` |
| Finite-Q termination | convolution with `sin(Q_max r)/r` | FFT band-limit at `qmax` (and `qmin`) |
| Nanoparticle envelope | `spdiameter` characteristic function | same `1 − 1.5x + 0.5x³`, `x = r/spdiameter` |
| Hard r-cutoff | `stepcut` | `stepcut` |

So for a symmetry-correct CIF with a single scalar Q and no anomalous
correction, PDF Rabbit Fit and PDFfit2 are computing the same model and should
agree to numerical precision. The interesting differences are below.

---

## Peak-width model — where `cbroad` lives

PDFfit2/PDFgui and DiffPy-CMI (`JeongPeakWidth`) all use the same correlated-
motion bracket. In PDF Rabbit Fit's notation the FWHM is

```
FWHM_ij = √(8 ln2) · σ⁰_ij · √( bracket )

bracket = 1 − δ1/r − δ2/r² + (qbroad·r)² + (8π²·cbroad)²
          └─────────────┘   └──────────┘   └───────────┘
           Jeong sharpening    Jeong         NEW: constant
           (short r)           broadening    broadening
                               (long r)
```

The first three contributions are the standard Jeong terms, identical in role
to the reference tools:

| Term | Sign / r-dependence | Physical role |
|---|---|---|
| `delta1` | `−δ1/r` | correlated-motion sharpening, dominant at **high T** |
| `delta2` | `−δ2/r²` | correlated-motion sharpening, dominant at **low T** |
| `qbroad` | `+(qbroad·r)²` | broadening that grows with r (resolution / strain) |

`cbroad` is the term with no counterpart in any of the three tools. It is an
**r-independent constant added inside the bracket**, so with the other terms
off it broadens *every* peak by the same fractional amount,

```
FWHM = FWHM_DW · √(1 + (8π²·cbroad)²)
```

The `8π²` factor is the B = 8π²U conversion, so `cbroad` reads as a constant
"B-like" excess width. This is physically distinct from each existing
mechanism, and the distinction is the whole point:

- it is **not** `delta1`/`delta2`, which *sharpen* and scale as `1/r`, `1/r²`
  (they vanish at large r);
- it is **not** `qbroad`, which *broadens* but scales as `r²` (it vanishes at
  small r);
- it is **not** `sratio`/`rcut` (see below), which is a *step* in r, not a
  constant offset.

`cbroad` captures broadening that is uniform across the whole r-range — the
kind produced by static/compositional disorder that neither follows the
near-neighbour correlated-motion law nor the resolution law. It must never be
mapped onto a PDFfit2 parameter; there is no PDFfit2 parameter with this
r-dependence.

> **Implementation note.** In the current code `cbroad` is only added when
> `qbroad != 0`. Until that guard is changed to `if self.cbroad != 0.0`, a
> `cbroad`-only refinement does nothing and the term is not actually
> independent. The description above assumes the fix.

### What PDF Rabbit Fit does *not* have: `sratio` / `rcut`

PDFfit2/PDFgui offer a second, alternative way to sharpen near-neighbour peaks:
multiply the width by a factor `sratio` for all `r < rcut` (Proffen & Billinge
1999; `rcut` is itself non-refinable). It is a discontinuous step in r, used
for rigid structural units, and — per the PDFgui guide — should **not** be used
together with `delta1`/`delta2`. PDF Rabbit Fit implements only the continuous
Jeong terms plus `cbroad`; it has no `sratio`/`rcut` step. A refinement that
needs an explicit sub-`rcut` sharpening step is currently a PDFfit2/PDFgui case.

---

## Scattering factors

This is the other substantive physics difference, and the reference tools
themselves differ here.

**PDFfit2 / PDFgui.** The scattering power `b_i` is a *constant* per atom type:
the neutron scattering length, or for X-rays the atomic form factor evaluated
at a single user-chosen Q — default **Q = 0**, i.e. `b_i = Z_i` (the electron
count). There is no Q-dependence inside the double sum and no anomalous
(energy-dependent) correction. The Q-dependence of f is assumed already removed
during data reduction.

**DiffPy-CMI.** Uses a pluggable `ScatteringFactorTable` (X-ray, neutron,
electron), so the X-ray form factor can be applied with its proper Q-dependence
rather than as a single constant. The most complete treatment of the three.

**PDF Rabbit Fit.** Like PDFfit2 it uses a *constant* f per element inside the
sum, but evaluated at a chosen Q rather than forced to Q = 0:

- `Q` may be a scalar (PDFfit2-style, one Q for all elements), or a
  **per-element dict**, e.g. `Q={'Ce': 1.5, 'O': 2.0}`, with `Q_default` for
  the rest;
- form factors come from `xraydb`, and **ionic** form factors are used when
  `use_charge=True` (oxidation states read from the CIF);
- **anomalous dispersion** is supported: with `energy_keV` set, the effective
  factor becomes `√((f0 + f′)² + f″²)` per element via Chantler tables.

So PDF Rabbit Fit sits between PDFfit2 (single constant, no anomalous) and
DiffPy-CMI (full Q-dependent table): it keeps the constant-per-element
approximation but lets you pick a representative Q per element and add
anomalous/ionic corrections that PDFfit2 lacks. It does **not** integrate
`f0(Q)` over the measured Q-range inside the sum — that remains a
DiffPy-CMI capability.

---

## Symmetry and degrees of freedom

| | symmetry handling |
|---|---|
| PDFFIT (original) | none — every atom in the cell/supercell entered explicitly; constraints written by hand in the command language |
| PDFfit2 / PDFgui | space-group constraints supported; positions and ADPs constrained to the chosen space group |
| DiffPy-CMI | arbitrary constraints/restraints via `diffpy.srfit` (fully programmable) |
| PDF Rabbit Fit | symmetry-allowed DoF **derived automatically** from the CIF via pymatgen/spglib |

PDF Rabbit Fit analyses the space group up front and reports exactly which
lattice/position/ADP parameters are free, which ADP components are constrained
to each other, and which are forced to zero — you free parameters by tag
(`lattice`, `positions`, `Uiso`, `pdf`, …) rather than coding constraints. The
pair sum is folded over the asymmetric unit weighted by site multiplicity, which
is an exact speed-up for symmetry-correct CIFs, with a P1 mode (`use_symmetry=
False`) for supercells and broken-symmetry models — the regime PDFfit2's
"enter every atom" approach is built for.

---

## Occupancy and disorder

All four keep per-site occupancy. PDF Rabbit Fit retains the **full per-site
composition** at mixed sites — every species scatters with `f_eff = Σ occ·f0`,
the density is `ρ₀ = Σocc / V`, matching the PDFfit2 weighting — rather than
collapsing a mixed site to its majority element. Coupled anti-site swaps are
expressible by linking occupancy parameters. See
`03_disordered_phase_fitting.md` for the details and the `Li₆PS₅Br` anti-site
example.

---

## Optimizer and interface

| | engine | optimizer | interface |
|---|---|---|---|
| PDFfit2 | C++ core, Python bindings | Levenberg–Marquardt, **analytic** derivatives | scripting |
| PDFgui | PDFfit2 | same | GUI, project tree, staged fits, multi-phase/multi-dataset |
| DiffPy-CMI | `libdiffpy`/`srreal` + `srfit` | any `scipy`/external optimizer; restraints, co-refinement of multiple datasets | Python framework |
| PDF Rabbit Fit | pure Python + Numba JIT | `lmfit` (least-squares LM by default; numerical Jacobian) | scripting, sequential staged refiner |

PDFfit2's analytic derivatives make its LM steps cheap and stable; PDF Rabbit
Fit relies on `lmfit`'s numerical Jacobian, which is simpler but can stall on
flat directions (e.g. a near-zero Jacobian on idealised synthetic data — a
numerical artefact, not a model error). For multi-dataset / multi-technique
co-refinement, DiffPy-CMI remains the most capable.

---

## Summary

| Capability | PDFfit2 | PDFgui | DiffPy-CMI | PDF Rabbit Fit |
|---|---|---|---|---|
| Gaussian small-box G(r) | ✓ | ✓ | ✓ | ✓ |
| Jeong `delta1`/`delta2`/`qbroad` | ✓ | ✓ | ✓ | ✓ |
| `sratio`/`rcut` step sharpening | ✓ | ✓ | ✓ | ✗ |
| **Constant `cbroad` term** | ✗ | ✗ | ✗ | ✓ (new) |
| `qdamp`, `spdiameter`, `stepcut` | ✓ | ✓ | ✓ | ✓ |
| X-ray f at single Q (default Z) | ✓ | ✓ | — | ✓ |
| Full Q-dependent f(Q) in sum | ✗ | ✗ | ✓ | ✗ |
| Per-element Q | ✗ | ✗ | ✓ | ✓ |
| Anomalous f′/f″, ionic f | ✗ | ✗ | partial | ✓ |
| Auto symmetry DoF from CIF | ✗ | ✓ (constraints) | via srfit | ✓ |
| Anisotropic ADPs | ✓ | ✓ | ✓ | ✓ |
| Multi-phase / multi-dataset | ✓ | ✓ | ✓ | ✗ |
| Neutron PDF | ✓ | ✓ | ✓ | ✗ (X-ray) |
| GUI | ✗ | ✓ | ✗ | ✗ |
| Analytic derivatives | ✓ | ✓ | optional | ✗ |

**Use PDF Rabbit Fit when** you want a transparent, hackable Python model with
automatic symmetry bookkeeping, per-element / anomalous / ionic X-ray
scattering, and the constant `cbroad` width term. **Reach for PDFfit2/PDFgui**
for `sratio`/`rcut`, neutron data, analytic-derivative speed, or a GUI; **reach
for DiffPy-CMI** for full Q-dependent form factors and multi-dataset
co-refinement with restraints.

---

## References

- Th. Proffen & S. J. L. Billinge, *PDFFIT, a program for full profile
  structural refinement of the atomic pair distribution function*,
  J. Appl. Cryst. **32**, 572–575 (1999).
- C. L. Farrow, P. Juhás, J. W. Liu, D. Bryndin, E. S. Božin, J. Bloch,
  Th. Proffen & S. J. L. Billinge, *PDFfit2 and PDFgui: computer programs for
  studying nanostructure in crystals*, J. Phys.: Condens. Matter **19**, 335219
  (2007).
- I. K. Jeong, Th. Proffen, F. Mohiuddin-Jacobs & S. J. L. Billinge,
  J. Phys. Chem. A **103**, 921–924 (1999) — correlated-motion peak-width model.
- P. Juhás, C. L. Farrow, X. Yang, K. R. Knox & S. J. L. Billinge, *Complex
  modeling: a strategy and software program …*, Acta Cryst. A **71**, 562–568
  (2015) — DiffPy-CMI.
