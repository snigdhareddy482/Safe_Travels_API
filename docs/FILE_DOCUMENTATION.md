# SafeTravels API - File Documentation

> Detailed explanation of each file in the project

---

## 📁 Root Level Files

### `MASTER_PLAN.md`
**Purpose:** Project roadmap and architecture overview

**What it does:**
- Defines the RAG-powered architecture
- 8-week sprint plan
- Tech stack decisions
- Deliverables timeline

---

### `CLAUDE.md`
**Purpose:** AI assistant rules file

**What it does:**
- Guidelines for AI tools when working on this project
- Documents RAG architecture
- Coding standards and constraints

---

### `README.md`
**Purpose:** Project documentation for GitHub

**What it does:**
- Quick start guide
- API endpoints list
- Project structure

---

### `requirements.txt`
**Purpose:** Python dependencies

**Key packages:**
| Package | Purpose |
|---------|---------|
| `fastapi` | Web API framework |
| `langchain` | RAG orchestration |
| `chromadb` | Vector database |
| `openai` | LLM for synthesis |
| `sentence-transformers` | Text embeddings |

---

## 📁 `safetravels/app/` - Core Application

### `main.py`
**Purpose:** FastAPI application entry point

**What it does:**
- Creates the FastAPI app
- Configures CORS middleware
- Includes API router

**How to run:**
```bash
cd safetravels
uvicorn app.main:app --reload
```

---

## 📁 `safetravels/core/` - The Engine Room

### 1. `app_settings.py` (The Rulebook)
- **One-Liner:** Defines the **laws** of the app (Risk Multipliers) and loads **secrets** from the Safe.

### 2. `data_loader.py` (The Supply Line)
- **One-Liner:** Loads all raw JSON data (Crime, Parking, Red Zones) and effectively feeds the entire system.


### `app_settings.py` (The Main Control Panel)
**Purpose:** Application settings
- **Role:** Centralized App Settings.
- **What it does:**
    - Loads `OPENAI_API_KEY`, `DATABASE_URL`, etc.
    - Defines the 15-Factor Risk Model constants.
    - *Analogy:* The settings menu on your phone where you turn on Wifi and Bluetooth.


---

## 📁 `safetravels/config/` - The Vendor Rolodex

This folder handles specific 3rd-party API connection details.

### 1. `external_services.py` (The Rolodex)
- **Role:** Information for External Services.
- **What it does:**
    - Stores the exact URLs for Google Maps (Geocoding, Places, Routes).
    - Stores the complex setup for Azure OpenAI (Endpoints, Deployments).
    - *Analogy:* A business card holder. When the Agents need to call Google, they look up the phone number (URL) here.



---

## 📁 `safetravels/api/` - The API Layer (Web Interface)

This folder builds the web server. Here is the plain English explanation of how these 4 files work together:

### 1. `main.py` (The Front Door)
- **Role:** Entry Point / Reception Desk.
- **What it does:**
    - Creates the FastAPI app.
    - Sets up the "Welcome" page (`/` and `/health`).
    - Tells the server: *"If anyone asks for `/api/v1/something`, send them to the `routes.py` file."*

### 2. `routes.py` (The Traffic Controller)
- **Role:** Endpoint Definitions / Departments.
- **What it does:**
    - Defines the actual "buttons" (endpoints) the user can press.
    - Lists URLs like:
        - `/assess-risk` (Department of Risk)
        - `/analyze-route` (Department of Routing)
        - `/safe-stops` (Department of Parking)
    - When a request comes in, it calls the **Agents** to do the actual work.

### 3. `schemas.py` (The Forms)
- **Role:** Data Validation / Paperwork.
- **What it does:**
    - Defines exactly what data is required.
    - Enforces rules like: *"You MUST provide a Latitude between -90 and 90."*
    - If you send bad data (e.g., `latitude: "banana"`), it rejects it immediately so the Agents don't crash.

### 4. `__init__.py` (The Badge)
- **Role:** Package Marker.
- **What it does:**
    - An empty file.
    - Acts as an ID Badge that says "We are official employees."
    - Tells Python: *"The files in this folder are related. Treat them as a package called `api`."*

### 5. `README.md` (The Signpost)
- **Role:** Directory Documentation.
- **What it does:**
    - A markdown file for developers.
    - *Analogy:* Generally a signpost explaining what the Department does (e.g. "This folder contains the API layer").

### 🔄 How They Flow Together
1.  **User** knocks on the door (`main.py`).
2.  **Receptionist** (`main.py`) checks the map and sends them to the right department (`routes.py`).
3.  **Department** (`routes.py`) hands them a form (`schemas.py`) to fill out.
4.  Once the form is valid, the **Department** calls the **Agents** (Planner/Analyst) to solve the problem.

---

## 📁 `safetravels/agents/` - The Swarm (The Workers)

This folder contains the AI agents that actually solve the problems.

### 1. `planner.py` (The Logistics Coordinator)
- **Role:** Route Generator / Math Wizard.
- **What it does:**
    - Draws the lines on the map.
    - Uses **Geometry** (not AI) to check if a route hits a "Red Zone" box.
    - *Analogy:* The guy with the map and compass who says "We can go way A, B, or C."

### 2. `analyst.py` (The Risk Expert)
- **Role:** Decision Maker / Detective.
- **What it does:**
    - Looks at the Planner's options.
    - Uses **AI** to read crime reports and decide which route is actually safest.
    - *Analogy:* The seasoned detective who says "Way A is shorter, but Way B is safer because there's a riot on Way A."

### 3. `critic.py` (The Auditor)
- **Role:** Quality Control / Teacher.
- **What it does:**
    - Checks the Analyst's homework.
    - "Did you cite your sources?" "Did you actually pick the safest one?"
    - *Analogy:* The strict teacher who marks your paper with a red pen before you can turn it in.

### 4. `memory.py` (The Historian)
- **Role:** Personalization / Database.
- **What it does:**
    - Remembers what the driver likes.
    - "Driver #42 hates unlit parking lots."
    - *Analogy:* The elephant that never forgets.

### 5. `state.py` (The Clipboard)
- **Role:** Shared Memory.
- **What it does:**
    - Defines the form that gets passed around between agents.
    - *Analogy:* The physical clipboard that the Planner hands to the Analyst, who hands it to the Critic.

### 6. `multi_agent_graph.py` (The Conductor)
- **Role:** Boss / Orchestrator.
- **What it does:**
    - Tells the agents when to work.
    - "Planner, you go first. Analyst, you go next. Critic, if you reject it, send it back to Analyst."
    - *Analogy:* The Traffic Cop directing the flow of work.

### 7. `graph.py` (The Researcher)
- **Role:** Librarian.
- **What it does:**
    - A specialized worker who just looks up answers to questions in the vector database.
    - *Analogy:* The librarian running to the stacks to find a book on "Cargo Theft in Dallas."

### 8. `__init__.py` (The Badge)
- **Role:** Package Marker.
- **What it does:**
    - Empty file that makes the folder importable.
    - *Analogy:* The "Authorized Personnel Only" sign on the door.

### 9. `README.md` (The Manual)
- **Role:** Developer Documentation.
- **What it does:**
    - Explains to other coders how to use the agents.
    - Contains usage examples (like how to run `planner.py`).
    - *Analogy:* The instruction manual left in the breakroom.

---

## 📁 `safetravels/rag/` - The Brain (Knowledge & Logic)

This folder handles "Retrieval Augmented Generation" (RAG). It makes the AI smart by giving it access to real data.

### 1. `vector_store.py` (The Librarian)
- **Role:** Keeper of the Books.
- **What it does:**
    - Taking new information (like a crime report) and filing it away (`add_documents`).
    - Finding the 5 most relevant documents when asked a question (`similarity_search`).
    - *Analogy:* The librarian who knows exactly which shelf the book on "Texas Highway Safety" is on.

### 2. `chain.py` (The Author)
- **Role:** Synthesis Engine.
- **What it does:**
    - Takes the User's question + The Librarian's books.
    - Sends them to OpenAI with instructions: "Read these books and answer the user's question."
    - *Analogy:* A student writing a research paper based on sources found in the library.

### 3. `__init__.py` (The Badge)
- **Role:** Package Marker.
- **What it does:** Makes the folder a Python package.

### 4. `README.md` (The Manual)
- **Role:** Developer Guide.
- **What it does:** Explains how to use the RAG tools.

---

## 📁 `safetravels/chroma_db/` - The Long-Term Memory (Storage)

### 1. `chroma.sqlite3` (The Card Catalog)
- **Role:** Database Index.
- **What it does:** A real SQL database that keeps track of where everything is stored. Do not touch this file directly.

### 2. `UUID Folders` (The Bookshelves)
- **Role:** Raw Data Storage.
- **What it does:** Folders named like `4e94bf4b...` contain the actual data for one specific Collection (e.g., "crime_data").
- **Inside the UUID Folder (The Blueprints):**

    #### A. `data_level0.bin` (The Filing Cabinet)
    - **What it is:** The heavy storage file.
    - **Analogy:** The physical cabinet holding the "resumes" (vectors). If you read this, you read *everything* (slow).

    #### B. `link_lists.bin` (The Sticky Notes)
    - **What it is:** The shortcut map.
    - **Analogy:** Notes saying *"If you like Alice, go look at Bob next."* It lets the AI jump between similar items instantly without scanning the whole cabinet.

    #### C. `header.bin` (The Label)
    - **What it is:** The metadata.
    - **Analogy:** The label on the drawer saying *"Start searching at Resume #1."*

    #### D. `length.bin` (The Counter)
    - **What it is:** Memory management list.
    - **Analogy:** A boring list telling the computer how much space to reserve for each item's connections.

---

## 📁 Generated Files (Ignore These)

### 1. `__pycache__` / `*.pyc` (Speed Translations)
- **Role:** Python's "Speed Translation" files.
- **What it does:**
    - Computers read 1s and 0s, not English.
    - When you run code, Python translates `planner.py` into machine code `planner.pyc`.
    - **Do not edit.** You can delete them anytime; Python will just recreate them next time you run the app.

---

## 🔄 How Files Connect

```
User Request
     │
     ▼
routes.py (API endpoint)
     │
     ▼
chain.py (RAG chain)
     │
     ├── embeddings.py (embed query)
     │
     ├── vector_store.py (retrieve docs)
     │
     └── LLM (synthesize answer)
     │
     ▼
Response (risk + explanation + sources)
```

---

## ✅ What's Working Now

| Component | Status |
|-----------|--------|
| FastAPI app | ✅ Runs |
| All endpoints | ✅ Return mock data |
| RAG module structure | ✅ Created |

## ❌ What Needs Implementation

| Component | Status |
|-----------|--------|
| ChromaDB integration | ❌ TODO |
| SBERT embeddings | ❌ TODO |
| LangChain chain | ❌ TODO |
| Data ingestion | ❌ TODO |
| Dashboard | ❌ TODO |
