from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

@router.get("/workspace/important-mlcs")
async def get_important_mlcs(request: Request, extraction_id: str = None):
    """
    Retrieve important MLCs based on their relationships.
    """
    driver = request.app.state.driver
    with driver.session() as session:
        if extraction_id:
            # If extraction_id is provided, filter MLCs related to that extraction
            result = session.run(
                "MATCH (mlc)-[r:RELATED_TO]-(x) "
                "MATCH (e:Extraction {id: $extraction_id})-[:HAS_HLC]->(hlc:HLC)-[:HAS_CHAIN]->(mlc:MLC) "
                "WITH mlc, count(r) as rels "
                "ORDER BY rels DESC "
                "LIMIT 20 "
                "RETURN collect({mlc: mlc, strength: rels}) as important_mlcs",
                extraction_id=extraction_id
            )
        else:
            # Otherwise, find the most related MLCs in the entire database

            result = session.run(
                "MATCH (a:MLC)-[r:RELATED_TO]-(x) "
                "WITH a, count(r) as rels "
                "ORDER BY rels DESC "
                "LIMIT 20 "
                "RETURN collect({mlc: a, strength: rels}) as important_mlcs"
            )

        result = result.single()
        if not result or not result["important_mlcs"]:
            raise HTTPException(status_code=404, detail="No important MLCs found")
        
        result = result["important_mlcs"]

        important_mlcs = []
        for item in result:
            mlc = item["mlc"]
            important_mlcs.append({
                "id": mlc["id"],
                "text": mlc["text"],
                "creation_time": mlc["creation_time"] if "creation_time" in mlc else None,
                "labels": list(mlc.labels),
                "strength": item["strength"]
            })

        return important_mlcs

@router.get("/workspace/recent-creations")
async def get_recent_creations(request: Request):
    """
    Retrieve recent creations (MLCs, HLCs, Entities) in the workspace.
    """
    driver = request.app.state.driver
    with driver.session() as session:
        result = session.run(
            "MATCH (n) "
            "WHERE n:Extraction OR n:Entity "
            "RETURN n "
            "ORDER BY n.creation_time DESC "
            "LIMIT 20"
        )

        recent_creations = []
        for record in result:
            node = record["n"]
            recent_creations.append({
                "id": node["id"],
                "text": node["text"],
                "textual_identifier": node.get("textual_identifier", None),
                "creation_time": node["creation_time"] if "creation_time" in node else None,
                "labels": list(node.labels)
            })

        return recent_creations
    
@router.get("/workspace/n-grams")
async def get_ngrams(request: Request, extraction_id: str = None):
    """
    Retrieve n-grams from the text of an extraction.
    """

    driver = request.app.state.driver
    with driver.session() as session:
        if extraction_id:
            result = session.run(
                """
                    MATCH (e:Extraction {id: $extraction_id})-[:HAS_HLC]-(hlc:HLC)
                    MATCH (hlc)-[r:HAS_CHAIN]-(mlc:MLC)
                    WHERE EXISTS { (mlc)-[:RELATED_TO]-() }
                    WITH e, hlc, mlc
                    ORDER BY r.order ASC
                    WITH e, hlc, COLLECT(mlc.text) AS seq
                    WITH e, hlc, seq, SIZE(seq) AS seq_len
                    UNWIND (
                        [i IN RANGE(0, seq_len-2) | seq[i..i+2]] +    // duograms (n=2)
                        [i IN RANGE(0, seq_len-3) | seq[i..i+3]] +    // trigrams (n=3)
                        [i IN RANGE(0, seq_len-4) | seq[i..i+4]]      // quadruplograms (n=4)
                    ) AS ngram
                    WITH e.id AS extraction,
                        REDUCE(s = "", word IN ngram | s + word + " ") AS phrase,
                        COUNT(DISTINCT hlc) AS frequency
                    WHERE frequency > 1
                    RETURN extraction, phrase, frequency
                    ORDER BY frequency DESC
                    LIMIT 50
                """,
                extraction_id=extraction_id
            )
        else:
            result = session.run(
                """
                    MATCH (e:Extraction)-[:HAS_HLC]-(hlc:HLC)
                    MATCH (hlc)-[r:HAS_CHAIN]-(mlc:MLC)
                    WHERE EXISTS { (mlc)-[:RELATED_TO]-() }
                    WITH e, hlc, mlc
                    ORDER BY r.order ASC
                    WITH e, hlc, COLLECT(mlc.text) AS seq
                    WITH e, hlc, seq, SIZE(seq) AS seq_len
                    UNWIND (
                        [i IN RANGE(0, seq_len-2) | seq[i..i+2]] +    // duograms (n=2)
                        [i IN RANGE(0, seq_len-3) | seq[i..i+3]] +    // trigrams (n=3)
                        [i IN RANGE(0, seq_len-4) | seq[i..i+4]]      // quadruplograms (n=4)
                    ) AS ngram
                    WITH e.id AS extraction,
                        REDUCE(s = "", word IN ngram | s + word + " ") AS phrase,
                        COUNT(DISTINCT hlc) AS frequency
                    WHERE frequency > 1
                    RETURN extraction, phrase, frequency
                    ORDER BY frequency DESC
                    LIMIT 50
                """
            )

        ngrams = []
        for record in result:
            ngram = {
                "extraction_id": record["extraction"],
                "phrase": record["phrase"].strip(),
                "frequency": record["frequency"]
            }
            ngrams.append(ngram)

        return ngrams