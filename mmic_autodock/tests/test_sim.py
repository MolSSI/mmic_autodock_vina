from mmelemental.models.molecule import Molecule
from mmelemental.models.app.docking import DockInput

# Construct docking input
receptor = Molecule.from_file("mmic_autodock/data/PHIPA_C2/PHIPA_C2_apo.pdb")
ligand = Molecule.from_data(
    "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", dtype="smiles"
)  # smiles code for ibuprofen

dockInput = DockInput(ligand=ligand, receptor=receptor)

# Import simulation component for autodock vina
from mmic_autodock.components.autodock_component import AutoDockComponent

# Run autodock vina
dockOutput = AutoDockComponent.compute(dockInput)

# Extract output
scores, ligands, flex = dockOutput.scores, dockOutput.ligands, dockOutput.flexible

print("Scores: ")
print("========")
print(scores)

print("Ligand pose: ")
print("========")
print(ligands)

if flex:
    print("Flexible receptor pose: ")
    print("========")
    print(flex)
