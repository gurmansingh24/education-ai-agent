from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr


class Extraction(BaseModel):
    """The only data shape accepted by downstream application code."""

    model_config = ConfigDict(extra="forbid")

    title: Annotated[
        StrictStr,
        Field(min_length=1, max_length=120),
    ]
    priority: Literal["low", "medium", "high"]
    tags: Annotated[
        list[StrictStr],
        Field(max_length=8),
    ]
    confidence: Annotated[
        float,
        Field(ge=0.0, le=1.0),
    ]
