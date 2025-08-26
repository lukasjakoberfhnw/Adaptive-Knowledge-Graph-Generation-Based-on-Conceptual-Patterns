from neo4j import GraphDatabase, RoutingControl
import os
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("DB_URI")
AUTH = (os.getenv("DB_USER"), os.getenv("DB_PASSWORD"))

# LLC = Low-Level Concept
# MLC = Medium-Level Concept
# HLC = High-Level Concept
# E = Entity

def add_node(driver, node_value, concept):
    """Available concepts: LLC, MLC, HLC, Entity"""

    # if concept not in ["LLC", "MLC", "HLC", "Entity"]:
    #     raise ValueError("Invalid concept. Choose from: LLC, MLC, HLC, Entity")

    if concept not in ["MLC"]:
        raise ValueError("Invalid concept. Choose from: MLC")

    driver.execute_query(
        "MERGE (a:" + concept + " {text: $value, id: $value}) " \
        "ON CREATE SET a.count = 1 " \
        "ON MATCH SET a.count = a.count + 1",
        value=node_value, database_="neo4j",
    )

def add_nodes(driver, node_values, concept):
    """
        Only available for MLC to create multiple in one query for optimization purposes.
    """

    driver.execute_query(
        "UNWIND $values AS value "
        "MERGE (a:" + concept + " {text: value, id: value}) "
        "ON CREATE SET a.count = 1 "
        "ON MATCH SET a.count = a.count + 1",
        values=node_values, database_="neo4j",
    )