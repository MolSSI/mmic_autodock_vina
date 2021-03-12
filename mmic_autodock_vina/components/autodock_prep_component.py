# Import models
from mmic_docking.models.input import DockInput
from mmelemental.models.util.input import OpenBabelInput, FileInput
from mmelemental.models.util.output import FileOutput
from mmelemental.models.molecule import Molecule
from mmic_autodock_vina.models.input import AutoDockComputeInput

# Import components
from mmelemental.components.util.openbabel_component import OpenBabelComponent
from mmic.components.blueprints.generic_component import GenericComponent

from typing import Any, Dict, Optional, Tuple
import os
import string
import random


class AutoDockPrepComponent(GenericComponent):
    """ Preprocessing component for autodock """

    @classmethod
    def input(cls):
        return DockInput

    @classmethod
    def output(cls):
        return AutoDockComputeInput

    def execute(
        self, inputs: DockInput, config: "TaskConfig" = None
    ) -> Tuple[bool, AutoDockComputeInput]:
        binput = self.build_input(inputs)
        return True, AutoDockComputeInput(dockInput=inputs, **binput)

    def build_input(
        self, inputs: DockInput, template: Optional[str] = None
    ) -> Dict[str, Any]:
        ligand_pdbqt = self.ligand_prep(smiles=inputs.mol.ligand.identifiers.smiles)
        receptor_pdbqt = self.receptor_prep(receptor=inputs.mol.receptor)
        inputDict = self.checkComputeParams(inputs)
        inputDict["ligand"] = ligand_pdbqt
        inputDict["receptor"] = receptor_pdbqt

        return inputDict

    # helper functions
    def receptor_prep(self, receptor: Molecule) -> str:
        pdb_name = self.randomString() + ".pdb"
        fo = FileOutput(path=os.path.abspath(pdb_name))
        receptor.to_file(fo.path)

        # Assume protein is rigid and ass missing hydrogens
        obabel_input = OpenBabelInput(
            fileInput=FileInput(path=fo.path), outputExt="pdbqt", args=["-xrh"]
        )

        final_receptor = OpenBabelComponent.compute(input_data=obabel_input).stdout
        fo.remove()

        return final_receptor

    def ligand_prep(self, smiles: str) -> str:
        return self.smi_to_pdbqt(smiles)

    def smi_to_pdbqt(self, smiles: str) -> str:
        smi_file = os.path.abspath(self.randomString() + ".smi")

        with open(smi_file, "w") as fp:
            fp.write(smiles)

        obabel_input = OpenBabelInput(
            fileInput=FileInput(path=smi_file),
            outputExt="pdbqt",
            args=["--gen3d", "-h"],
        )
        obabel_output = OpenBabelComponent.compute(input_data=obabel_input)

        os.remove(smi_file)

        return obabel_output.stdout

    def checkComputeParams(self, input_model: DockInput) -> Dict[str, Any]:
        geometry = input_model.mol.receptor.geometry
        outputDict = {}
        searchSpace = input_model.searchSpace

        if not searchSpace:
            xmin, xmax = geometry[:, 0].min(), geometry[:, 0].max()
            ymin, ymax = geometry[:, 1].min(), geometry[:, 1].max()
            zmin, zmax = geometry[:, 2].min(), geometry[:, 2].max()
        else:
            xmin, xmax, ymin, ymax, zmin, zmax = searchSpace

        outputDict["center_x"] = (xmin + xmax) / 2.0
        outputDict["size_x"] = xmax - xmin

        outputDict["center_y"] = (ymin + ymax) / 2.0
        outputDict["size_y"] = ymax - ymin

        outputDict["center_z"] = (zmin + zmax) / 2.0
        outputDict["size_z"] = zmax - zmin

        outputDict["out"] = os.path.abspath("autodock.pdbqt")
        outputDict["log"] = os.path.abspath("autodock.log")

        return outputDict

    @staticmethod
    def randomString(stringLength=10) -> str:
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for i in range(stringLength))
