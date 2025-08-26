# MSCT Project Code

# Prerequirements

This system requires a Neo4j database connection. A open-source community edition is available here: https://neo4j.com/product/community-edition/

Further, the system requires NodeJS to be installed on the device for running the VueJS app locally. NodeJS can be downloaded here: https://nodejs.org/en/download/

## Installation

```bash
# Go to the directory of this repository in your console
cd /path/to/project/directory

# Create a virtual environment for the project
python -m venv .venv

# Activate the virtual environment (Windows version, if you are using a different OS, please check how to activate the virtual environment)
.venv\Scripts\activate

# Install all required python libraries
pip install -r requirements.txt

# Fetch dependencies from the web
python -m spacy download en_core_web_sm

# Change to the frontend directory
cd ./msct-frontend

# Install required node packages using the node package manager
npm install
```

## Run

To run the application locally, three services must be started.

### FastAPI Backend
```bash
# Go to the directory of this repository in your console
cd /path/to/project/directory

# Activate the virtual environment
.venv\Scripts\activate

# Start the backend service
fastapi dev api.py
```

### VueJS Frontend
```bash
# Go to the directory of this repository in your console
cd /path/to/project/directory

# Go into frontend folder
cd ./msct-frontend

# Start VueJS
npm run dev
```

### Neo4j Graph Database

Make sure your neo4j database is started and enter the correct configuration into the .env file. The .env.example file provides the necessary structure for the setup.

# Contact

If you have any questions regarding the code or the thesis, feel free to reach out to lukas.jakober@fhnw.ch. The full PDF of the thesis will follow soon.
