# Import models
from mmic_autodock_vina.models.output import AutoDockComputeOutput
from mmic_docking.models.output import OutputDock
from mmelemental.models.util import FileInput, FileOutput
from mmelemental.models import Molecule
from cmselemental.util.decorators import classproperty

# Import components
from mmic.components.blueprints import GenericComponent
from mmic_cmd.components import CmdComponent

from typing import Any, Dict, List, Optional, Tuple, Union
import os
import tempfile


class AutoDockPostComponent(GenericComponent):
    """Postprocessing autodock component."""

    @classproperty
    def input(cls):
        return AutoDockComputeOutput

    @classproperty
    def output(cls):
        return OutputDock

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
    ) -> Tuple[bool, Dict[str, Any]]:

        execute_input = self.build_input(inputs)
        execute_output = CmdComponent.compute(execute_input)

        out = True, self.parse_output(execute_output, inputs)
        return out

    def build_input(
        self,
        input_model: AutoDockComputeOutput,
        config: "TaskConfig" = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Builds input files for autodock vina_split."""

        system = input_model.system

        fsystem = FileOutput(path=tempfile.NamedTemporaryFile(suffix=".pdbqt").name)
        fsystem.write(system)

        cmd = [
            "vina_split",
            "--input",
            fsystem.abs_path,
            "--ligand",
            "ligand",
            "--flex",
            "flex",
        ]
        env = os.environ.copy()

        if config:
            env["MKL_NUM_THREADS"] = str(config.ncores)
            env["OMP_NUM_THREADS"] = str(config.ncores)

        scratch_directory = config.scratch_directory if config else None

        return {
            "command": cmd,
            "infiles": [fsystem.abs_path],
            "outfiles": ["ligand*", "flex*"]
            if hasattr(input_model.proc_input, "flex")
            else ["ligand*"],
            "scratch_directory": scratch_directory,
            "environment": env,
        }

    def parse_output(
        self, outputs: Dict[str, Any], inputs: AutoDockComputeOutput
    ) -> OutputDock:
        """Parses output from vina_split."""

        ligands = self.read_files(files=outputs.outfiles["ligand*"])
        flex = self.read_files(files=outputs.outfiles.get("flex*"))

        scores = self.get_scores(inputs.stdout)

        return OutputDock(
            proc_input=inputs.proc_input,
            schema_name=inputs.proc_input.schema_name,
            schema_version=inputs.proc_input.schema_version,
            success=True,
            poses={
                "ligand": ligands,
                "receptor": flex,
            },  # should we reconstruct the whole receptor?
            scores=scores,
            scores_units="kcal/mol",
        )

    def read_files(
        self, files: List[str], config: Optional["TaskConfig"] = None
    ) -> List[Molecule]:

        env = os.environ.copy()

        if config:
            env["MKL_NUM_THREADS"] = str(config.ncores)
            env["OMP_NUM_THREADS"] = str(config.ncores)

        scratch_directory = config.scratch_directory if config else None

        mols = []

        obabel_input_lambda = lambda ifile, ofile: {
            "command": [
                "obabel",
                ifile,
                "-O" + ofile,
            ],
            "infiles": [ifile],
            "outfiles": [ofile],
            "scratch_directory": scratch_directory,
            "environment": env,
        }

        if files is not None:
            for fname in files:
                ligand_file = tempfile.NamedTemporaryFile(suffix=".pdb")
                with FileOutput(path=os.path.abspath(fname), clean=True) as pdbqt:

                    pdbqt.write(files[fname])
                    obabel_input = obabel_input_lambda(pdbqt.path, ligand_file.name)

                    ligand_pdb = CmdComponent.compute(input_data=obabel_input).outfiles[
                        ligand_file.name
                    ]
                    with FileOutput(path=ligand_file.name, clean=False) as pdb:
                        pdb.write(ligand_pdb)
                        mols.append(Molecule.from_file(pdb.path))

        return mols

    def get_scores(self, stdout: str) -> List[float]:
        """
        Extracts scores from autodock vina command-line output.
        .. todo:: Extract and return RMSD values.
        """
        read_scores = False
        scores = []

        for line in stdout.split("\n"):
            if line == "-----+------------+----------+----------":
                read_scores = True
                continue
            elif "Writing output" in line:
                break
            if read_scores:
                trial, score, _, _ = line.split()
                scores.append(float(score))

        return scores
