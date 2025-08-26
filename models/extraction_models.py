from pydantic import BaseModel, Field
from typing import Optional, List

class Entity(BaseModel):
    """ Model for an entity in the extraction task. """
    text: str = Field(..., description="Text of the entity")
    label: Optional[str] = Field(..., description="Label of the entity (e.g., PERSON, ORGANIZATION)")
    start_char: Optional[int] = Field(..., description="Start character index of the entity in the text")
    end_char: Optional[int] = Field(..., description="End character index of the entity in the text")
    id: Optional[str] = Field(None, description="Unique identifier for the existing entity")

class HLCModel(BaseModel):
    """ Model for a high-level concept (HLC) in the extraction task. """
    hlc_id: str = Field(..., description="Unique identifier for the high-level concept")
    # name: str = Field(..., description="Name of the high-level concept")
    text: str = Field(..., description="Text of the high-level concept")
    # description: Optional[str] = Field(None, description="Description of the high-level concept")
    creation_time: Optional[str] = Field(None, description="Creation time of the high-level concept")
    count: Optional[int] = Field(None, description="Count of occurrences of the high-level concept in the text")

class ExtractionModel(BaseModel):
    """ Base model for extraction tasks. """
    extraction_id: str = Field(..., description="Unique identifier for the extraction task")
    text: str = Field(..., description="Text to be processed for extraction")
    creation_time: Optional[str] = Field(None, description="Creation time of the extraction task")
    status: Optional[str] = Field("pending", description="Status of the extraction task, e.g., initial, automatic, manual, pending, processed")

class ExtractionResponseModel(BaseModel):
    """ Response model for extraction tasks. """
    extraction_id: str = Field(..., description="Unique identifier for the extraction task")
    textual_identifier: Optional[str] = Field(None, description="Optional textual identifier for the extraction task")
    source_id: Optional[str] = Field(None, description="Optional source identifier for the extraction task")
    status: str = Field(..., description="Status of the extraction task")
    text: str = Field(..., description="Text that was processed for extraction")
    sentences: Optional[List[HLCModel]] = Field(None, description="List of sentences extracted from the text")

    entities_recommended: Optional[List[Entity]] = Field(None, description="List of entities recommended in extraction")
    relationships: Optional[List[str]] = Field(None, description="List of relationships present in extraction")
    creation_time: Optional[str] = Field(None, description="Creation time of the extraction task")
    entities: Optional[List[Entity]] = Field(None, description="List of entities already existing in the extraction")

class ExtractionCreateModel(BaseModel):
    """ Model for creating a new extraction task. """
    text: str = Field(..., description="Text to be processed for extraction")
    textual_identifier: Optional[str] = Field(None, description="Optional textual identifier for the extraction task")
    source_id: Optional[str] = Field(None, description="Optional source identifier for the extraction task")
