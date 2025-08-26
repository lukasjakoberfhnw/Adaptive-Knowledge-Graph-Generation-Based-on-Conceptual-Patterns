from pypdf import PdfReader
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from data_processor.data_transformer import get_english_stopwords, get_spacy_tokens
from models.function_models import RecommendedEntityFetch

router = APIRouter()

@router.post("/text-from-pdf")
async def text_from_pdf(file: UploadFile = File(...)):
    """
    Extract text from a PDF file.
    """
    # Placeholder for actual PDF text extraction logic
    # In a real application, you would use a library like PyPDF2 or pdfminer.six to extract text from the PDF
    
    print(f"Received file: {file.filename}, Content Type: {file.content_type}")

    reader = PdfReader(file.file)
    extracted_text = ""
    for page in reader.pages:
        extracted_text += page.extract_text() + "\n"
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from the PDF file.")

    return {"extracted_text": extracted_text}
    # return {"extracted_text": "This is a placeholder for the extracted text from the PDF file."}


@router.get("/nodes/search")
async def search_nodes(request: Request, query: str, node_type: str):
    """
    Search for nodes in the graph database based on a query string.
    """

    spacy_context = request.app.state.spacy_context

    if not query:
        raise HTTPException(status_code=400, detail="Query string is required")

    print(f"Search query: {query}")

    if(" " in query):
        # use tokenizor and find all relevant mlcs
        # split query into tokens

        # make sure to use the same tokenizer as the one used for indexing
        tokens = get_spacy_tokens(spacy_context, query)
        if not tokens:
            raise HTTPException(status_code=400, detail="No tokens found in the query string")
        print(f"Tokens found: {tokens}")

        tokens = [t.strip() for t in tokens if t.strip()]  # Clean up tokens
        tokens = [t.lower() for t in tokens]  # Convert to lower case for case-insensitive search
        tokens = [t for t in tokens if t not in get_english_stopwords()]  # Remove stopwords ---> idk how smart this is -- gets more concrete results but removes the possible usage of stopwords

        # get MLCs for tokens
        driver = request.app.state.driver
        with driver.session() as session:
            result = session.run(
                "MATCH (mlc:MLC) "
                "WHERE toLower(mlc.text) IN $tokens "
                "OPTIONAL MATCH (mlc)<-[:COMBINATION_OF]-(entity:Entity) "
                "OPTIONAL MATCH (mlc)<-[:HAS_CHAIN]-(hlc:HLC) "
                "RETURN mlc, collect(hlc) as hlcs, collect(entity) as entities",
                tokens=tokens
            )

            nodes = {}

            # Iterate through the result and collect all nodes as a single node
            for record in result:
                mlc_node = record["mlc"]
                entities = record["entities"]
                hlcs = record["hlcs"]

                if mlc_node:
                    nodes[mlc_node["id"]] = {
                        "id": mlc_node["id"],
                        "text": mlc_node["text"],
                        "creation_time": mlc_node["creation_time"],
                        "labels": list(mlc_node.labels),
                        "strength": 9999
                    }

                for entity in entities:
                    if entity["id"] not in nodes:
                        # Add entity only if it is not already added
                        nodes[entity["id"]] = {
                            "id": entity["id"],
                            "text": entity["text"],
                            "textual_identifier": entity.get("textual_identifier", None),
                            "creation_time": entity["creation_time"],
                            "labels": list(entity.labels),
                            "strength": 0
                        }
                    else:
                        # If entity already exists, just update the strength
                        nodes[entity["id"]]["strength"] += 1

                for hlc in hlcs:
                    if hlc["id"] not in nodes:
                        # Add HLC only if it is not already added
                        nodes[hlc["id"]] = {
                            "id": hlc["id"],
                            "text": hlc["text"],
                            "creation_time": hlc["creation_time"],
                            "labels": list(hlc.labels),
                            "strength": 0
                        }
                    else:
                        # If HLC already exists, just update the strength
                        nodes[hlc["id"]]["strength"] += 1

            if not nodes:
                raise HTTPException(status_code=404, detail="No nodes found matching the query")

            # Convert the dictionary to a list of nodes
            nodes = list(nodes.values())
            # Sort nodes by strength in descending order
            nodes.sort(key=lambda x: x["strength"], reverse=True)

            return nodes

    # if no space, we assume it's a single term search -- currently does not find "brucelee" or "kgg_1"
    driver = request.app.state.driver
    with driver.session() as session:
        # Use a full-text search or a simple substring match
        result = session.run(
            f"MATCH (n{node_type}) "
            "WHERE toLower(n.text) CONTAINS toLower($search_term) OR toLower(n.textual_identifier) CONTAINS toLower($search_term) "
            "RETURN n",
            search_term=query
        )

        nodes = []
        for record in result:
            node = record["n"]
            nodes.append({
                "id": node["id"],
                "text": node["text"],
                "creation_time": node["creation_time"],
                "textual_identifier": node.get("textual_identifier", None),
                "labels": list(node.labels),
                "creation_time": node.get("creation_time", None),
            })

        return nodes

@router.post("/find-recommended-entities")
async def find_entities(request: Request, body: RecommendedEntityFetch):
    # what input do we need?
    # mlc_ids to find entities that are linked to the entities
    # hlc_id to find entities that are linked to the HLC
    # extraction_id to find entities that are linked to the Extraction

    print(body.mlc_ids, body.hlc_id)
    # remove grammatical stuff here like ".", "," etc.
    stopsigns = {" ", ".", ",", ":", ";", "!", "?", "-", "_", "(", ")", "[", "]", "{", "}", "", "\n", "\"", "'", "/", "\n\n"}
    body.mlc_ids = [mlc_id for mlc_id in body.mlc_ids if mlc_id not in stopsigns]


    # get tokens from hlc_id
    with request.app.state.driver.session() as session:
        possible_entities = []
        if body.hlc_id:
            result = session.run(
                """
                    CALL () {
                        MATCH (mlc:MLC)
                    WHERE mlc.id IN $mlc_ids
                    MATCH (hlc:HLC {id: $hlc_id})
                    OPTIONAL MATCH (e1:Entity)-[:COMBINATION_OF]-(mlc)
                    OPTIONAL MATCH (e2:Entity)-[:HAS_ENTITY]-(hlc)
                    OPTIONAL MATCH (extraction:Extraction)-[:HAS_HLC]-(hlc)
                    OPTIONAL MATCH (e3:Entity)-[:HAS_ENTITY]-(extraction)
                    WITH mlc, hlc,
                    [entity IN COLLECT(DISTINCT e1) WHERE entity IS NOT NULL | {entity: entity, origin: 'mlc'}] +
                    [entity IN COLLECT(DISTINCT e2) WHERE entity IS NOT NULL | {entity: entity, origin: 'hlc'}] +
                    [entity IN COLLECT(DISTINCT e3) WHERE entity IS NOT NULL | {entity: entity, origin: 'extraction'}] AS all_entities

                    UNWIND all_entities AS entity
                    WITH entity.entity AS ent, collect(DISTINCT entity.origin) AS origins, count(*) AS frequency
                    RETURN ent AS e, origins as mlcs, frequency
                    ORDER BY frequency DESC
                    UNION
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
                    }
                    WITH e, mlcs, frequency
                    WHERE frequency >= 2
                    ORDER BY frequency DESC
                    RETURN e, mlcs, frequency
                    LIMIT 5
                """,
                hlc_id=body.hlc_id,
                mlc_ids=body.mlc_ids
            )

            possible_entities = [record for record in result]

            # now check if any of them make sense
            # for each token? or for each entity that spacy is predicting? or for each entity that is already in the database? so many questions...

        print(possible_entities)

    return possible_entities

@router.get("/compare-extractions")
async def compare_extractions(request: Request, extraction_id_1: str, extraction_id_2: str):
    """
    Compare two extractions and return their differences.
    """
    driver = request.app.state.driver
    with driver.session() as session:
        result = session.run(
            """
                CALL {
                    MATCH (e:Extraction)-[:HAS_HLC]-(hlc:HLC)
                    WHERE e.id = $extraction_id_1
                    MATCH (hlc)-[r:HAS_CHAIN]-(mlc:MLC)
                    WHERE EXISTS { (mlc)-[:RELATED_TO]-() }
                    WITH e, hlc, mlc
                    ORDER BY r.order ASC
                    WITH e, hlc, COLLECT(mlc.text) AS seq
                    WITH e, hlc, seq, SIZE(seq) AS seq_len
                    UNWIND (
                        [i IN RANGE(0, seq_len-2) | seq[i..i+2]] +
                        [i IN RANGE(0, seq_len-3) | seq[i..i+3]] +
                        [i IN RANGE(0, seq_len-4) | seq[i..i+4]]
                    ) AS ngram
                    WITH REDUCE(s = "", word IN ngram | s + word + " ") AS phrase,
                        COUNT(DISTINCT hlc) AS freq1
                    // WHERE freq1 > 1 maybe add later again if there are too many results...
                    RETURN phrase, freq1
                    }
                    WITH COLLECT({phrase: phrase, freq1: freq1}) AS set1

                    // Process second extraction
                CALL {
                    MATCH (e2:Extraction)-[:HAS_HLC]-(hlc2:HLC)
                    WHERE e2.id = $extraction_id_2
                    MATCH (hlc2)-[r2:HAS_CHAIN]-(mlc2:MLC)
                    WHERE EXISTS { (mlc2)-[:RELATED_TO]-() }
                    WITH e2, hlc2, mlc2
                    ORDER BY r2.order ASC
                    WITH e2, hlc2, COLLECT(mlc2.text) AS seq2
                    WITH e2, hlc2, seq2, SIZE(seq2) AS seq_len2
                    UNWIND (
                        [i IN RANGE(0, seq_len2-2) | seq2[i..i+2]] +
                        [i IN RANGE(0, seq_len2-3) | seq2[i..i+3]] +
                        [i IN RANGE(0, seq_len2-4) | seq2[i..i+4]]
                    ) AS ngram2
                    WITH REDUCE(s = "", word IN ngram2 | s + word + " ") AS phrase,
                        COUNT(DISTINCT hlc2) AS freq2
                    // WHERE freq2 > 1 maybe add later again if there are too many results...
                    RETURN phrase, freq2
                }
                WITH set1, COLLECT({phrase: phrase, freq2: freq2}) AS set2

                // Compute intersection and sum frequencies
                UNWIND set1 AS s1
                UNWIND set2 AS s2
                WITH s1, s2
                WHERE s1.phrase = s2.phrase
                RETURN s1.phrase AS phrase,
                    s1.freq1 AS extraction1_freq,
                    s2.freq2 AS extraction2_freq,
                    s1.freq1 + s2.freq2 AS total_frequency
                ORDER BY total_frequency DESC
                LIMIT 50
            """,
            extraction_id_1=extraction_id_1,
            extraction_id_2=extraction_id_2
        )
        
        intersections = []

        for record in result:
            # print("Record:", record)
            intersection = {
                "phrase": record["phrase"],
                "extraction1_freq": record["extraction1_freq"],
                "extraction2_freq": record["extraction2_freq"],
                "total_frequency": record["total_frequency"]
            }
            intersections.append(intersection)

        if not intersections:
            raise HTTPException(status_code=404, detail="No common phrases found between the two extractions")
        
        return intersections