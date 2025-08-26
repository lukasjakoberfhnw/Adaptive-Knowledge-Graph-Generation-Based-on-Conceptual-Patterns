import fastapi
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.middleware import cors
from neo4j import GraphDatabase
from models.extraction_models import Entity, ExtractionModel, ExtractionResponseModel, ExtractionCreateModel
from models.entity_models import Entity as EntityModelForGeneration, EntityLinkingCreate, RelationshipCreateModel
from data_processor.data_transformer import get_english_stopwords, get_hlc_entities, get_spacy_sentences, get_spacy_entities, get_spacy_tokens
from database.graph_helper import add_node
import uuid
from datetime import datetime
from helper import extraction_create, extraction_create_calculate_in_ram, remove_all_nodes
from helper_test import extraction_create_optimized, extraction_create_optimized_nltk
import time
import spacy

from pypdf import PdfReader

# get router from /routes/extractions.py and add it to the app
from routes.extractions import router as extractions_router
from routes.hlcs import router as hlcs_router
from routes.mlcs import router as mlcs_router
from routes.entities import router as entities_router
from routes.relationships import router as relationships_router
from routes.workspace import router as workspace_router
from routes.functions import router as functions_router

import dotenv
import os

dotenv.load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # neo4j driver initialization

    db_uri = os.getenv("DB_URI")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    print(db_uri)
    print(db_user)
    print(db_password)

    driver = GraphDatabase.driver(
        db_uri,
        auth=(db_user, db_password)
    )
    spacy_context = spacy.load("en_core_web_sm")
    app.state.driver = driver
    app.state.spacy_context = spacy_context
    try:
        yield
    finally:
        # Close the driver when the app is shutting down
        await driver.close()

app = FastAPI(lifespan=lifespan)

# cors 
origins = [
    "http://localhost:5173",  # Local development
]

app.add_middleware(
    cors.CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extractions_router, tags=["extractions"])
app.include_router(hlcs_router, tags=["hlcs"])
app.include_router(mlcs_router, tags=["mlcs"])
app.include_router(entities_router, tags=["entities"])
app.include_router(relationships_router, tags=["relationships"])
app.include_router(workspace_router, tags=["workspace"])
app.include_router(functions_router, tags=["functions"])

# idk if this will be necessary in the future:

@app.get("/sources")
async def get_sources():
    """
    Retrieve all sources.
    """
    # Placeholder for source retrieval logic
    sources = [
        {"id": "source_1", "name": "Source One", "creation_time": "2023-10-02T12:00:00Z"},
        {"id": "source_2", "name": "Source Two", "creation_time": "2023-10-01T12:00:00Z"},
        {"id": "source_3", "name": "Source Three", "creation_time": "2023-10-02T12:00:00Z"}
    ]
    return sources

@app.get("/sources/{source_id}")
async def get_source(source_id: str):
    """
    Retrieve a specific source by its ID.
    """
    # Placeholder for actual source retrieval logic
    if source_id == "source_1":
        source = {"id": "source_1", "name": "Source One", "creation_time": "2023-10-02T12:00:00Z"}
        return source
    else:
        raise HTTPException(status_code=404, detail="Source not found")
    
@app.get("/sources")
async def get_all_sources():
    """
    Retrieve all sources.
    """
    # Placeholder for actual source retrieval logic
    sources = [
        {"id": "source_1", "name": "Source One"},
        {"id": "source_2", "name": "Source Two"},
        {"id": "source_3", "name": "Source Three"}
    ]
    return sources