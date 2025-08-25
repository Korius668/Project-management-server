# Project Management Server

## ✨ Features

## 🚀 Quick Start
```
bash
# 1. (Optional) create & activate a virtual environment
python -m venv .venv && source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate                           # Windows PowerShell

# 2. Install the dependencies
pip install -r requirements.txt

# 3. Run the development server (auto-reload enabled)
python ./app/main.py
```

Navigate to <http://localhost:8000/docs> for the interactive Swagger UI 🚀
## 🗂 Project Structure
```
app/
    domain/
    ports/
    adapters/
    usecases/
    api/
    main.py
tests/             
```
---

## 🔌 HTTP API Overview

| Method | Path | Description | Status |
| :-- | :-- | :-- | :-- |
| POST | /auth/create_user | Create a new user | 201/400 |
| POST | /auth/login | Authenticate user and receive JWT token | 200/401 |
|
| GET | /projects/ | Get all accessible projects (owned + shared) | 200 |
| POST | /projects/ | Create project  | 201 |
| GET | /projects/{project_id}/info | Get project details | 200/404 |
| PUT | /projects/{project_id}/info | Update project name and description | 200/404 |
| DELETE | /projects/{project_id} | Delete a project and its documents | 200/404 |
| GET | /projects/{project_id}/documents | List documents in a project | 200/404 |
| POST | /projects/{project_id}/documents | Upload one or multiple documents to a project | 201/404/415 |
| POST | /projects/{project_id}/invite | Grant a user access to a project | 200/400/404 |
|
| GET | /documents/{document_id} | Download a document | 200/404 |
| PUT | /documents/{document_id} | Update document content or metadata | 200/404 |
| DELETE | /documents/{document_id} | Delete a document | 200/404 |

> OpenAPI documentation is served automatically at `/docs` (Swagger UI) and `/redoc`.

## 🧱 Architecture

```mermaid
flowchart TB
  subgraph row3[ ]
    port["Repositories (port)"]
    domain[Domain]
    sql[SQLRepositories]
    usecases[Use-cases]

    usecases -- "(sync)" --> domain -- "(sync)" --> sql -- "implements" --> port <--> usecases
  end
  
  subgraph row1[ ]
    api[FastAPI]
    client[async client / UI]
   
    api -- "calls (async)" --> usecases
    api <-- "HTTP" --> client
  end

style row1 fill:none,stroke:none
style row3 fill:none,stroke:none
```

## Data Base Schema
```mermaid
erDiagram
    USERS {
        UUID id PK
        VARCHAR email "unique"
        VARCHAR name
        VARCHAR password_hash
    }

    PROJECTS {
        UUID id PK
        UUID owner_id FK
        VARCHAR name
        TEXT description
    }

    PROJECT_MEMBERSIPS {
        UUID project_id FK
        UUID user_id FK
        VARCHAR role "enum: owner, editor, viewer"
    }

    DOCUMENTS {
        UUID id PK
        UUID project_id FK
        VARCHAR filename
        VARCHAR content_type
        BIGINT size_bytes
        VARCHAR storage_path "object store path or key"
        JSON metadata
    }

    USERS ||--o{ PROJECTS : owns
    PROJECTS ||--o{ PROJECT_MEMBERSHIPS : "has members"
    USERS ||--o{ PROJECT_MEMBERSHIPS : "member of"
    PROJECTS ||--o{ DOCUMENTS : "contains"
    USERS ||--o{ DOCUMENTS : "uploaded by"
```