from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

 
@router.get("/mlc/{mlc_id}")
async def get_mlc(request: Request, mlc_id: str):
    """
    Retrieve a specific MLC by its ID.
    """
    # get mlc from db
    driver = request.app.state.driver

    with driver.session() as session:
        # get MLC node by id, all relationships to this MLC, and the connected neighbour nodes
        # result = session.run(
        #     "MATCH (mlc:MLC {id: $mlc_id}) "
        #     "OPTIONAL MATCH (mlc)<-[r]-(x) "
        #     "RETURN mlc, collect({rel: r, rel_type: TYPE(r), neighbor: x, neighbor_type: LABELS(x)[0]}) AS relationships_with_neighbors",
        #     mlc_id=mlc_id
        # )

        result = session.run(
            """
                MATCH (mlc:MLC {id: $mlc_id})
                CALL(mlc) {
                    OPTIONAL MATCH (mlc)-[r:RELATED_TO]-(x)
                    WITH mlc, x, sum(r.strength) AS totalStrength
                    ORDER BY totalStrength DESC
                    LIMIT 20
                    WITH mlc, collect({strength: totalStrength, rel_type: 'RELATED_TO', 
                                    neighbor: x, neighbor_type: LABELS(x)[0]}) AS relationships_with_neighbors
                    OPTIONAL MATCH (mlc)-[other_r]-(other_node)
                    WHERE TYPE(other_r) <> 'RELATED_TO' AND TYPE(other_r) <> 'HAS_CHAIN'
                    RETURN relationships_with_neighbors,
                        collect({rel_type: TYPE(other_r), 
                                    neighbor: other_node, 
                                    neighbor_type: LABELS(other_node)[0]}) AS other_connections
                }

                CALL(mlc) {
                    OPTIONAL MATCH(mlc)-[:HAS_CHAIN]-(hlc:HLC)
                    OPTIONAL MATCH(hlc)-[:HAS_HLC]-(extraction:Extraction)
                    RETURN collect(DISTINCT hlc) as hlcs, collect(DISTINCT {id: extraction.id, textual_identifier: extraction.textual_identifier}) as extractions
                }

                RETURN mlc, relationships_with_neighbors, hlcs, extractions, other_connections
            """,
            parameters={"mlc_id": mlc_id}
        )

        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="MLC not found")
        
        mlc_node = record["mlc"]
        relationships_with_neighbors = record["relationships_with_neighbors"]

        # create MLC object with id, text, creation_time, and count of relationships
        mlc = {
            "id": mlc_node["id"],
            "text": mlc_node["text"],
            "creation_time": mlc_node["creation_time"],
            "properties": mlc_node,
            "count": mlc_node["count"] if "count" in mlc_node else 0, 
            "relationships_with_neighbors": relationships_with_neighbors,
            "other_connections": record["other_connections"],
            "hlcs": record["hlcs"],
            "extractions": record["extractions"]
        }

        # mlc = {
        #     "id": mlc_node["id"],
        #     "text": mlc_node["text"],
        #     "creation_time": mlc_node["creation_time"],
        #     "count": mlc_node["count"] if "count" in mlc_node else 0, 
        # }
        return mlc