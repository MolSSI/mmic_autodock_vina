# Import models
from mmic_docking.models import DockInput
from mmelemental.models import Molecule
from mmic_autodock_vina.models import AutoDockComputeInput

# Import components
from mmic.components.blueprints import SpecificComponent
from mmic_util.components import CmdComponent

from mmelemental.util.units import convert
from mmelemental.util.files import random_file
from typing import Any, Dict, Optional, Tuple
import os
import string
import tempfile


class AutoDockPrepComponent(SpecificComponent):
    """ Preprocessing component for autodock """

    @classmethod
    def input(cls):
        return DockInput

    @classmethod
    def output(cls):
        return AutoDockComputeInput

    def execute(
        self, inputs: DockInput, config: Optional["TaskConfig"] = None
    ) -> Tuple[bool, AutoDockComputeInput]:
        binput = self.build_input(inputs, config)
        return True, AutoDockComputeInput(proc_input=inputs, **binput)

    def build_input(
        self, inputs: DockInput, config: Optional["TaskConfig"] = None
    ) -> Dict[str, Any]:
        ligand_pdbqt = self.ligand_prep(
            smiles=inputs.molecule.ligand.identifiers.smiles
        )
        receptor_pdbqt = self.receptor_prep(
            receptor=inputs.molecule.receptor, config=config
        )
        inputDict = self.checkComputeParams(inputs)
        inputDict["ligand"] = ligand_pdbqt
        inputDict["receptor"] = receptor_pdbqt

        return inputDict

    # helper functions
    def receptor_prep(self, receptor: Molecule, config: "TaskConfig" = None) -> str:
        """ Returns a receptor molecule for rigid docking. """
        env = os.environ.copy()

        if config:
            env["MKL_NUM_THREADS"] = str(config.ncores)
            env["OMP_NUM_THREADS"] = str(config.ncores)

        scratch_directory = config.scratch_directory if config else None

        pdb_file = random_file(suffix=".pdb")
        receptor.to_file(pdb_file, mode="w")

        # Assume protein is rigid and ass missing hydrogens
        outfile = random_file(suffix=".pdbqt")
        obabel_input = {
            "command": [
                "obabel",
                pdb_file,
                "-O" + outfile,
                "-xrh",
            ],
            "infiles": None,
            "outfiles": [outfile],
            "scratch_directory": scratch_directory,
            "environment": env,
        }

        obabel_output = CmdComponent.compute(obabel_input)
        final_receptor = obabel_output.outfiles[outfile]
        os.remove(pdb_file)

        return final_receptor

    def ligand_prep(self, smiles: str, config: Optional["TaskConfig"] = None) -> str:
        """ Returns a ligand molecule for rigid docking. """
        env = os.environ.copy()

        if config:
            env["MKL_NUM_THREADS"] = str(config.ncores)
            env["OMP_NUM_THREADS"] = str(config.ncores)

        scratch_directory = config.scratch_directory if config else None

        smi_file = random_file(suffix=".smi")

        with open(smi_file, "w") as fp:
            fp.write(smiles)

        outfile = random_file(suffix=".pdbqt")

        obabel_input = {
            "command": [
                "obabel",
                smi_file,
                "-O" + outfile,
                "--gen3d",
                "-h",
            ],
            "infiles": None,
            "outfiles": [outfile],
            "scratch_directory": scratch_directory,
            "environment": env,
        }
        obabel_output = CmdComponent.compute(obabel_input)
        final_ligand = obabel_output.outfiles[outfile]
        os.remove(smi_file)

        return final_ligand

    def checkComputeParams(self, input_model: DockInput) -> Dict[str, Any]:
        geometry = convert(
            input_model.molecule.receptor.geometry,
            input_model.molecule.receptor.geometry_units,
            "angstrom",
        )
        outputDict = {}
        searchSpace = input_model.searchSpace

        if not searchSpace:
            xmin, xmax = geometry[:, 0].min(), geometry[:, 0].max()
            ymin, ymax = geometry[:, 1].min(), geometry[:, 1].max()
            zmin, zmax = geometry[:, 2].min(), geometry[:, 2].max()
        else:
            xmin, xmax, ymin, ymax, zmin, zmax = convert(
                searchSpace, input_model.searchSpace_units, "angstrom"
            )

        outputDict["center_x"] = (xmin + xmax) / 2.0
        outputDict["size_x"] = xmax - xmin

        outputDict["center_y"] = (ymin + ymax) / 2.0
        outputDict["size_y"] = ymax - ymin

        outputDict["center_z"] = (zmin + zmax) / 2.0
        outputDict["size_z"] = zmax - zmin

        outputDict["out"] = os.path.abspath("autodock.pdbqt")
        outputDict["log"] = os.path.abspath("autodock.log")

        return outputDict
