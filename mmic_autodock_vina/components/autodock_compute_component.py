from typing import Any, Dict, List, Optional, Tuple
from mmic.components.blueprints import SpecificComponent
from mmic_autodock_vina.models.input import AutoDockComputeInput
from mmic_autodock_vina.models.output import AutoDockComputeOutput
from mmelemental.models.util.input import FileInput

from mmic_util.models import CmdInput
from mmic_util.components import CmdComponent
from mmelemental.util.files import random_file
import os


class AutoDockComputeComponent(SpecificComponent):
    @classmethod
    def input(cls):
        return AutoDockComputeInput

    @classmethod
    def output(cls):
        return AutoDockComputeOutput

    def execute(
        self,
        inputs: Dict[str, Any],
        extra_outfiles: Optional[List[str]] = None,
        extra_commands: Optional[List[str]] = None,
        scratch_name: Optional[str] = None,
        timeout: Optional[int] = None,
        config: Optional["TaskConfig"] = None,
    ) -> Tuple[bool, Dict[str, Any]]:

        receptor, ligand = inputs.receptor, inputs.ligand
        receptor_fname = random_file(suffix=".pdbqt")
        ligand_fname = random_file(suffix=".pdbqt")

        with open(receptor_fname, "w") as fp:
            fp.write(receptor)

        with open(ligand_fname, "w") as fp:
            fp.write(ligand)

        input_model = inputs.dict()
        del input_model["proc_input"]

        input_model["receptor"] = receptor_fname
        input_model["ligand"] = ligand_fname
        # need to include flex too
        input_model["out"] = random_file(suffix=".pdbqt")
        input_model["log"] = random_file(suffix=".log")

        execute_input = self.build_input(input_model, config)
        execute_output = CmdComponent.compute(execute_input)
        output = True, self.parse_output(execute_output.dict(), inputs)
        self.cleanup(input_model)
        return output

    def cleanup(self, files):
        for file in files:
            if os.path.isfile(file):
                os.remove(file)

    def build_input(
        self,
        input_model: Dict[str, Any],
        config: Optional["TaskConfig"] = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:

        cmd = ["vina"]

        for key, val in input_model.items():
            if val and key != "provenance":
                cmd.append("--" + key)
                if isinstance(val, str):
                    cmd.append(val)
                else:
                    cmd.append(str(val))

        env = os.environ.copy()

        if config:
            env["MKL_NUM_THREADS"] = str(config.ncores)
            env["OMP_NUM_THREADS"] = str(config.ncores)

        scratch_directory = config.scratch_directory if config else None

        return {
            "command": cmd,
            "infiles": [input_model["ligand"], input_model["receptor"]],
            "outfiles": [
                input_model["out"],
                input_model["log"],
            ],
            "scratch_directory": scratch_directory,
            "environment": env,
        }

    def parse_output(
        self, output: Dict[str, Any], input_model: AutoDockComputeInput
    ) -> AutoDockComputeOutput:
        stdout = output["stdout"]
        stderr = output["stderr"]
        outfiles = output["outfiles"]

        if stderr:
            print("Error from AutoDock Vina:")
            print("=========================")
            print(stderr)

        system, log = outfiles

        return AutoDockComputeOutput(
            stdout=stdout,
            stderr=stderr,
            log=FileInput(path=log).read(),
            system=FileInput(path=system).read(),
            proc_input=input_model.proc_input,
        )
