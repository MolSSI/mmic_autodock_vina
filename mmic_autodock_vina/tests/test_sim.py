from mmelemental.models.molecule import Molecule
from mmic_docking.models.input import DockInput

# Construct docking input
receptor = Molecule.from_file("mmic_autodock_vina/data/PHIPA_C2/PHIPA_C2_apo.pdb")
ligand = Molecule.from_data(
    "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", dtype="smiles"
)  # smiles code for ibuprofen

dockInput = DockInput(mol={"ligand": ligand, "receptor": receptor})

# Import simulation component for autodock vina
from mmic_autodock_vina.components.autodock_component import AutoDockComponent

# Run autodock vina
dockOutput = AutoDockComponent.compute(dockInput)

# Extract output
scores, ligands, flex = (
    dockOutput.observables.score,
    dockOutput.poses.ligand,
    dockOutput.poses.receptor,
)

print("Scores: ")
print("=======")
print(scores)

print("Ligand pose: ")
print("============")
print(ligands)

if flex:
    print("Flexible receptor pose: ")
    print("=======================")
    print(flex)
