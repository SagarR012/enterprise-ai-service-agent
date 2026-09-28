# Enterprise Knowledge Base \& RAG Assistant

An enterprise-grade **Retrieval-Augmented Generation (RAG)** system with **Role-Based Access Control (RBAC)** and **PII guardrails**. Upload documents to workspace-specific knowledge bases and chat with an AI assistant that retrieves relevant information while enforcing access control and masking sensitive data.

\---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        React Frontend                            │
│   Login │ Chat │ Documents │ Admin Dashboard │ User Switcher     │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP (Vite proxy)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python)                      │
│                                                                  │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌────────────────┐  │
│  │  Auth   │  │  Chat    │  │ Documents │  │     Admin      │  │
│  │ (JWT)   │  │  (RAG)   │  │ (Upload)  │  │  (Audit Logs)  │  │
│  └────┬────┘  └────┬─────┘  └─────┬─────┘  └───────┬────────┘  │
│       │            │              │                  │           │
│       ▼            ▼              ▼                  ▼           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Service Layer                         │    │
│  │  auth │ document │ embedding │ pii │ rag │ audit │ feedback │
│  └───────┬──────────┬───────────┬─────┬─────┬───────┬──────┘    │
└──────────┼──────────┼───────────┼─────┼─────┼───────┼───────────┘
           │          │           │     │     │       │
           ▼          ▼           ▼     ▼     ▼       ▼
    ┌────────────┐ ┌────────┐ ┌────────┐ ┌──────────────────────┐
    │ PostgreSQL │ │ Qdrant │ │ Gemini │ │ Microsoft Presidio   │
    │  (Users,   │ │(Vector │ │  (LLM  │ │  (PII Detection \\\&    │
    │  Docs,     │ │ Search │ │  +     │ │   Anonymization)     │
    │  Chats,    │ │  + RBAC│ │  Embed)│ │                      │
    │  Audit)    │ │ Filter)│ │        │ │                      │
    └────────────┘ └────────┘ └────────┘ └──────────────────────┘
```

\---

## Tech Stack

|Layer|Technology|
|-|-|
|**Backend**|Python, FastAPI, SQLAlchemy ORM, Pydantic, Uvicorn|
|**Frontend**|React 19, TypeScript, Vite 8, Tailwind CSS 4, React Router 6|
|**Database**|PostgreSQL 16 (relational data)|
|**Vector Store**|Qdrant v1.12.1 (embeddings + RBAC-filtered search)|
|**LLM**|Google Gemini 3.6 Flash (answer generation)|
|**Embeddings**|Google Gemini gemini-embedding-001 (3072-dim vectors)|
|**PII Guardrails**|Microsoft Presidio (analyzer + anonymizer), spaCy|
|**Auth**|JWT (PyJWT) + bcrypt password hashing|
|**Document Parsing**|pypdf (PDF), built-in (TXT)|
|**Infrastructure**|Docker Compose|

\---

## Key Features

* **Role-Based Access Control** — Documents are tagged with allowed roles. Vector search in Qdrant is filtered by role, so users only retrieve chunks they are authorized to see.
* **PII Detection \& Masking** — Microsoft Presidio scans all document chunks at ingestion time and replaces sensitive entities (emails, phone numbers, SSNs, names, etc.) with `<PII\\\_REDACTED>` placeholders. Privileged roles (`exec\\\_admin`, `legal\\\_admin`) see raw text; others see masked text.
* **RAG-Powered Chat** — User queries are embedded, matched against the vector store with RBAC filtering, and the top chunks are sent to Gemini as context for answer generation.
* **Source Citations** — Every assistant response includes citations with chunk IDs, source document references, and relevance scores.
* **Audit Trail** — Every RAG query is logged with user ID, query text, chunks retrieved, PII masking status, RBAC block status, and role used.
* **Conversation History** — Multi-turn conversations with context carried across messages.
* **Feedback System** — Thumbs up/down on assistant responses for quality tracking.
* **Admin Dashboard** — Real-time stats (total queries, PII redactions, RBAC blocks, documents indexed) and full audit log viewer.
* **Demo User Switching** — Quick-switch between 4 pre-seeded roles to demonstrate access control differences.

\---

## Knowledge Base Architecture

### Ingestion Pipeline

```
Document (TXT/PDF)
    │
    ▼
Text Extraction (pypdf / plain text decode)
    │
    ▼
Chunking (paragraph-boundary splitting, 1000 chars max, 200 char overlap)
    │
    ▼
PII Masking (Presidio detects 12 entity types → replaces with <PII\\\_REDACTED>)
    │
    ▼
Embedding (Gemini gemini-embedding-001 → 3072-dim vectors)
    │
    ▼
Storage
    ├── PostgreSQL: Document metadata + chunk records (raw\\\_text, masked\\\_text, access\\\_roles, contains\\\_pii)
    └── Qdrant: Vector embeddings + payload (text, document\\\_id, chunk\\\_db\\\_id, access\\\_roles)
```

### Retrieval Pipeline

```
User Query
    │
    ▼
Embed Query (Gemini gemini-embedding-001)
    │
    ▼
Qdrant Search (cosine similarity + RBAC filter: access\\\_roles ∩ user\\\_roles ≠ ∅)
    │
    ▼
Context Assembly (privileged roles → raw text; others → masked text)
    │
    ▼
Gemini Generation (system prompt + context + chat history → answer)
    │
    ▼
PII Detection on Answer (Presidio scan)
    │
    ▼
Audit Log Entry (user, query, chunks, pii\\\_masked, rbac\\\_blocked, role)
    │
    ▼
Response to Frontend (answer + citations + metadata)
```

\---

## Dataset

The project ships with 4 sample documents in the `data/` directory to demonstrate workspace isolation and RBAC enforcement:

|File|Workspace|Description|
|-|-|-|
|`executive\\\_q2\\\_review.txt`|Executive|Q2 2026 strategic review — revenue growth, APAC expansion, AI product line, risk factors. Contains PII (executive names, emails).|
|`legal\\\_contract\\\_acme.txt`|Legal|Master Service Agreement with ACME Supply Chain Solutions — pricing, liability, data protection clauses. Contains PII (contact names, emails, phone numbers).|
|`finance\\\_q2\\\_report.txt`|Finance|Q2 2026 financial report — revenue breakdown, expenses, balance sheet, key metrics. Contains PII (CFO name, email).|
|`general\\\_handbook.txt`|General|Employee handbook — work hours, PTO policy, IT security, ethics. Public-safe with no PII.|

Each document is assigned to its respective workspace and can only be retrieved by users with the matching role.

\---

## Roles \& Workspaces

|Role|User|Workspace|Access Level|
|-|-|-|-|
|`exec\\\_admin`|Alice Executive|Executive|Full access — sees raw PII, can upload restricted docs, admin dashboard|
|`legal\\\_admin`|David Legal|Legal|Full access — sees raw PII, can upload restricted docs, admin dashboard|
|`finance\\\_viewer`|Priya Finance|Finance|Read-only — PII masked, cannot upload confidential/restricted|
|`general\\\_viewer`|Karen General|General|Read-only — PII masked, cannot upload confidential/restricted|

\---

## API Endpoints

### Auth (`/api/auth`)

|Method|Endpoint|Description|
|-|-|-|
|POST|`/login`|Email/password login → JWT|
|GET|`/me`|Current user info|
|POST|`/switch-user`|Demo-only: re-issue JWT for any seed user|

### Chat (`/api/chat`)

|Method|Endpoint|Description|
|-|-|-|
|POST|`/`|Send message → RAG-powered answer with citations|
|POST|`/feedback`|Submit thumbs up/down on a response|
|GET|`/conversations`|List user's conversations|
|GET|`/conversations/{id}`|Full message history for a conversation|

### Documents (`/api/documents`)

|Method|Endpoint|Description|
|-|-|-|
|POST|`/upload`|Upload TXT/PDF → extract, chunk, mask PII, embed, store|
|GET|`/`|List documents in user's workspace|
|DELETE|`/{id}`|Delete document + chunks from Postgres and Qdrant|

### Admin (`/api/admin`)

|Method|Endpoint|Description|
|-|-|-|
|GET|`/stats`|Dashboard stats (admin only)|
|GET|`/audit-logs`|All audit logs (admin only)|

### Demo (`/api/demo`)

|Method|Endpoint|Description|
|-|-|-|
|GET|`/users`|List all seed users|

### Health

|Method|Endpoint|Description|
|-|-|-|
|GET|`/api/health`|Health check|

\---

## Getting Started

### Prerequisites

* Python 3.11+
* Node.js 18+
* Docker \& Docker Compose
* Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### 1\. Clone the repository

```bash
git clone https://github.com/Keerthan5R/RBAC.git
cd RBAC
```

### 2\. Start infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL (port 5432) and Qdrant (port 6333).

### 3\. Configure environment

Create a `.env` file in the project root:

```env
# Database
DATABASE\\\_URL=postgresql://kbadmin:kbpass123@localhost:5432/knowledge\\\_base

# Qdrant
QDRANT\\\_HOST=localhost
QDRANT\\\_PORT=6333
QDRANT\\\_COLLECTION=doc\\\_chunks

# JWT
JWT\\\_SECRET=your-secret-key-here
JWT\\\_ALGORITHM=HS256
JWT\\\_EXPIRY\\\_MINUTES=120

# Gemini
GEMINI\\\_API\\\_KEY=your-gemini-api-key-here

# Presidio
PII\\\_PRIVILEGED\\\_ROLES=exec\\\_admin,legal\\\_admin
```

### 4\. Set up the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\\\\Scripts\\\\activate
pip install -r requirements.txt
```

### 5\. Seed the database

```bash
python -m app.seed
```

Creates 4 workspaces and 4 demo users.

### 6\. Ingest sample documents

```bash
python -m app.ingest\\\_samples
```

Processes the 4 sample documents from `data/`, chunks them, masks PII, generates embeddings, and stores them in Qdrant.

### 7\. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

### 8\. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
```

App available at `http://localhost:5173`.

\---

## Demo Accounts

All accounts use password: `password`

|Name|Email|Role|
|-|-|-|
|Alice Executive|alice@enron.com|`exec\\\_admin`|
|David Legal|david@enron.com|`legal\\\_admin`|
|Priya Finance|priya@enron.com|`finance\\\_viewer`|
|Karen General|karen@enron.com|`general\\\_viewer`|

\---

## Use Cases

* **Enterprise Knowledge Management** — Centralized document repository where employees search for information using natural language, with automatic access control enforcement.
* **Compliance \& Legal** — Contracts and legal documents are indexed with PII redaction, ensuring only authorized roles see sensitive details while audit logs track all queries.
* **Financial Analysis** — Finance teams query quarterly reports and financial data; non-finance roles are blocked from accessing confidential financial information.
* **HR \& Onboarding** — Employee handbooks and policies are searchable by all staff, while sensitive HR documents remain restricted.
* **Multi-Tenant SaaS** — Workspace-based isolation demonstrates how a single deployment can serve multiple departments with proper data separation.
* **Regulatory Compliance** — Full audit trail of who queried what, whether PII was involved, and whether access was blocked — essential for GDPR, HIPAA, and SOC 2 compliance.

