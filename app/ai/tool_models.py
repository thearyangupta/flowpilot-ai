from pydantic import BaseModel, Field


class LookupOrderArgs(BaseModel):
    order_id: str = Field(pattern=r"^ORD-[0-9]{6}$")