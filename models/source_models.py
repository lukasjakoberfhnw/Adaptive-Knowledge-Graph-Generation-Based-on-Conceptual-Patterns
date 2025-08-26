from pydantic import BaseModel, Field
from typing import Optional, List

class Source(BaseModel):
    """ Model for a source. """
    id: str = Field(..., description="Id of the source")
    name: str = Field(..., description="Name of the source")
    description: Optional[str] = Field(None, description="Description of the source")
    creation_time: Optional[str] = Field(None, description="Creation time of the source")
