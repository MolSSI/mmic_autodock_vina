[//]: # (Badges)
[![GitHub Actions Build Status](https://github.com/MolSSI/mmic_autodock_vina/workflows/CI/badge.svg)](https://github.com/MolSSI/mmic_autodock_vina/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/MolSSI/mmic_autodock_vina/branch/master/graph/badge.svg)](https://codecov.io/gh/MolSSI/mmic_autodock_vina/branch/master)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/MolSSI/mmic_autodock_vina.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/MolSSI/mmic_mda/context:python)

<p align="center">
<img src="mmic_autodock_vina/data/imgs/autodock.png">
</p>

# AutoDock Vina Component
This is part of the [MolSSI](http://molssi.org) Molecular Mechanics Interoperable Components ([MMIC](https://github.com/MolSSI/mmic)) project. This package provides molecular docking compute via [AutoDock Vina](http://vina.scripps.edu) program.

## Preparing Input

```python
# Import MM molecule data model
from mmelemental.models.molecule import Molecule

# Construct MM molecules
receptor_data   = Molecule.from_file(pdb_file)
ligand_data     = Molecule.from_data(smiles_code)

# Import docking data model compliant with MMSchema
from mmic_docking.models import DockInput

# Construct docking input data from MMSchema molecules
dock_input = DockInput(
    mol={"ligand": ligand_data, "receptor": receptor_data},
    searchSpace=(xmin, xmax, ymin, ymax, zmin, zmax),
    searchSpace_units="angstrom",
)
```

## Running Docking with AutoDock Vina component

```python
# Import docking simulation component for autodock vina
from mmic_autodock_vina.components.autodock_component import AutoDockComponent

# Run autodock vina
dock_output = AutoDockComponent.compute(dock_input)

# Extract output
affinity, ligands = dock_output.observables.score, dock_output.poses.ligand
```

### Copyright

Copyright (c) 2021, MolSSI


#### Acknowledgements

Project based on the
[Computational Molecular Science Python Cookiecutter](https://github.com/molssi/cookiecutter-cms) version 1.1.
