from neo4j import GraphDatabase
from database.graph_helper import add_node
from data_processor.data_transformer import get_low_level_concepts, get_medium_level_concepts
import time
import os 
from dotenv import load_dotenv

load_dotenv()

print("Starting Neo4j data processing...")
start = time.time()

# Old code for testing purposes - current main entry point is in api.py


# Neo4j connection details
URI = os.getenv("DB_URI")
AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))

test_sentence = "Bruce Lee (chinesisch 李小龍 / 李小龙, Pinyin Lǐ Xiǎolóng, Jyutping Lei5 Siu2lung4, kantonesisch Lee Siu-lung, * 27. November 1940 in San Francisco; † 20. Juli 1973 in Hongkong; geboren als Lee Jun-fan 李振藩, Lǐ Zhènfán, Jyutping Lei5 Zan3faan4) war ein sinoamerikanischer Schauspieler, Kampfkünstler und Kampfkunst-Ausbilder.[1] Er gilt als Ikone des Martial-Arts-Films und wird von vielen als größter Kampfkünstler des 20. Jahrhunderts angesehen.[2][3] Er entwickelte den Kampfkunststil Jeet Kune Do."

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    print("Connected to Neo4j database.")
    second = time.time()    
    # Add Low-Level Concepts
    llc = get_low_level_concepts(test_sentence)
    for char in llc:
        add_node(driver, char, "LLC")

    # Add Medium-Level Concepts
    mlc = get_medium_level_concepts(test_sentence)
    for word in mlc:
        add_node(driver, word, "MLC")

    for i, word in enumerate(mlc):
        for i in range(i + 1, len(mlc)):
            word2 = mlc[i]
            driver.execute_query(
                "MATCH (a:MLC {id: $word1}), (b:MLC {id: $word2}) "
                "MERGE (a)-[:IN_SENTENCE]->(b)",
                word1=word, word2=word2, database_="neo4j"
            )

    print("Nodes added successfully.")
    end = time.time()
    print(f"Time taken to process data: {end - second:.2f} seconds")

print(f"Total time taken: {end - start:.2f} seconds")