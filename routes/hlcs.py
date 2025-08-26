from fastapi import APIRouter, HTTPException, Request
from data_processor.data_transformer import get_hlc_entities, get_spacy_tokens, get_spacy_entities

router = APIRouter()


@router.get("/hlc/{hlc_id}")
async def get_hlc(request: Request, hlc_id: str):
    """
    Retrieve a specific HLC by its ID.
    """
    # get hlc from db
    driver = request.app.state.driver
    spacy_context = request.app.state.spacy_context

    with driver.session() as session:
        # get HLC node by id and connected MLCs and connected distinct Extraction
        result = session.run(
            "MATCH (hlc:HLC {id: $hlc_id}) "
            "OPTIONAL MATCH (hlc)<-[:HAS_HLC]-(e:Extraction) "
            "OPTIONAL MATCH (hlc)-[:HAS_ENTITY]->(entity:Entity) "
            "OPTIONAL MATCH (hlc)-[r:HAS_CHAIN]->(chain_item) "
            "WITH hlc, collect(DISTINCT e) as extractions, collect(DISTINCT entity) as entities, chain_item, r.order as pos "
            "ORDER BY pos "
            "RETURN hlc, collect({id: chain_item.id, type: head(labels(chain_item)), text: chain_item.text}) as chain, extractions, entities",
            hlc_id=hlc_id
        )
        record = result.single()
                
        if not record:
            raise HTTPException(status_code=404, detail="HLC not found")
        hlc_node = record["hlc"]
        tokens = get_spacy_tokens(spacy_context, hlc_node["text"])
        spacy_entities = get_spacy_entities(spacy_context, hlc_node["text"])
        hlc_entities = get_hlc_entities(session, hlc_node["text"])
            
        # enhance space entities with recommended_by field
        if spacy_entities is None or len(spacy_entities) == 0:
            spacy_entities = []
        else:
            spacy_entities = [{"text": ent[0], "label": ent[1], "start_char": ent[2], "end_char": ent[3], "recommended_by": "spacy"} for ent in spacy_entities]
    
        # hlc_found = [{"text": "University of Applied Sciences and Arts Northwestern Switzerland", "label": "ORGANIZATION", "start_char": 17, "end_char": 80, "recommended_by": "hlc"}]
    
        hlc = {
            "id": hlc_node["id"],
            "creation_time": hlc_node["creation_time"],
            "text": hlc_node["text"],
            "tokens": tokens,
            "recommended_entities": spacy_entities + hlc_entities,
            "relations": [],
            "chain": record["chain"],
            "extractions": record["extractions"],
            "entities": record["entities"]
        }

        return hlc