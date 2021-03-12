from mmic_docking.components import DockComponent
from mmic_autodock_vina.components.autodock_prep_component import AutoDockPrepComponent
from mmic_autodock_vina.components.autodock_compute_component import (
    AutoDockComputeComponent,
)
from mmic_autodock_vina.components.autodock_post_component import AutoDockPostComponent

from typing import Any, Dict, List, Optional, Tuple


class AutoDockComponent(DockComponent):
    def execute(
        self,
        inputs: Dict[str, Any],
        extra_outfiles: Optional[List[str]] = None,
        extra_commands: Optional[List[str]] = None,
        scratch_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Tuple[bool, Dict[str, Any]]:

        compInput = AutoDockPrepComponent.compute(input_data=inputs)
        compOutput = AutoDockComputeComponent.compute(input_data=compInput)
        dockOutput = AutoDockPostComponent.compute(input_data=compOutput)

        return True, dockOutput
