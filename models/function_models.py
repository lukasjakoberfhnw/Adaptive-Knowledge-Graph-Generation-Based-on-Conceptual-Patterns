# , mlc_ids: list[str], hlc_id: str = None
from pydantic import BaseModel

class RecommendedEntityFetch(BaseModel):
    mlc_ids: list[str]
    hlc_id: str = None
