from typing import Optional
from mmelemental.models.base import Base
from mmelemental.models.app.docking import DockInput
from pydantic import Field, validator

__all__ = ["AutoDockComputeInput"]

class AutoDockInput(DockInput):
    @validator("mol")
    def valid_mol(cls, v):
        assert(v.get("ligand"))
        assert(v.get("receptor"))
        assert(len(v) == 2)
        return v

class AutoDockComputeInput(Base):
    dockInput: DockInput = Field(..., description="Docking input model.")
    ligand: str = Field(..., description="Ligand file string.")
    receptor: str = Field(..., description="Receptor file string.")
    cpu: Optional[int] = Field(
        1,
        description="The number of CPUs to use. The default is to try to "
        "detect the number of CPUs.",
    )
    out: Optional[str] = Field(None, description="Output models.")
    log: Optional[str] = Field(None, description="Log file output.")
    exhaustiveness: Optional[int] = Field(
        8,
        description="Exhaustiveness of the global search (roughly proportional to time)",
    )
    seed: Optional[int] = Field(None, description="Random seed.")
    center_x: Optional[float] = Field(
        None, description="X coordinate of the search box center."
    )
    center_y: Optional[float] = Field(
        None, description="Y coordinate of the search box center."
    )
    center_z: Optional[float] = Field(
        None, description="Z coordinate of the search box center."
    )
    size_x: Optional[float] = Field(
        None, description="Search box size in the X dimension (Angstroms)."
    )
    size_y: Optional[float] = Field(
        None, description="Search box size in the Y dimension (Angstroms)."
    )
    size_z: Optional[float] = Field(
        None, description="Search box size in the Z dimension (Angstroms)."
    )
    num_modes: Optional[int] = Field(
        9, description="Maximum number of binding modes to generate."
    )
    energy_range: Optional[int] = Field(
        3,
        description="Maximum energy difference between the best binding mode "
        "and the worst one displayed (kcal/mol).",
    )