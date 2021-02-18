# Import models
from mmelemental.models.app.docking import DockInput
from mmelemental.models.util.input import OpenBabelInput, FileInput
from mmelemental.models.util.output import FileOutput
from mmelemental.models.molecule import Molecule
from mmic_autodock.models.input import AutoDockComputeInput

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
        ligand_pdbqt = self.ligand_prep(smiles=inputs.ligand.identifiers.smiles)
        receptor_pdbqt = self.receptor_prep(receptor=inputs.receptor)
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
        receptor = input_model.receptor
        outputDict = {}
        inputDict = input_model.dict()

        if not (inputDict.get("center_x") and inputDict.get("size_x")):
            xmin, xmax = receptor.geometry[:, 0].min(), receptor.geometry[:, 0].max()
            outputDict["center_x"] = (xmin + xmax) / 2.0
            outputDict["size_x"] = xmax - xmin

        if not (inputDict.get("center_y") and inputDict.get("size_y")):
            ymin, ymax = receptor.geometry[:, 1].min(), receptor.geometry[:, 1].max()
            outputDict["center_y"] = (ymin + ymax) / 2.0
            outputDict["size_y"] = ymax - ymin

        if not (inputDict.get("center_z") and inputDict.get("size_z")):
            zmin, zmax = receptor.geometry[:, 2].min(), receptor.geometry[:, 2].max()
            outputDict["center_z"] = (zmin + zmax) / 2.0
            outputDict["size_z"] = zmax - zmin

        outputDict["out"] = os.path.abspath("autodock.pdbqt")
        outputDict["log"] = os.path.abspath("autodock.log")

        return outputDict

    @staticmethod
    def randomString(stringLength=10) -> str:
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for i in range(stringLength))
