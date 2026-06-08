# PDF Rabbit Fit — Advanced Guide & Reference

This covers the four classes you interact with directly, every argument that
matters for use, the full tag vocabulary for staged refinement, and the
controls for bounds, regularization, and output.

You normally touch only: `PDFStructure`, `PDFCalculator`, `PDFRefiner`,
`SequentialRefiner`. The parameter machinery (`ParameterManager`,
`StructuralParameters`, `PDFParameters`, `StructureUpdater`) runs underneath;
the parts you may want are listed at the end.

---

## PDFStructure

Loads a CIF, runs the symmetry analysis, builds the pair list and ADP tensors.

```python
PDFStructure(cif_path, symprec=1e-5, use_symmetry=True)
```

| arg | meaning |
|---|---|
| `cif_path` | path to the CIF. |
| `symprec` | symmetry tolerance passed to spglib/pymatgen. Loosen (e.g. `1e-3`) for slightly noisy experimental CIFs. |
| `use_symmetry` | `True`: loop over the asymmetric unit and weight pairs by site multiplicity (fast, exact for symmetric CIFs); parameters are named `element_wyckoff`. `False`: treat every atom independently (P1) — for supercells, disordered models, or manually broken symmetry. |

Useful methods:

- `initial_structure()` — printed table of lattice, sites (each species of a
  mixed site on its own row), occupancies, coordinates, ADPs.
- `degrees_of_freedom()` — printed Y/N table of symmetry-allowed refinable
  parameters, with the lattice/position/ADP totals and a separate count of
  optional occupancy parameters (occupancy is **not** in the DoF total).
- `refresh_occupancy()` — recompute Σocc, N_eff, ρ₀ after editing `site_occ`
  directly.

Attributes worth knowing: `N`, `V`, `num_dens`, `elems` (dominant element per
site), `site_elems` (tuple of species per site), `site_occ` (per-species
occupancies), `occ` (per-site total), `Uij_crystal`.

---

## PDFCalculator

Computes G(r) from a `PDFStructure` using the Jeong "rabbit" Gaussian peak
model. Build once; re-evaluate by setting attributes or calling it.

```python
PDFCalculator(structure,
              rmin=0.0, rmax=20.0, rstep=0.01, maxextension=5.0,
              qmin=0.0, qmax=0.0,
              biso=0.0, scale=1.0,
              spdiameter=0.0, stepcut=0.0,
              peakprecision=3.33e-6, peak_width_model='jeong_rabbit',
              use_charge=False, Q=0.0, Q_default=0.0, energy_keV=None,
              zero_shift=0.0,
              qdamp=0.001, delta1=0.001, delta2=0.001, qbroad=0.001, cbroad=0.001)
```

**r-grid**

| arg | meaning |
|---|---|
| `rmin`, `rmax`, `rstep` | output r-range and step (Å). |
| `maxextension` | extra Å added to `rmax` when building the pair list, so peaks just past `rmax` still contribute. |

**Q-space / termination**

| arg | meaning |
|---|---|
| `qmin`, `qmax` | Q-range limits (Å⁻¹); `0` disables. Non-zero applies a finite-Q termination via FFT round-trip. |
| `qdamp` | Gaussian resolution damping `exp(-½(qdamp·r)²)` — the dominant instrument-broadening term. |
| `qbroad`, `cbroad` | Q-dependent and constant peak-broadening terms inside the width model. |

**Peak width / displacement**

| arg | meaning |
|---|---|
| `biso` | global Biso override (Å²). `0` = use per-pair MSD from the CIF ADPs (normal case). |
| `delta1`, `delta2` | correlated-motion sharpening of near-neighbour peaks (`1/r` and `1/r²` terms). |

**Scattering factors**

| arg | meaning |
|---|---|
| `Q` | momentum transfer for evaluating f0(Q). Scalar (same for all elements) **or** a dict `{'Ce':1.5,'O':2.0}`. Default `0.0` ⇒ f0 = atomic number (electron count). |
| `Q_default` | fallback Q for elements absent from a per-element `Q` dict. |
| `use_charge` | use ionic form factors; oxidation states come from the CIF or a manual `structure.add_oxidation_state_by_element(...)`. Falls back to neutral if absent. |
| `energy_keV` | apply anomalous dispersion (f′, f″) at this beam energy. |

**Shape / cut / shift**

| arg | meaning |
|---|---|
| `scale` | overall scale factor. |
| `spdiameter` | spherical nanoparticle envelope diameter (Å); `0` disables. |
| `stepcut` | hard cutoff in r (Å); `0` disables. |
| `zero_shift` | constant offset applied to the experimental r-axis (Å). |
| `peakprecision` | peak truncation threshold (smaller = wider Gaussian tails kept). |
| `peak_width_model` | `'jeong_rabbit'` (only model). |

Methods / properties:

- `compute_gr()` → `(r, gr, rdf, baseline, envelope, d_pairs, fwhms)`.
- `compute_rdf()` → `(rdf, d_pairs, fwhm)`.
- `get_all()` → dict with `r, gr, rdf, baseline, envelope, f0, f_avg, norm, p_w, …`.
- `calc(rmax=25, qdamp=0.05)` — set any constructor parameter and re-evaluate;
  returns `(r, gr)`.
- properties: `pdf`, `rdf`, `rgrid`, `feff` (per-site effective scattering),
  `numdensity`, `slope`, `fwhm_DW`.

> Defaults note: the Jeong profile terms default to `0.001`, not `0`, so a
> freshly built calculator already has a small physical width. Set `qdamp`
> to your instrument value before fitting.

---

## PDFRefiner

Wraps a calculator + observed data and exposes the parameter set. All
refinable parameters are created automatically on construction.

```python
PDFRefiner(calculator, obs_file, rmin=None, rmax=None, sigma=None, verbose=True)
```

| arg | meaning |
|---|---|
| `calculator` | a `PDFCalculator`. |
| `obs_file` | two-column text file `r  G(r)` (`#` comments allowed). |
| `rmin`, `rmax` | fit window (Å); default to the calculator's range. |
| `sigma` | per-point uncertainties for weighting; either length-of-data or already masked. Default uniform weights. |
| `verbose` | print a load summary. |

Setup methods:

- `set_bounds(name, lo, hi)` — set bounds; `lo == hi` fixes the parameter.
- `set_regularization(type, weight)` — `'none' | 'barrier' | 'log' | 'l2'`;
  a soft penalty that steers parameters away from their bounds.
- `set_occ_mode(name, mode)` / `set_occ_swap(free, complement, equals)` —
  occupancy controls (see the Disordered-phase guide).
- `show_parameters()` — value / stderr / bounds / status table.

Run / output:

- `refine(method='least_squares', max_iter=1000, save_report=None, **minimize_kws)`
  — `minimize_kws` pass straight to lmfit (e.g. `ftol=1e-12`). Returns the
  lmfit result. Use this for one-shot fits; otherwise prefer `SequentialRefiner`.
- `calculate_rwp()` → current Rwp (%).
- `plot(figsize=(12,8), show=True, save_path=None)`.
- `save_structure(filename, adp_mode='aniso')` — refined CIF; `adp_mode='iso'`
  collapses ADPs to isotropic. Refined occupancies are written too.
- `get_refinement_data(filename)` — `r, G_obs, G_calc, diff`.
- `save_report(filename)` — JSON of parameters + Rwp history.

---

## SequentialRefiner

Runs a chain of refinement stages, each freeing a tag group on top of the
previous result. This is the primary fitting interface.

```python
seq = SequentialRefiner(ref)
seq.add_stage(*args, method='least_squares', max_iter=500)
seq.run(save_reports=False, report_prefix='stage')
```

- `add_stage(label, *tags)` — if the first argument isn't a known tag/param it
  is used as a label; the rest are tags. Each stage fixes everything, then
  frees the resolved tags (user-fixed parameters stay fixed).
- `run(...)` — executes every stage in order, printing the per-stage Rwp
  transition and a parameter table, then a final summary.
- `rwp_progression()` → list of per-stage Rwp.
- `plot(**kwargs)`, `save_structure(filename)`, `save_summary(filename)`.

### Tag vocabulary

| tag | frees |
|---|---|
| `all` | everything **except** occupancy (symmetry-fixed ADP/lattice components stay fixed). |
| `lattice` | symmetry-free lattice parameters. |
| `lattice_iso` / `lattice_dia` / `lattice_offdia` | lattice subsets (cell lengths / diagonal / angles). |
| `a` `b` `c` `alpha` `beta` `gamma` | one lattice parameter. |
| `positions` or `xyz` | all symmetry-free atomic coordinates. |
| `x` `y` `z` | a coordinate axis across all atoms. |
| `adp` | all ADP parameters. |
| `adp_iso` | isotropic ADPs (`Uiso_*`). |
| `adp_dia` / `adp_nondia` | diagonal / off-diagonal anisotropic components. |
| `U11`…`U23`, `Uiso` | a single ADP component across atoms. |
| `pdf` | peak-profile terms: `scale`, `zero_shift`, `qdamp`, `delta1`, `delta2`, `qbroad`, `cbroad`. |
| `occ` | all occupancy parameters (expr-linked swap partners auto-skipped). |
| *param name* | free exactly that parameter, e.g. `qdamp`, `Uiso_O_c`. |
| *atom+axis* | e.g. `O_c_x` (one coordinate of one site). |
| *component+atom* | e.g. `U11_Ce_a`. |

Parameter names in symmetric mode are `element_wyckoff` (`Ce_a`, `O_c`,
`S_d`, `Br_a`); a same-element/same-Wyckoff collision gets an ordinal
(`Li_h_1`, `Li_h_2`). Position params are `pos_<label>_<axis>`, ADPs are
`<comp>_<label>`, occupancies are `occ_<species>_<wyckoff>`.

---

## Under-the-hood classes (occasionally useful)

- **StructuralParameters(analyzer)** — the symmetry-derived parameter lists:
  `get_lattice_params()`, `get_position_params()`, `get_adp_params()`,
  `get_occ_specs()` (per-species occupancy specs), `get_constraints()`,
  `print_summary()`.
- **PDFParameters(model)** — the profile-term catalog:
  `get_params()`, `get_default(name)`, `get_bounds(name)`, `print_summary()`.
- **StructureUpdater(structure)** — applies parameter values back to the
  structure and syncs ADP/occupancy for export. You rarely call this directly;
  `save_structure` uses `sync_occ_to_structure()` and `sync_adp_to_map()`.

Access the live managers from a refiner via `ref.pm` (the `ParameterManager`),
`ref.structural_params`, and `ref.pdf_params`.

---

## A fuller refinement

```python
st   = PDFStructure("material.cif", symprec=1e-4)
calc = PDFCalculator(st, rmin=1.0, rmax=30.0, rstep=0.01,
                     qdamp=0.045, qmax=24.0)
ref  = PDFRefiner(calc, "material.gr", rmin=1.5, rmax=28.0)

ref.set_bounds("a", 0.99*calc.structure.lengths[0], 1.01*calc.structure.lengths[0])
ref.set_regularization("barrier", weight=0.05)   # keep ADPs off their bounds

seq = SequentialRefiner(ref)
seq.add_stage("warm-up",   "scale")
seq.add_stage("cell",      "lattice")
seq.add_stage("profile",   "qdamp", "delta1", "delta2")
seq.add_stage("coords",    "positions")
seq.add_stage("thermal",   "adp_iso")
seq.add_stage("polish",    "all")
seq.run(save_reports=True)

print(seq.rwp_progression())
seq.save_structure("material_refined.cif")
seq.save_summary("material_stages.json")
```
