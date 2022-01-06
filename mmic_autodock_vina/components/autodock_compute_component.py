from typing import Any, Dict, List, Optional, Tuple
from mmic.components.blueprints import GenericComponent
from mmic_autodock_vina.models.input import AutoDockComputeInput
from mmic_autodock_vina.models.output import AutoDockComputeOutput
from mmic_cmd.components import CmdComponent
from cmselemental.util.decorators import classproperty
import tempfile

import os


class AutoDockComputeComponent(GenericComponent):
    @classproperty
    def input(cls):
        return AutoDockComputeInput

    @classproperty
    def output(cls):
        return AutoDockComputeOutput

    @classproperty
    def version(cls):
        return ""

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
        receptor_fname = tempfile.NamedTemporaryFile(suffix=".pdbqt").name
        ligand_fname = tempfile.NamedTemporaryFile(suffix=".pdbqt").name

        with open(receptor_fname, "w") as fp:
            fp.write(receptor)

        with open(ligand_fname, "w") as fp:
            fp.write(ligand)

        input_model = inputs.dict()
        del input_model["proc_input"]

        input_model["receptor"] = receptor_fname
        input_model["ligand"] = ligand_fname
        # need to include flex too
        input_model["out"] = tempfile.NamedTemporaryFile(suffix=".pdbqt").name
        input_model["log"] = tempfile.NamedTemporaryFile(suffix=".log").name

        execute_input = self.build_input(input_model, config)
        execute_output = CmdComponent.compute(execute_input)
        input_model["proc_input"] = inputs.proc_input
        output = True, self.parse_output(execute_output.dict(), input_model)
        return output

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
            "raise_err": True,
        }

    def parse_output(
        self, output: Dict[str, Any], inputs: AutoDockComputeInput
    ) -> AutoDockComputeOutput:
        stdout = output["stdout"]
        stderr = output["stderr"]
        outfiles = output["outfiles"]
        system = outfiles[inputs["out"]]
        log = outfiles[inputs["log"]]

        return AutoDockComputeOutput(
            schema_name="mmschema",
            schema_version=1,
            success=True,
            stdout=stdout,
            stderr=stderr,
            log=log,
            system=system,
            proc_input=inputs["proc_input"],
        )
