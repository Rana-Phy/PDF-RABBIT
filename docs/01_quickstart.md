# PDF Rabbit Fit — Quick Start

A minimal X-ray PDF refinement, start to finish: load a CIF, compute G(r),
fit it against measured data, plot, and save the refined structure.

## Install / import

The toolkit is a set of modules (no package install). Put them on your path
and import:

```python
from structure   import PDFStructure
from calculator  import PDFCalculator
from refiner     import PDFRefiner, SequentialRefiner
```

Dependencies: `pymatgen`, `numpy`, `numba`, `lmfit`, `xraydb`, `matplotlib`,
`scipy`, `tabulate`.

## 1. Load a structure

```python
st = PDFStructure("CeO2.cif")          # symmetry on by default
st.initial_structure()                 # printed summary: lattice, sites, ADPs
st.degrees_of_freedom()                # symmetry-allowed refinable parameters
```

`initial_structure()` prints one row per crystallographic site (both species
at a mixed site), with Wyckoff letter, multiplicity, occupancy, fractional
coordinates, and ADP. `degrees_of_freedom()` prints a Y/N table of which
lattice/position/ADP parameters symmetry allows you to refine.

## 2. Compute G(r)

```python
calc = PDFCalculator(
    st,
    rmin = 1.0, rmax = 20.0, rstep = 0.01,
    qdamp = 0.04,                      # instrument resolution damping
)
r, G = calc.compute_gr()[:2]           # r-grid and G(r)
```

`compute_gr()` returns `(r, gr, rdf, baseline, envelope, d_pairs, fwhms)`;
take the first two for a plain G(r). For everything in one dict, use
`calc.get_all()`.

## 3. Refine against measured data

The observed file is a two-column text file `r  G(r)` (comment lines with `#`).
Parameters are created automatically when you build the refiner.

```python
ref = PDFRefiner(calc, "CeO2_measured.gr", rmin=1.5, rmax=20.0)
```

Refinement is staged: each stage frees a group of parameters (by *tag*),
fits, then the next stage builds on the result. This is the recommended
workflow and is far more stable than freeing everything at once.

```python
seq = SequentialRefiner(ref)
seq.add_stage("scale")                     # overall scale first
seq.add_stage("lattice")                   # symmetry-free lattice params
seq.add_stage("qdamp", "delta1")           # peak-profile terms
seq.add_stage("adp_iso")                   # isotropic displacement params
seq.run()                                  # prints per-stage Rwp + tables
```

`add_stage(*tags)` frees the listed tag groups for that stage. You can prefix
an optional **label** (any string that isn't itself a tag/parameter name):
`seq.add_stage("thermal", "adp_iso")`. Common tags: `scale`, `lattice`,
`positions`, `adp`, `adp_iso`, `pdf`, `all` (everything *except* occupancy),
or any individual parameter name. See the Advanced guide for the full list.

## 4. Inspect, plot, save

```python
print("final Rwp:", ref.calculate_rwp())
ref.plot()                                 # observed / calculated / difference
ref.show_parameters()                      # value, stderr, bounds, status

ref.save_structure("CeO2_refined.cif")     # writes refined CIF (ADPs included)
ref.get_refinement_data("CeO2_fit.txt")    # r, G_obs, G_calc, difference
ref.save_report("CeO2_report.json")        # parameters + Rwp history
```

## Full example

```python
from structure  import PDFStructure
from calculator import PDFCalculator
from refiner    import PDFRefiner, SequentialRefiner

st   = PDFStructure("CeO2.cif")
calc = PDFCalculator(st, rmin=1.0, rmax=20.0, rstep=0.01, qdamp=0.04)

ref  = PDFRefiner(calc, "CeO2_measured.gr", rmin=1.5, rmax=20.0)
seq  = SequentialRefiner(ref)
seq.add_stage("warm-up", "scale")
seq.add_stage("cell",    "lattice")
seq.add_stage("profile", "qdamp", "delta1")
seq.add_stage("thermal", "adp_iso")
seq.run()

ref.plot()
seq.save_structure("CeO2_refined.cif")
seq.save_summary("CeO2_stages.json")
```

## Tips

- **Bounds / fixing:** `ref.set_bounds("a", 5.40, 5.42)`. Setting equal bounds
  (`set_bounds("scale", 1.0, 1.0)`) fixes a parameter at that value.
- **Refine order matters:** scale → lattice → profile → positions → ADP is a
  reliable default. ADPs and the profile terms (`qdamp`, `delta1`, `delta2`)
  correlate, so don't free them in the same early stage.
- **Occupancy is opt-in.** It is never refined by the `all` tag; you free it
  explicitly with the `occ` tag or `occ_*` names. See the Disordered-phase
  guide.
- **Reproducible peak widths:** `qdamp` captures instrument resolution;
  `delta1`/`delta2` capture correlated motion (sharper near-neighbour peaks).
