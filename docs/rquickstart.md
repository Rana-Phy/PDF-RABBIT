# Quick Start

A complete small-box refinement: load a CIF, preview the model G(r), set up a
staged fit, apply bounds, and save the result.

## 1. Setup

```python
import sys
sys.path.append(r'C:\pdf_rabbit_fit')

from structure  import PDFStructure
from calculator import PDFCalculator
from refiner    import PDFRefiner, SequentialRefiner
import matplotlib.pyplot as plt

cif_path = r"CeO2.cif"
Gr_path  = "../pdf_fittig/Gr_final.dat"      # measured G(r): two columns r  G(r)

structure = PDFStructure(cif_path, use_symmetry=True)
structure.initial_structure()
structure.degrees_of_freedom()

pdf_calculator = PDFCalculator(structure, rmin=1, rmax=24.3, biso=0.3)
plt.plot(pdf_calculator.r, pdf_calculator.pdf)   # preview before fitting

refiner = PDFRefiner(pdf_calculator, Gr_path)
refiner.set_regularization('barrier', weight=0.1)
refiner.show_parameters()
```

## 2. Staged refinement

```python
seq = SequentialRefiner(refiner)
seq.add_stage('scale',)
seq.add_stage('scale', 'qbroad', 'qdamp')
seq.add_stage('scale', 'qbroad', 'qdamp', 'delta1', 'delta2')
seq.add_stage('scale', 'qbroad', 'qdamp', 'delta1', 'delta2', 'adp')
seq.add_stage('scale', 'lattice', 'qbroad', 'qdamp', 'delta1', 'delta2', 'adp', 'cbroad')
seq.add_stage('all', max_iter=10e6)
```

## 3. Bounds

```python
refiner.set_bounds('a', 5.40, 5.42)          # lattice parameter window
refiner.set_bounds('qdamp', 0.0, 0.1)
refiner.set_bounds('Uiso_Ce_a', 0.0, 0.05)
refiner.set_bounds('Uiso_O_c', 0.0, 0.05)
refiner.set_bounds('zero_shift', 0.0, 0.0)   # equal bounds fix a parameter
```

## 4. Run and save

```python
seq.run()
seq.plot()
seq.save_structure("CeO2_refined.cif")
seq.save_summary("CeO2_summary.json")
```
