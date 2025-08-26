from pydantic import BaseModel, Field
from typing import Optional, List

class Entity(BaseModel):
    text: str = Field(..., description="Text of the entity")
    textual_identifier: str = Field(..., description="Unique textual identifier for the entity")
    id: Optional[str] = Field(..., description="Unique identifier for the entity")
    creation_time: Optional[str] = Field(None, description="Creation time of the entity")
    from_hlc: Optional[bool] = Field(None, description="Indicates if the entity is directly generated from a high-level concept (HLC)")
    hlc_id: Optional[str] = Field(None, description="Unique identifier for the high-level concept (HLC) associated with the entity")
    mlc_token_ids: Optional[List[str]] = Field(None, description="List of medium-level concept (MLC) token IDs associated with the entity")
    mlc_token_index: Optional[int] = Field(None, description="Index of the first medium-level concept (MLC) token associated with the entity")

class EntityLinkingCreate(BaseModel):
    entity_id: str = Field(..., description="Unique identifier for the entity")
    hlc_id: Optional[str] = Field(None, description="Unique identifier for the high-level concept (HLC) associated with the entity")
    token_ids: Optional[List[str]] = Field(None, description="List of tokens")
    order: Optional[int] = Field(None, description="Order of the entity in the sentence")

class RelationshipCreateModel(BaseModel):
    source_id: str = Field(..., description="Unique identifier for the source node")
    source_type: str = Field(..., description="Type of the source node")
    target_id: Optional[str] = Field(..., description="Unique identifier for the target node")
    target_type: str = Field(..., description="Type of the target node")
    relationship_type: str = Field(..., description="Type of the relationship between the source and target entities")
    target_text: Optional[str] = Field(None, description="Text of the target entity")