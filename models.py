from sqlmodel import Field, SQLModel
import datetime


class Elevator(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    max_floor: int = Field(default=10)
    min_floor: int = Field(default=0)
    current_floor: int = Field(default=0)
    next_stop: int | None = Field(default=0)
    motion_status: str = Field(default="still")
    # min_floor <= current_floor <= max_floor
    # motion_status = "still" | "ascending" | "descending"

class Floor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    floor: int = Field(default=None)
    elevator_id: int = Field(default=None, foreign_key="elevator.id")
    is_demanded: bool = Field(default=False)

class Demand(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    elevator_id: int = Field(default=None, foreign_key="elevator.id")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    source: str = Field(default=None)
    target_floor: int = Field(default=None)

    # source = "inside" | "outside"
    # elevator_id must exist
    # elevator.min_floor <= target_floor <= elevator.max_floor



