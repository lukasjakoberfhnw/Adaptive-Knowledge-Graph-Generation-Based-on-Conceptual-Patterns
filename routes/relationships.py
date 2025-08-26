from fastapi import APIRouter, HTTPException, Request
from models.entity_models import RelationshipCreateModel

router = APIRouter()


@router.post("/relationships")
async def create_relationship(request: Request, relationship: RelationshipCreateModel):
    # Create a new relationship between two entities.
    # also add type of node where to add the relationship... 

    # if target_id, create relationship. Otherwise, create property.
    if(relationship.target_id is not None):
        
        # needs adjustment
        string_builder1 = "MATCH (source:" + relationship.source_type + " {id: $source_id}) "
        string_builder2 = "MATCH (target:" + relationship.target_type + " {id: $target_id}) "
        string_builder3 = f"MERGE (source)-[:{relationship.relationship_type}]->(target)"

        full_string = string_builder1 + string_builder2 + string_builder3

        with request.app.state.driver.session() as session:
            query = (
                full_string
            )
            session.run(
                query,
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                relationship_type=relationship.relationship_type
            )
    else:
        # source exists but no target indicated
        if not relationship.target_text:
            raise HTTPException(status_code=400, detail="Target text is required when target ID is not provided")
        with request.app.state.driver.session() as session:
            # set property of source entity with name = relationship_type and value = target_id

            # make sure that target does not have ' in it, otherwise it will break the query
            relationship.target_text = relationship.target_text.replace("'", "\\'")

            full_query = "MATCH (source:" + relationship.source_type + " {id: $source_id}) SET source." + relationship.relationship_type + " = '" + relationship.target_text + "'"

            query = (
                full_query
            )
            session.run(
                query,
                source_id=relationship.source_id
            )
    return {"message": "Relationship created successfully"}

@router.get("/relationship-types")
async def get_relationship_types(request: Request):
    """
    Retrieve all relationship types in the graph database.
    """
    driver = request.app.state.driver
    with driver.session() as session:
        result = session.run(
            "CALL db.relationshipTypes() YIELD relationshipType "
            "RETURN relationshipType"
        )

        relationship_types = [record["relationshipType"] for record in result]

        return {"relationship_types": relationship_types}
    