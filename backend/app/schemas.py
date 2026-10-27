from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Category = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]
FiniteNumber = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class TrafficRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dur: FiniteNumber
    proto: Category
    service: Category
    sbytes: FiniteNumber
    dbytes: FiniteNumber
    spkts: FiniteNumber
    dpkts: FiniteNumber
    sttl: FiniteNumber
    dttl: FiniteNumber
    ct_srv_src: FiniteNumber


class BatchRequest(BaseModel):
    records: list[dict]
