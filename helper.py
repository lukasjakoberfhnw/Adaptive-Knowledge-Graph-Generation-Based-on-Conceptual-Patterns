from datetime import datetime

from neo4j import GraphDatabase
from models.extraction_models import ExtractionResponseModel, Entity
from database.graph_helper import add_node, add_nodes
from data_processor.data_transformer import get_english_stopwords, get_spacy_tokens
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extraction_create(driver, spacy_context, extraction_id, extraction, creation_time, sentences, entities_recommended):
    stopsigns = [" ", ".", ",", ":", ";", "!", "?", "-", "_", "(", ")", "[", "]", "{", "}", "", "\n", "\"", "'", "/", "\n\n"]

    with driver.session() as session:
        session.run(
            "CREATE (e:Extraction {id: $extraction_id, text: $text, creation_time: $creation_time, status: 'initial', textual_identifier: $textual_identifier, source_id: $source_id})",
            extraction_id=extraction_id,
            text=extraction.text,
            creation_time=creation_time,
            textual_identifier=extraction.textual_identifier if extraction.textual_identifier else None,
            source_id=extraction.source_id if extraction.source_id else None
        )

        for index, sentence in enumerate(sentences):
            print("Processing sentence:", sentence)
            session.run(
                "MERGE (e:Extraction {id: $extraction_id}) "  # Finds or creates if missing
                "CREATE (hlc:HLC {id: $hlc_id, text: $text, creation_time: $creation_time}) "
                "CREATE (e)-[:HAS_HLC {order: $index}]->(hlc)",
                hlc_id=sentence["hlc_id"],
                text=sentence["text"],
                creation_time=creation_time,
                extraction_id=extraction_id,
                index=index
            )

            spacy_tokens = get_spacy_tokens(spacy_context, sentence["text"])
            print("Spacy tokens for sentence:", spacy_tokens)

            # create MLCs for each sentence
            # for token in spacy_tokens:
                # might need processing to ensure token makes sense... -> possibly check for punctuation or other non-word characters
                
                #----- this leads to missing MLCs like Jackie Chan ?? idk why tbh
                # if token in [" ", ".", ",", ":", ";", "!", "?", "-", "_", "(", ")", "[", "]", "{", "}", "", "\n", "\"", "'"]: 
                #     # not necessary for natural MLCs I think -- might be different for structured languages
                #     # this somehow messes up the "Jackie" token?? whyyyy...
                #     print(f"Skipping token: {token} as it is not a valid MLC")
                #     spacy_tokens.remove(token)
                #     continue
                #-----
                # add_node(driver, token, "MLC")
            add_nodes(driver, spacy_tokens, "MLC")

            # create relationships between MLCs and HLC including the correct order
            
            tokens_with_order = [{"mlc_id": id, "order": idx} for idx, id in enumerate(spacy_tokens)]
            print("Tokens with order for HLC:", tokens_with_order)

            result = session.run(
                """MATCH (hlc:HLC {id: $hlc_id})
                UNWIND $tokens_with_order AS token_data
                MATCH (mlc:MLC {id: token_data.mlc_id})
                CREATE (hlc)-[r:HAS_CHAIN]->(mlc)
                SET r.order = token_data.order""",
                hlc_id=sentence["hlc_id"],
                tokens_with_order=tokens_with_order
            )

            # if result:
            #     print("Relationships created between HLC and MLCs.")
            # else:
            #     print("No relationships created between HLC and MLCs.")

            # remove stopwords from spacy_tokens --> they will not be used for RELATED_TO relationships
            stopwords = get_english_stopwords()
            spacy_tokens = [token for token in spacy_tokens if (token.lower() not in stopwords) and (token not in stopsigns)]

            # create all relationships locally in python first, then push all at once to the database
            relationships = []
            for i in range(len(spacy_tokens)):
                for j in range(i + 1, len(spacy_tokens)):
                    if i != j:
                        relationships.append((spacy_tokens[i], spacy_tokens[j]))

            # push all relationships to the database using a single query --> I think this does not work...
            if relationships:
                session.run(
                    """
                    WITH $relationships AS relationships
                    UNWIND relationships AS rel
                    MATCH (a:MLC {id: rel[0]}), (b:MLC {id: rel[1]})
                    MERGE (a)-[r:RELATED_TO]->(b)
                    ON CREATE SET r.strength = 1
                    ON MATCH SET r.strength = r.strength + 1""",
                    relationships=relationships
                )


            # create relationships for each MLC in the sentence to each other MLC in the sentence
            # for i in range(len(spacy_tokens)):
            #     for j in range(i + 1, len(spacy_tokens)):
            #         if i != j:
            #             session.run(
            #                 """MATCH (a:MLC {id: $mlc1_id}), (b:MLC {id: $mlc2_id})
            #                 MERGE (a)-[r:RELATED_TO]->(b)
            #                 ON CREATE SET r.strength = 1
            #                 ON MATCH SET r.strength = r.strength + 1""",
            #                 mlc1_id=spacy_tokens[i],
            #                 mlc2_id=spacy_tokens[j]
            #             )

    print("Extraction created with ID:", extraction_id)

    response = ExtractionResponseModel(
        extraction_id=extraction_id,
        textual_identifier=extraction.textual_identifier if extraction.textual_identifier else None,
        source_id=extraction.source_id if extraction.source_id else None,
        status="initial",
        text=extraction.text,
        sentences=sentences,  
        entities_recommended=entities_recommended,
        relationships=None,  # Placeholder for relationships
        creation_time=creation_time
    )

    return response

def extraction_create_calculate_in_ram(driver, spacy_context, extraction_id, extraction, creation_time, sentences, entities_recommended):
    """
        This function calculates all relationships in RAM before sending it in batches 
        to the database.

        This function could be even more optimized by using async requests to Neo4j and
        calculate relationships in the meantime - fully utilizing the parallel options.
    """
    # set stopsigns
    stopsigns = [" ", ".", ",", ":", ";", "!", "?", "-", "_", "(", ")", "[", "]", "{", "}", "", "\n", "\"", "'", "/", "\n\n"]
    with driver.session() as session:
        # create extraction in DB and retrieve ID

        logging.info(f"Creating extraction with ID: {extraction_id} and text: {extraction.text}")

        session.run(
            "CREATE (e:Extraction {id: $extraction_id, text: $text, creation_time: $creation_time, status: 'initial', textual_identifier: $textual_identifier, source_id: $source_id})",
            extraction_id=extraction_id,
            text=extraction.text,
            creation_time=creation_time,
            textual_identifier=extraction.textual_identifier if extraction.textual_identifier else None,
            source_id=extraction.source_id if extraction.source_id else None
        )

        logging.info(f"Extraction created with ID: {extraction_id}")

        logging.info(f"Loading all MLCs")

        # retrieve all MLCs from all sentences to send one query only
        all_mlcs: list[str] = []

        # object to store enhanced sentences with MLCs
        enhanced_sentences: list[dict] = []

        for index, sentence in enumerate(sentences):
            spacy_tokens = get_spacy_tokens(spacy_context, sentence["text"])
            enhanced_sentences.append({
                "hlc_id": sentence["hlc_id"],
                "text": sentence["text"],
                "index": index,
                "mlcs": spacy_tokens
            })
            all_mlcs.extend(spacy_tokens)


        # check if the MLCs exists, if not, create them and retrieve all ids - in one query
        add_nodes(driver, all_mlcs, "MLC")

        logging.info(f"All MLCs loaded: {len(all_mlcs)} MLCs")

        logging.info(f"Creating HLCs and add relation to Extraction")
        sentences_with_index = [{"hlc_id": sentence["hlc_id"], "text": sentence["text"], "index": index} for index, sentence in enumerate(sentences)]
        # create HLCs and relate them to the Extraction
        session.run(
            "UNWIND $sentences AS sentence "
            "MERGE (e:Extraction {id: $extraction_id}) "  # Finds or creates if missing
            "CREATE (hlc:HLC {id: sentence.hlc_id, text: sentence.text, creation_time: $creation_time}) "
            "CREATE (e)-[:HAS_HLC {order: sentence.index}]->(hlc)"
            "RETURN hlc",
            sentences=sentences_with_index,
            creation_time=creation_time,
            extraction_id=extraction_id
        )
        logging.info(f"HLCs created and related to Extraction with ID: {extraction_id}")

        # calculate all relationships between MLCs and HLCs with the correct order
        for enhanced_sentence in enhanced_sentences:
            tokens_with_order = [{"mlc_id": id, "order": idx} for idx, id in enumerate(enhanced_sentence["mlcs"])]
            logging.info(f"Creating relationships between HLC {enhanced_sentence['hlc_id']} and MLCs with order: {tokens_with_order}")

            result = session.run(
                """MATCH (hlc:HLC {id: $hlc_id})
                UNWIND $tokens_with_order AS token_data
                MATCH (mlc:MLC {id: token_data.mlc_id})
                CREATE (hlc)-[r:HAS_CHAIN]->(mlc)
                SET r.order = token_data.order""",
                hlc_id=enhanced_sentence["hlc_id"],
                tokens_with_order=tokens_with_order
            )

            stopwords = get_english_stopwords()
            spacy_tokens = [token for token in spacy_tokens if (token.lower() not in stopwords) and (token not in stopsigns)]

            # create all relationships locally in python first, then push all at once to the database
            relationships = []
            for i in range(len(spacy_tokens)):
                for j in range(i + 1, len(spacy_tokens)):
                    if i != j:
                        relationships.append((spacy_tokens[i], spacy_tokens[j]))

            # push all relationships to the database using a single query --> I think this does not work...
            if relationships:
                session.run(
                    """
                    WITH $relationships AS relationships
                    UNWIND relationships AS rel
                    MATCH (a:MLC {id: rel[0]}), (b:MLC {id: rel[1]})
                    MERGE (a)-[r:RELATED_TO]->(b)
                    ON CREATE SET r.strength = 1
                    ON MATCH SET r.strength = r.strength + 1""",
                    relationships=relationships
                )

                print("Extraction created with ID:", extraction_id)

    response = ExtractionResponseModel(
        extraction_id=extraction_id,
        textual_identifier=extraction.textual_identifier if extraction.textual_identifier else None,
        source_id=extraction.source_id if extraction.source_id else None,
        status="initial",
        text=extraction.text,
        sentences=enhanced_sentences,
        entities_recommended=entities_recommended,
        relationships=None,  # Placeholder for relationships
        creation_time=creation_time
    )

    return response

def remove_all_nodes(driver):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")


if __name__ == "__main__":
    # Example usage

    # establish connection with Neo4j
    pass
