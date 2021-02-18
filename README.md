# AutoDock Vina Component
## Preparing Input

```python
# Import MM molecule data model
from mmelemental.models.molecule import Molecule

# Construct MM molecules
receptor_data   = Molecule.from_file(pdb_file)
ligand_data     = Molecule.from_data(smiles_code)

# Import docking data model compliant with MMSchema
from mmelemental.models.app.docking import DockInput

# Construct docking input data from MMSchema molecules
dock_input = DockInput(
	ligand=ligand_data, 
	receptor=receptor_data,
	searchSpace=(xmin, xmax, ymin, ymax, zmin, zmax)
)

```

## Running Docking with AutoDock Vina component

<p align="center">
<img src="mmic_autodock/data/imgs/autodock.png">
</p>

```python
# Import docking simulation component for autodock vina
from mmic_autodock.components.autodock_component import AutoDockComponent

# Run autodock vina
dock_output = AutoDockComponent.compute(dock_input)

# Extract output
affinity, ligands = dock_output.scores, dock_output.ligands
```

### Copyright

Copyright (c) 2021, MolSSI


#### Acknowledgements

Project based on the
[Computational Molecular Science Python Cookiecutter](https://github.com/molssi/cookiecutter-cms) version 1.1.
