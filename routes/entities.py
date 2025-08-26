from datetime import datetime
import uuid
from fastapi import APIRouter, HTTPException, Request
from models.entity_models import Entity as EntityModelForGeneration, EntityLinkingCreate

router = APIRouter()

@router.post("/entities")
async def create_entity(request: Request, entity: EntityModelForGeneration):
    """
    Create a new entity.
    """
    # create new unique id for entity
    entity_id = str(uuid.uuid4())
    # get current time
    creation_time = datetime.now().isoformat()
    driver = request.app.state.driver

    # if from hlc
    # -> remove old relationships to MLCs
    # -> create new relationships to MLCs and Entity
    # -> create relationship between Entity and HLC
    # -> create relationship between Entity and Extraction of HLC
    if entity.from_hlc:
        if(entity.hlc_id == None):
            raise HTTPException(status_code=400, detail="HLC ID is required for entity creation from HLC")
        with driver.session() as session:
            # just add entity to HLC and Extraction
            session.run(
                "MERGE (hlc:HLC {id: $hlc_id}) "  # Ensure HLC exists
                "MERGE (e:Extraction)-[:HAS_HLC]->(hlc) "  # Ensure Extraction exists
                "MERGE (entity:Entity {id: $entity_id}) "
                "SET entity.text = $text, entity.textual_identifier = $textual_identifier, entity.creation_time = $creation_time "
                "MERGE (e)-[:HAS_ENTITY]->(entity) "
                "MERGE (hlc)-[:HAS_ENTITY]->(entity)"
                "MERGE (hlc)-[:HAS_CHAIN {order: $order}]->(entity)",
                hlc_id=entity.hlc_id,
                entity_id=entity_id,
                text=entity.text,
                textual_identifier=entity.textual_identifier,
                creation_time=creation_time,
                order=entity.mlc_token_index if entity.mlc_token_index is not None else 0
            )

        # if entity has MLC token IDs, create relationships to MLCs
        if entity.mlc_token_ids:
            for mlc_id in entity.mlc_token_ids:
                with driver.session() as session:
                    session.run(
                        "MATCH (entity:Entity {id: $entity_id}) "
                        "MATCH (mlc:MLC {id: $mlc_id}) "
                        "MERGE (entity)-[:COMBINATION_OF]->(mlc)",
                        entity_id=entity_id,
                        mlc_id=mlc_id
                    )

        print("[FROM-HLC-VIEW] Entity created from HLC with ID:", entity_id)
    else:
        # if not from hlc, just create entity
        with driver.session() as session:
            session.run(
                "CREATE (entity:Entity {id: $entity_id, text: $text, textual_identifier: $textual_identifier, creation_time: $creation_time})",
                entity_id=entity_id,
                text=entity.text,
                textual_identifier=entity.textual_identifier,
                creation_time=creation_time
            )
        print("Entity created with ID:", entity_id)

    return {"id": entity_id, "text": entity.text, "textual_identifier": entity.textual_identifier, "creation_time": creation_time}

@router.get("/entities/{entity_id}")
async def get_entity(request: Request, entity_id: str):
    """
    Retrieve a specific entity by its ID.
    """
    driver = request.app.state.driver
    with driver.session() as session:
        # get Entity node by id and connected MLCs and connected HLCs

        # use this:
        # MATCH (n:Entity {id: $entity.id})-[r]-(x)
        # WHERE TYPE(r) <> 'HAS_CHAIN'
        # RETURN n, 
        # COLLECT({rel: r, neighbor: x}) AS relationships_with_neighbors,
        # COLLECT({rel_type: TYPE(r), neighbor: x.id, node_type: LABELS(x)[0], text: substring(x.text, 0, 150)}) AS simplified_connections

        result = session.run(
            "MATCH (entity:Entity {id: $entity_id})-[r]-(x) "
            "WHERE TYPE(r) <> 'HAS_CHAIN' "
            "RETURN entity AS entity, "
            "COLLECT({rel: r, neighbor: x}) AS relationships_with_neighbors, "
            "COLLECT({rel_type: TYPE(r), neighbor: x.id, node_type: LABELS(x)[0], text: substring(x.text, 0, 150)}) AS simplified_connections",
            entity_id=entity_id
        )
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        entity_node = record["entity"]
        neighbours = record["relationships_with_neighbors"]
        simplified_connections = record["simplified_connections"]
        properties = record["entity"]["properties"]

        entity = {
            "id": entity_node["id"],
            "text": entity_node["text"],
            "textual_identifier": entity_node["textual_identifier"],
            "creation_time": entity_node["creation_time"],
            "properties": entity_node,
            "neighbours": neighbours,
            "simplified_connections": simplified_connections
        }
        return entity
    
@router.get("/entities-from-mlcs/{mlc_ids}")
async def get_entities_from_mlcs(request: Request, mlc_ids: str):
    """
    Retrieve entities from MLCs by their IDs.
    """
    mlc_ids_list = mlc_ids.split(",")
    if not mlc_ids_list:
        raise HTTPException(status_code=400, detail="No MLC IDs provided")

    driver = request.app.state.driver
    with driver.session() as session:
        # lowered_mlcs = [mlc.lower() for mlc in mlc_ids_list]
        mlc_ids = [mlc for mlc in mlc_ids_list]

        result = session.run(
            """
                MATCH(e:Entity)-[:HAS_ENTITY]-(ext)
                MATCH(mlc)-[:HAS_CHAIN]-(ext)
                WHERE mlc.id IN $mlc_ids
                WITH e, collect(DISTINCT mlc.id) as mlcs, count(DISTINCT mlc.id) as frequency
                RETURN e, mlcs, frequency
                ORDER BY frequency DESC
                UNION
                MATCH (mlc:MLC)-[:COMBINATION_OF]-(entity:Entity)
                WHERE mlc.id IN $mlc_ids
                WITH entity, collect(mlc.id) as mlcs, count(mlc.id) as frequency
                RETURN entity as e, mlcs, frequency
            """,
            mlc_ids=mlc_ids
        )

        entities = []
        for record in result:
            entity_node = record["e"]
            if entity_node:
                entities.append({
                    "id": entity_node["id"],
                    "text": entity_node["text"],
                    "textual_identifier": entity_node["textual_identifier"],
                    "creation_time": entity_node["creation_time"],
                    "mlc_ids": record["mlcs"],
                    "frequency": record["frequency"],
                    # "origin": entity["origin"],
                })
        print(result)
        
        return entities
    
@router.post("/link-entity")
async def link_entity(request: Request, entitylinking: EntityLinkingCreate):
    """
    Link an entity to an HLC.
    """
    if not entitylinking.entity_id or not entitylinking.hlc_id:
        raise HTTPException(status_code=400, detail="Entity ID and HLC ID are required")

    driver = request.app.state.driver
    with driver.session() as session:
        # create relationship between Entity and HLC, between Entity and Extraction of HLC, and between Entity and MLCs
        session.run(
            "MATCH (entity:Entity {id: $entity_id}), (hlc:HLC {id: $hlc_id}) "
            "MERGE (hlc)-[:HAS_ENTITY]->(entity) "
            "MERGE (hlc)-[:HAS_CHAIN {order: $order}]->(entity) "
            "MERGE (e:Extraction)-[:HAS_HLC]->(hlc) "
            "MERGE (e)-[:HAS_ENTITY]->(entity) "
            "WITH entity, hlc "
            "UNWIND $token_ids AS token_id "
            "MATCH (mlc:MLC {id: token_id}) "
            "MERGE (entity)-[:COMBINATION_OF]->(mlc)",
            entity_id=entitylinking.entity_id,
            hlc_id=entitylinking.hlc_id,
            order=entitylinking.order,
            token_ids=entitylinking.token_ids
        )
    
        # 

    return {"message": "Entity linked to HLC successfully"}