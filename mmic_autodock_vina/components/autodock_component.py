from mmic_docking.components import DockComponent
from mmic_autodock_vina.components.autodock_prep_component import AutoDockPrepComponent
from mmic_autodock_vina.components.autodock_compute_component import (
    AutoDockComputeComponent,
)
from mmic_autodock_vina.components.autodock_post_component import AutoDockPostComponent

from typing import Any, Dict, List, Optional, Tuple

__all__ = ["AutoDockComponent"]


class AutoDockComponent(DockComponent):
    def execute(
        self,
        inputs: Dict[str, Any],
        extra_outfiles: Optional[List[str]] = None,
        extra_commands: Optional[List[str]] = None,
        scratch_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Tuple[bool, Dict[str, Any]]:

        compInput = AutoDockPrepComponent.compute(inputs)
        compOutput = AutoDockComputeComponent.compute(compInput)
        dockOutput = AutoDockPostComponent.compute(compOutput)

        return True, dockOutput
