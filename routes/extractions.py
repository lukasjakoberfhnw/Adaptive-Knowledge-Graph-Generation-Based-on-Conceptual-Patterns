from datetime import datetime
import time
import uuid
from fastapi import APIRouter, HTTPException, Request
from data_processor.data_transformer import get_spacy_sentences
from helper import extraction_create, remove_all_nodes
from helper_test import ExtractionResponseModel, extraction_create_optimized, extraction_create_optimized_nltk
from models.extraction_models import ExtractionCreateModel

router = APIRouter()

@router.get("/extractions")
async def get_extractions(request: Request):
    """
    Retrieve all extractions.
    """

    # get list of the last 10 extractions from the database
    driver = request.app.state.driver
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Extraction) "
            "RETURN e "
            "ORDER BY e.creation_time DESC "
            "LIMIT 10"
        )
        extractions = []
        for record in result:
            extraction_node = record["e"]
            extraction = ExtractionResponseModel(
                extraction_id=extraction_node["id"],
                textual_identifier=extraction_node.get("textual_identifier"),
                source_id=extraction_node.get("source_id"),
                status=extraction_node["status"],
                text=extraction_node["text"],
                sentences=[],  # Placeholder for sentences
                entities_recommended=None,  # Placeholder for entities
                relationships=None,  # Placeholder for relationships
                creation_time=extraction_node["creation_time"]
            )
            extractions.append(extraction)

        if not extractions:
            raise HTTPException(status_code=404, detail="No extractions found")
        
        return extractions

@router.get("/extractions/{extraction_id}")
async def get_extraction(request: Request,extraction_id: str):
    """
    Retrieve a specific extraction by its ID.
    """

    # retrieve extraction from database
    driver = request.app.state.driver
    with driver.session() as session:
        # use cypher to find extraction by id and the corresponding HLCs 
        result = session.run(
        "MATCH (e:Extraction {id: $extraction_id})-[r:HAS_HLC]->(hlc:HLC) "
        "WITH e, hlc, r.order AS pos "
        "ORDER BY pos "
        "WITH e, collect({id: hlc.id, text: hlc.text}) AS hlc_list "
        "OPTIONAL MATCH (e)-[:HAS_ENTITY]->(entity:Entity) "
        "RETURN "
          "e AS extraction, "
            "hlc_list, "
            "collect(entity) as entities ",
            extraction_id=extraction_id
        )
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Extraction not found")

        extraction_node = record["extraction"]
        hlcs = record["hlc_list"]
        entities = record["entities"]
        
        # create sentences from hlcs
        # sentences = [{"hlc_id": hlc["id"], "text": hlc["text"]} for hlc in hlcs]

        sentences = [{"hlc_id": hlc["id"], "text": hlc["text"]} for hlc in hlcs]
        
        
        # entities_recommended = get_spacy_entities(extraction_node["text"])
        # if entities_recommended is None or len(entities_recommended) == 0:
        #     entities_recommended = None
        # else:
        #     entities_recommended = [Entity(text=ent[0], label=ent[1], start_char=ent[2], end_char=ent[3]) for ent in entities_recommended]
        
        response = ExtractionResponseModel(
            extraction_id=extraction_node["id"],
            textual_identifier=extraction_node.get("textual_identifier"),
            source_id=extraction_node.get("source_id"),
            status=extraction_node["status"],
            text=extraction_node["text"],
            sentences=sentences,
            # entities_recommended=entities_recommended,
            relationships=None,  # Placeholder for relationships
            creation_time=extraction_node["creation_time"],
            entities=entities
        )
        return response

@router.post("/extractions")
async def create_extraction(request: Request, extraction: ExtractionCreateModel):
    """
    Create a new extraction task.
    """
    # load required context
    spacy_context = request.app.state.spacy_context
    driver = request.app.state.driver

    # create new unique id for extraction
    extraction_id = str(uuid.uuid4())

    # get sentences from extraction text
    sentences = get_spacy_sentences(spacy_context,extraction.text)

    if not sentences:
        raise HTTPException(status_code=400, detail="System could not split text into sentences based on spacy processing.")

    # process sentences to create HLCs
    sentences = [{"hlc_id": str(uuid.uuid4()), "text": sentence} for sentence in sentences]

    # get entities from spacy
    # entities_recommended = get_spacy_entities(extraction.text)
    # print("Entities Recommended:", entities_recommended)
    # if entities_recommended is None or len(entities_recommended) == 0:
    #     entities_recommended = None
    # else:
    #     entities_recommended = [Entity(text=ent[0], label=ent[1], start_char=ent[2], end_char=ent[3]) for ent in entities_recommended]

    creation_time = datetime.now().isoformat()

    # Call the extraction_create function to process the extraction
    # response = extraction_create(driver, extraction_id, extraction, creation_time, sentences, [])

    # remove_all_nodes(driver)
    # print("Removed all nodes for testing the speed")

    start_time = time.time()   

    # Was used for measuring the speed of extraction/transformation using different algorithms and libraries
    # response_old = extraction_create(driver, spacy_context, extraction_id, extraction, creation_time, sentences, [])
    # after_old = time.time()
    # diff_for_old = after_old - start_time

    # print(f"Old extraction_create took {after_old - start_time:.2f} seconds")
    # remove_all_nodes(driver)
    # print("Removed all nodes for testing the speed")
    
    # start_time = time.time()
    # response = extraction_create_optimized(driver, spacy_context, extraction_id, extraction, creation_time, sentences, [])
    # after_optimized = time.time()
    # diff_for_optimized = after_optimized - start_time

    # print(f"Optimized extraction_create took {after_optimized - start_time:.2f} seconds")

    # remove_all_nodes(driver)
    # print("Removed all nodes for testing the speed")

    start_time = time.time()
    # using nltk tokenizor - testing for speed 
    response = extraction_create_optimized_nltk(driver, spacy_context, extraction_id, extraction, creation_time, sentences, [])

    after_nltk = time.time()
    print(f"NLTK optimized extraction_create took {after_nltk - start_time:.2f} seconds")

    print(f"Different execution times per model and process: ")
    # print(f" - Old: {diff_for_old:.2f} seconds")
    # print(f" - Optimized: {diff_for_optimized:.2f} seconds")
    print(f" - NLTK: {after_nltk - start_time:.2f} seconds")

    response = ExtractionResponseModel(
        extraction_id=extraction_id,
        textual_identifier=extraction.textual_identifier if extraction.textual_identifier else None,
        source_id=extraction.source_id if extraction.source_id else None,
        status="initial",
        text=extraction.text,
        sentences=sentences,  
        entities_recommended=[], # return nothing for faster response time -> entity extraction at a later stage 
        relationships=None,  # Placeholder for relationships
        creation_time=creation_time
    )
    return response
