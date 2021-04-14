"""
Unit and regression test for the mmic_autodock_vina package.
"""

# Import package, test suite, and other packages as needed
import mmic_autodock_vina
from mmelemental.models.molecule import Molecule
from mmic_docking.models.input import DockInput
import pytest
import sys


def test_mmic_autodock_vina_imported():
    """Sample test, will always pass so long as import statement worked"""
    assert "mmic_autodock_vina" in sys.modules


def test_mmic_autodock_vina_run():
    """ Test all the components via a docking compute. """
    # Construct docking input
    receptor = Molecule.from_file("mmic_autodock_vina/data/PHIPA_C2/PHIPA_C2_apo.pdb")
    ligand = Molecule.from_data(
        "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", dtype="smiles"
    )  # smiles code for ibuprofen

    searchSpace = [-37.807, 5.045, -2.001, 30.131, -19.633, 37.987]

    dockInput = DockInput(
        molecule={"ligand": ligand, "receptor": receptor},
        searchSpace=searchSpace,
        searchSpace_units="angstrom",
    )

    # Import simulation component for autodock vina
    from mmic_autodock_vina.components.autodock_component import AutoDockComponent

    # Run autodock vina
    dockOutput = AutoDockComponent.compute(dockInput)

    # Extract output
    scores, ligands, flex = (
        dockOutput.scores,
        dockOutput.poses.ligand,
        dockOutput.poses.receptor,
    )

    assert len(scores) == len(ligands)
    assert isinstance(scores, list)
    # add more assertions here
