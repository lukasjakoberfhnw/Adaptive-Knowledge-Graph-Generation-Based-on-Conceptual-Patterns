import logging
from collections import Counter
from datetime import datetime
from neo4j import GraphDatabase
from database.graph_helper import add_node, add_nodes
from data_processor.data_transformer import get_english_stopwords, get_spacy_tokens, get_nltk_tokens
import time
from models.extraction_models import ExtractionResponseModel

def extraction_create_optimized(driver, nlp, extraction_id, extraction, creation_time, sentences, entities_recommended):
    """
    This function computes all nodes and relationships in RAM before sending them
    in a minimal number of batched queries to the database.
    """
    logging.info(f"Starting optimized extraction for ID: {extraction_id}")
    stopsigns = {" ", ".", ",", ":", ";", "!", "?", "-", "_", "(", ")", "[", "]", "{", "}", "", "\n", "\"", "'", "/", "\n\n"}
    stopwords = get_english_stopwords()

    time_spend_on_task = {}

    # --- (1) PREPARE ALL DATA IN PYTHON ---
    
    all_mlcs = []
    enhanced_sentences = []
    hlc_to_mlc_chain = []
    # Using a Counter is highly efficient for aggregating relationship strengths
    related_to_strength_counter = Counter()

    for index, sentence in enumerate(sentences):
        start_time = time.time()
        spacy_tokens = get_spacy_tokens(nlp, sentence["text"])
        time_spend_on_task["tokenization"] = time.time() - start_time
        after_tokenization = time.time()

        # Store all MLCs for bulk creation later
        all_mlcs.extend(spacy_tokens)
        
        # Prepare sentence data with tokens for the response object
        enhanced_sentences.append({
            "hlc_id": sentence["hlc_id"],
            "text": sentence["text"],
            "index": index,
            "mlcs": spacy_tokens
        })
        
        # Prepare data for (HLC)-[:HAS_CHAIN]->(MLC) relationships
        for order, token in enumerate(spacy_tokens):
            hlc_to_mlc_chain.append({
                "hlc_id": sentence["hlc_id"],
                "mlc_id": token,
                "order": order
            })

        # Prepare data for (MLC)-[:RELATED_TO]->(MLC) relationships
        # Filter out stopwords and signs for these relationships
        filtered_tokens = [token for token in spacy_tokens if token.lower() not in stopwords and token not in stopsigns]
        
        # Generate all unique pairs within the sentence
        for i in range(len(filtered_tokens)):
            for j in range(i + 1, len(filtered_tokens)):
                # Sorting the pair ensures that (a, b) and (b, a) are treated as the same relationship
                pair = tuple(sorted((filtered_tokens[i], filtered_tokens[j])))
                related_to_strength_counter[pair] += 1

        rest = time.time() - after_tokenization
        time_spend_on_task["rest"] = rest

    logging.info(f"Time spent on task for extraction {extraction_id}: {time_spend_on_task}")

    # Convert the counter to the format needed for the Cypher query: [{'mlc1': 'a', 'mlc2': 'b', 'strength': 2}]
    mlc_to_mlc_relationships = [
        {"mlc1": pair[0], "mlc2": pair[1], "strength": strength}
        for pair, strength in related_to_strength_counter.items()
    ]

    # --- (2) EXECUTE MINIMAL DATABASE QUERIES ---

    with driver.session() as session:
        # Query 1: Create the main Extraction node
        session.run(
            "CREATE (e:Extraction {id: $extraction_id, text: $text, creation_time: $creation_time, status: 'initial', textual_identifier: $textual_identifier, source_id: $source_id})",
            extraction_id=extraction_id, text=extraction.text, creation_time=creation_time,
            textual_identifier=extraction.textual_identifier if extraction.textual_identifier else None,
            source_id=extraction.source_id if extraction.source_id else None
        )
        logging.info("Step 1/5: Extraction node created.")

        # Query 2: Bulk create all unique MLC nodes from the entire text
        add_nodes(driver, all_mlcs, "MLC")
        logging.info(f"Step 2/5: {len(set(all_mlcs))} unique MLC nodes created.")

        # Query 3: Bulk create all HLC nodes and link them to the Extraction node
        sentences_with_index = [{"hlc_id": s["hlc_id"], "text": s["text"], "index": s["index"]} for s in enhanced_sentences]
        session.run(
            """
            MATCH (e:Extraction {id: $extraction_id})
            UNWIND $sentences AS s
            CREATE (hlc:HLC {id: s.hlc_id, text: s.text, creation_time: $creation_time})
            CREATE (e)-[:HAS_HLC {order: s.index}]->(hlc)
            """,
            extraction_id=extraction_id, sentences=sentences_with_index, creation_time=creation_time
        )
        logging.info(f"Step 3/5: {len(sentences_with_index)} HLC nodes and their relationships to Extraction created.")

        # Query 4: Bulk create all (HLC)-[:HAS_CHAIN]->(MLC) relationships
        session.run(
            """
            UNWIND $chain_data AS data
            MATCH (hlc:HLC {id: data.hlc_id})
            MATCH (mlc:MLC {id: data.mlc_id})
            CREATE (hlc)-[r:HAS_CHAIN]->(mlc)
            SET r.order = data.order
            """,
            chain_data=hlc_to_mlc_chain
        )
        logging.info(f"Step 4/5: {len(hlc_to_mlc_chain)} HAS_CHAIN relationships created.")

        # Query 5: Bulk create/update all (MLC)-[:RELATED_TO]->(MLC) relationships
        if mlc_to_mlc_relationships:
            session.run(
                """
                UNWIND $relationships AS rel
                MATCH (a:MLC {id: rel.mlc1})
                MATCH (b:MLC {id: rel.mlc2})
                MERGE (a)-[r:RELATED_TO]-(b)
                ON CREATE SET r.strength = rel.strength
                ON MATCH SET r.strength = r.strength + rel.strength
                """,
                relationships=mlc_to_mlc_relationships
            )
        logging.info(f"Step 5/5: {len(mlc_to_mlc_relationships)} RELATED_TO relationships created/updated.")

    logging.info(f"Extraction {extraction_id} created successfully.")

    # --- (3) RETURN RESPONSE ---

    response = ExtractionResponseModel(
        extraction_id=extraction_id,
        textual_identifier=extraction.textual_identifier if extraction.textual_identifier else None,
        source_id=extraction.source_id if extraction.source_id else None,
        status="initial",
        text=extraction.text,
        sentences=enhanced_sentences,
        entities_recommended=entities_recommended,
        relationships=None,
        creation_time=creation_time
    )
    return response

# test function to check the nltk --> could be written much better, especially for the future if it should be configurable... for now, just a quick test
def extraction_create_optimized_nltk(driver, nlp, extraction_id, extraction, creation_time, sentences, entities_recommended):
    """
    This function computes all nodes and relationships in RAM before sending them
    in a minimal number of batched queries to the database.
    """
    logging.info(f"Starting optimized extraction for ID: {extraction_id}")
    stopsigns = {" ", ".", ",", ":", ";", "!", "?", "-", "_", "(", ")", "[", "]", "{", "}", "", "\n", "\"", "'", "/", "\n\n"}
    stopwords = get_english_stopwords()

    time_spend_on_task = {}

    # --- (1) PREPARE ALL DATA IN PYTHON ---
    
    all_mlcs = []
    enhanced_sentences = []
    hlc_to_mlc_chain = []
    # Using a Counter is highly efficient for aggregating relationship strengths
    related_to_strength_counter = Counter()

    for index, sentence in enumerate(sentences):
        start_time = time.time()
        nltk_tokens = get_nltk_tokens(sentence["text"])
        time_spend_on_task["tokenization"] = time.time() - start_time
        after_tokenization = time.time()

        # Store all MLCs for bulk creation later
        all_mlcs.extend(nltk_tokens)
        
        # Prepare sentence data with tokens for the response object
        enhanced_sentences.append({
            "hlc_id": sentence["hlc_id"],
            "text": sentence["text"],
            "index": index,
            "mlcs": nltk_tokens
        })
        
        # Prepare data for (HLC)-[:HAS_CHAIN]->(MLC) relationships
        for order, token in enumerate(nltk_tokens):
            hlc_to_mlc_chain.append({
                "hlc_id": sentence["hlc_id"],
                "mlc_id": token,
                "order": order
            })

        # Prepare data for (MLC)-[:RELATED_TO]->(MLC) relationships
        # Filter out stopwords and signs for these relationships
        filtered_tokens = [token for token in nltk_tokens if token.lower() not in stopwords and token not in stopsigns]
        
        # Generate all unique pairs within the sentence
        for i in range(len(filtered_tokens)):
            for j in range(i + 1, len(filtered_tokens)):
                # Sorting the pair ensures that (a, b) and (b, a) are treated as the same relationship
                pair = tuple(sorted((filtered_tokens[i], filtered_tokens[j])))
                related_to_strength_counter[pair] += 1

        rest = time.time() - after_tokenization
        time_spend_on_task["rest"] = rest

    logging.info(f"Time spent on task for extraction {extraction_id}: {time_spend_on_task}")

    # Convert the counter to the format needed for the Cypher query: [{'mlc1': 'a', 'mlc2': 'b', 'strength': 2}]
    mlc_to_mlc_relationships = [
        {"mlc1": pair[0], "mlc2": pair[1], "strength": strength}
        for pair, strength in related_to_strength_counter.items()
    ]

    # --- (2) EXECUTE MINIMAL DATABASE QUERIES ---

    with driver.session() as session:
        # Query 1: Create the main Extraction node
        session.run(
            "CREATE (e:Extraction {id: $extraction_id, text: $text, creation_time: $creation_time, status: 'initial', textual_identifier: $textual_identifier, source_id: $source_id})",
            extraction_id=extraction_id, text=extraction.text, creation_time=creation_time,
            textual_identifier=extraction.textual_identifier if extraction.textual_identifier else None,
            source_id=extraction.source_id if extraction.source_id else None
        )
        logging.info("Step 1/5: Extraction node created.")

        # Query 2: Bulk create all unique MLC nodes from the entire text
        add_nodes(driver, all_mlcs, "MLC")
        logging.info(f"Step 2/5: {len(set(all_mlcs))} unique MLC nodes created.")

        # Query 3: Bulk create all HLC nodes and link them to the Extraction node
        sentences_with_index = [{"hlc_id": s["hlc_id"], "text": s["text"], "index": s["index"]} for s in enhanced_sentences]
        session.run(
            """
            MATCH (e:Extraction {id: $extraction_id})
            UNWIND $sentences AS s
            CREATE (hlc:HLC {id: s.hlc_id, text: s.text, creation_time: $creation_time})
            CREATE (e)-[:HAS_HLC {order: s.index}]->(hlc)
            """,
            extraction_id=extraction_id, sentences=sentences_with_index, creation_time=creation_time
        )
        logging.info(f"Step 3/5: {len(sentences_with_index)} HLC nodes and their relationships to Extraction created.")

        # Query 4: Bulk create all (HLC)-[:HAS_CHAIN]->(MLC) relationships
        session.run(
            """
            UNWIND $chain_data AS data
            MATCH (hlc:HLC {id: data.hlc_id})
            MATCH (mlc:MLC {id: data.mlc_id})
            CREATE (hlc)-[r:HAS_CHAIN]->(mlc)
            SET r.order = data.order
            """,
            chain_data=hlc_to_mlc_chain
        )
        logging.info(f"Step 4/5: {len(hlc_to_mlc_chain)} HAS_CHAIN relationships created.")

        # Query 5: Bulk create/update all (MLC)-[:RELATED_TO]->(MLC) relationships
        if mlc_to_mlc_relationships:
            session.run(
                """
                UNWIND $relationships AS rel
                MATCH (a:MLC {id: rel.mlc1})
                MATCH (b:MLC {id: rel.mlc2})
                MERGE (a)-[r:RELATED_TO]-(b)
                ON CREATE SET r.strength = rel.strength
                ON MATCH SET r.strength = r.strength + rel.strength
                """,
                relationships=mlc_to_mlc_relationships
            )
        logging.info(f"Step 5/5: {len(mlc_to_mlc_relationships)} RELATED_TO relationships created/updated.")

    logging.info(f"Extraction {extraction_id} created successfully.")

    # --- (3) RETURN RESPONSE ---

    response = ExtractionResponseModel(
        extraction_id=extraction_id,
        textual_identifier=extraction.textual_identifier if extraction.textual_identifier else None,
        source_id=extraction.source_id if extraction.source_id else None,
        status="initial",
        text=extraction.text,
        sentences=enhanced_sentences,
        entities_recommended=entities_recommended,
        relationships=None,
        creation_time=creation_time
    )
    return response