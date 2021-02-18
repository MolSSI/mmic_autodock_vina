# Import models
from mmic_autodock.models.output import AutoDockComputeOutput
from mmelemental.models.app.docking import DockOutput
from mmelemental.models.util.input import OpenBabelInput, FileInput
from mmelemental.models.util.output import FileOutput
from mmelemental.models.molecule import Molecule
from mmelemental.models.util.output import CmdOutput

# Import components
from mmelemental.components.util.openbabel_component import OpenBabelComponent
from mmelemental.components.util.cmd_component import CmdComponent

from typing import Any, Dict, List, Optional
import os


class AutoDockPostComponent(CmdComponent):
    """ Postprocessing autodock component. """

    @classmethod
    def input(cls):
        return AutoDockComputeOutput

    @classmethod
    def output(cls):
        return DockOutput

    def build_input(
        self,
        input_model: AutoDockComputeOutput,
        config: "TaskConfig" = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """ Builds input files for autodock vina_split. """

        system = input_model.system

        fsystem = FileOutput(path=os.path.abspath("system.pdbqt"))
        fsystem.write(system)

        cmd = [
            "vina_split",
            "--input",
            fsystem.path,
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
            "infiles": None,
            "outfiles": ["ligand*", "flex*"],
            "scratch_directory": scratch_directory,
            "environment": env,
            "clean_files": fsystem,
        }

    def parse_output(
        self, outfiles: Dict[str, Dict[str, str]], input_model: AutoDockComputeOutput
    ) -> DockOutput:
        """ Parses output from vina_split. """

        ligands = self.read_files(files=outfiles["outfiles"]["ligand*"])
        flex = self.read_files(files=outfiles["outfiles"]["flex*"])

        cmdout = input_model.cmdout
        scores = self.get_scores(cmdout)
        return DockOutput(
            dockInput=input_model.dockInput,
            ligands=ligands,
            receptors=flex, # should we reconstruct the whole receptor?
            scores=scores,
        )

    def read_files(self, files: List[str]) -> List[Molecule]:

        mols = []

        if files is not None:
            for fname in files:
                with FileOutput(path=os.path.abspath(fname), clean=True) as pdbqt:
                    pdbqt.write(files[fname])

                    obabel_input = OpenBabelInput(
                        fileInput=FileInput(path=pdbqt.path), outputExt="pdb"
                    )

                    ligand_pdb = OpenBabelComponent.compute(
                        input_data=obabel_input
                    ).stdout
                    with FileOutput(
                        path=os.path.abspath("ligand.pdb"), clean=True
                    ) as pdb:
                        pdb.write(ligand_pdb)
                        mols.append(Molecule.from_file(pdb.path))

        return mols

    def get_scores(self, cmdout: CmdOutput) -> List[float]:
        """
        Extracts scores from autodock vina command-line output.
        .. todo:: Extract and return RMSD values.
        """
        read_scores = False
        scores = []

        for line in cmdout.stdout.split("\n"):
            if line == "-----+------------+----------+----------":
                read_scores = True
                continue
            elif "Writing output" in line:
                break
            if read_scores:
                trial, score, _, _ = line.split()
                scores.append(float(score))

        return scores
