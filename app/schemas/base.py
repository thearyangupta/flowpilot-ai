from pydantic import BaseModel, ConfigDict


class StrictRequestModel(BaseModel):
    """
    Base class for data received from external callers.

    Unexpected fields are rejected rather than silently ignored.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
