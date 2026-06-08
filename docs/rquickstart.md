# Quick Start

A complete small-box refinement in one script: load a CIF, preview the model
G(r), fit it to measured data, and save the result.

```python
import sys
sys.path.append(r'C:\pdf_rabbit_fit')

from structure  import PDFStructure
from calculator import PDFCalculator
from refiner    import PDFRefiner, SequentialRefiner
import matplotlib.pyplot as plt

cif_path = r"CeO2.cif"
Gr_path  = "../pdf_fittig/Gr_final.dat"      # measured G(r), two columns: r  G(r)

# 1. Structure
structure = PDFStructure(cif_path, use_symmetry=True)
structure.initial_structure()                # lattice, sites, occupancies, ADPs
structure.degrees_of_freedom()               # symmetry-allowed refinable params

# 2. Model G(r)
pdf_calculator = PDFCalculator(structure, rmin=1, rmax=24.3, biso=0.3)
plt.plot(pdf_calculator.r, pdf_calculator.pdf)   # preview before fitting

# 3. Refine
refiner = PDFRefiner(pdf_calculator, Gr_path)
refiner.set_regularization('barrier', weight=0.1)
refiner.show_parameters()

seq = SequentialRefiner(refiner)
seq.add_stage('all', max_iter=int(1e7))      # free everything except occupancy
seq.run()

# 4. Output
seq.plot()
seq.save_structure("CeO2_refined.cif")
seq.save_summary("CeO2_summary.json")
```
