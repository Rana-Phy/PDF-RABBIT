# PDF Rabbit Fit — Disordered Phase Fitting

How the toolkit handles partial occupancy, vacancies, and mixed (anti-site)
sites, and how to refine occupancies — including coupled anti-site swaps.

---

## What "disorder" means here

A site can host more than one species (a **mixed** site, e.g. an anion-swap
site `{Br: 0.8, S: 0.2}`) and/or be partially occupied (a **vacancy** site,
`occ < 1`). The toolkit keeps the **full per-site composition**: every species
present scatters, with its peak scaled by occupancy, instead of collapsing the
site to its majority element.

This is the physically correct PDF treatment. The effective scattering of a
site is the occupancy-weighted sum over its species,

```
f_eff(site) = Σ_species  occ · f0
```

and a pair weight is `f_eff(i) · f_eff(j)`. Occupancy also feeds the average
scattering factor `⟨f⟩`, the normalization, and the number density ρ₀
(ρ₀ = Σocc / V), matching PDFfit2.

> **Position and ADP are shared per site** (taken from the dominant species);
> **occupancy is per species**. A mixed site is one position with several
> occupants, which is the usual crystallographic picture.

## Loading and inspecting

```python
from structure import PDFStructure
st = PDFStructure("Li6PS5Br.cif")     # argyrodite with Br/S anti-site mixing
st.initial_structure()
```

A mixed site prints as one row per species, sharing the Wyckoff/coords/ADP:

```
Atom    Wyck  Mult  Occ     x       y       z       ADP
S_d     d     4     0.8     0.75    0.75    0.75    Uiso=0.00010
Br_d                0.2
Br_a    a     4     0.8     0       0       0       Uiso=0.00010
S_a                 0.2

  2 mixed/disordered site(s); occupancy is an optional DoF (fixed unless freed via the 'occ' tag).
```

Labels are `element_wyckoff`. On the 4a site the majority is Br (`Br_a`) and
the minority S (`S_a`); on 4d it is reversed (`S_d` / `Br_d`).

`degrees_of_freedom()` reports the symmetry DoF (lattice/position/ADP) and,
separately, the count of optional occupancy parameters — occupancy is **never**
part of the DoF total and is fixed unless you free it.

## Occupancy is opt-in

Occupancy parameters exist for every (site, species) — named
`occ_<species>_<wyckoff>` (`occ_Br_a`, `occ_S_a`, `occ_S_d`, `occ_Br_d`, …) —
but they are fixed by default and excluded from the `all` tag. You free them
explicitly. Bounds modes:

```python
ref.set_occ_mode("occ_O_c", "vacancy")   # [0, 1]   (default)
ref.set_occ_mode("occ_O_c", "excess")    # [0, 1.5] (over-occupancy allowed)
```

### Simple vacancy refinement

```python
seq.add_stage("vacancy", "occ_O_c")       # one site
seq.add_stage("all_occ", "occ")           # every occupancy at once
```

## Anti-site swaps

When two sites exchange species (one site gains what the other loses), couple
their occupancies so a single inversion fraction *x* drives all four numbers.
`set_occ_swap` builds the lmfit expressions for you.

```python
set_occ_swap(free, complement=[...], equals=[...])
```

- `free` — the driving parameter, *x* (refined).
- `complement` — partners tied to `1 - x`.
- `equals` — partners tied to `x`.

### 1. Conservative anti-site (1 DOF) — sites stay full *and* total composition conserved

```python
ref.set_occ_swap("occ_S_a",
                 complement=["occ_Br_a", "occ_S_d"],
                 equals=["occ_Br_d"])
# occ_S_a = x, occ_Br_a = 1-x, occ_S_d = 1-x, occ_Br_d = x
seq.add_stage("swap", "occ_S_a")           # free only the driver; partners follow
```

### 2. Non-equilibrium, sites still full (2 DOF) — each site inverts independently

Stoichiometry is *not* conserved across the two sites. Set per-site
complements yourself instead of `set_occ_swap`:

```python
ref.params["occ_Br_a"].set(expr="1 - occ_S_a")   # 4a full
ref.params["occ_Br_d"].set(expr="1 - occ_S_d")   # 4d full
seq.add_stage("antisite", "occ_S_a", "occ_S_d")
```

### 3. Fully unconstrained (4 DOF) — vacancies / off-stoichiometry allowed

```python
for n in ("occ_S_a", "occ_Br_a", "occ_S_d", "occ_Br_d"):
    ref.set_occ_mode(n, "vacancy")
seq.add_stage("free_occ", "occ_S_a", "occ_Br_a", "occ_S_d", "occ_Br_d")
```

A mixed coupling is fine too — e.g. conserve total Br while allowing vacancies
with a custom expression `ref.params["occ_X"].set(expr="0.95 - occ_S_a")`.

## The degeneracy you must manage

PDF intensity scales as `f_eff(i)·f_eff(j)`, so a **uniform rescaling of all
occupancies is degenerate with `scale`**. The conservative swap (case 1) is
rank-1 and removes this degeneracy; relaxing to cases 2–3 reintroduces it and
adds strong occupancy↔ADP correlation. When occupancies are loosely
constrained:

- fix `scale` (or pin one occupancy, or impose a known total composition),
- refine ADPs in a *separate* stage from occupancy,
- prefer the most constrained model your chemistry allows.

## Robust workflow: the Rwp scan

For a single inversion parameter against clean/synthetic data, the
least-squares Jacobian for one occupancy can flatten at the default
finite-difference step and stop early. The robust approach — and a good check
on any optimizer result — is to scan the fraction directly:

```python
import numpy as np
def rwp_at(x):
    for k in range(st.N):
        if len(st.site_occ[k]) > 1:
            st.site_occ[k] = [1 - x, x]      # set both species
    st.refresh_occupancy()
    G = calc.compute_gr()[1]
    return np.sqrt(((G - G_obs)**2).sum() / (G_obs**2).sum()) * 100

xs = np.linspace(0, 0.5, 51)
best = xs[np.argmin([rwp_at(x) for x in xs])]
```

Plug the minimum back in (e.g. `ref.params["occ_S_a"].set(value=best)`), apply,
and save.

## Saving disordered structures

`save_structure` writes refined occupancies back into the CIF (both species of
a mixed site, each with its occupancy). Refined occupancies survive a
save→reload round-trip, and a coupled swap stays self-consistent
(`occ_S + occ_Br = 1` per site).

```python
ref.set_occ_swap("occ_S_a", complement=["occ_Br_a","occ_S_d"], equals=["occ_Br_d"])
ref.params["occ_S_a"].set(value=best)     # or after a swap stage
ref.pm.apply_to_structure(ref.params)      # push values into the structure
ref.save_structure("argyrodite_refined.cif")
```

## Limitations (current version)

- **Shared ADP at a mixed site** — the minority species uses the site's ADP;
  it cannot refine its own.
- **Symmetry mode only** for per-species occupancy. With `use_symmetry=False`
  (P1) the structure is treated atom-by-atom and disordered sites are not split
  into per-species occupancies.
- **Charged / anomalous form factors** use the dominant species' oxidation
  state; a minority species falls back to neutral.
