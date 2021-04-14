# Import models
from mmic_autodock_vina.models.output import AutoDockComputeOutput
from mmic_docking.models.output import DockOutput
from mmelemental.models.util.input import FileInput
from mmelemental.models.util.output import FileOutput
from mmelemental.models.molecule import Molecule

# Import components
from mmic.components.blueprints import SpecificComponent
from mmic_util.components import CmdComponent

from mmelemental.util.files import random_file
from typing import Any, Dict, List, Optional, Tuple, Union
import os


class AutoDockPostComponent(SpecificComponent):
    """ Postprocessing autodock component. """

    @classmethod
    def input(cls):
        return AutoDockComputeOutput

    @classmethod
    def output(cls):
        return DockOutput

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
        if execute_input.get("infiles"):
            self.clean(execute_input.get("infiles"))
        return out

    def build_input(
        self,
        input_model: AutoDockComputeOutput,
        config: "TaskConfig" = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """ Builds input files for autodock vina_split. """

        system = input_model.system

        fsystem = FileOutput(path=random_file(suffix=".pdbqt"))
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
    ) -> DockOutput:
        """ Parses output from vina_split. """

        ligands = self.read_files(files=outputs.outfiles["ligand*"])
        flex = self.read_files(files=outputs.outfiles.get("flex*"))

        scores = self.get_scores(inputs.stdout)

        return DockOutput(
            proc_input=inputs.proc_input,
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
                ligand_file = random_file(suffix=".pdb")
                with FileOutput(path=os.path.abspath(fname), clean=True) as pdbqt:

                    pdbqt.write(files[fname])
                    obabel_input = obabel_input_lambda(pdbqt.path, ligand_file)

                    ligand_pdb = CmdComponent.compute(input_data=obabel_input).outfiles[
                        ligand_file
                    ]
                    with FileOutput(path=ligand_file, clean=True) as pdb:
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

    def clean(self, files: List[str]):
        for file in files:
            os.remove(file)
