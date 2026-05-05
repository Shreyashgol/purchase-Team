# SAP Purchase Agents

This repository contains a small multi-agent SAP Business One purchasing workspace. Each document agent runs as its own FastAPI service, and the Purchase Team Streamlit app routes natural-language requests to the correct backend.

## Current Structure

```text
sap/
├── .env.example
├── README.md
├── shared/
│   ├── env.py
│   └── db/
│       └── runtime.py
├── Purchase Order/
│   ├── .env.example
│   ├── README.md
│   ├── requirements.txt
│   ├── streamlit_app.py
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── agents/
│       ├── api/
│       ├── crud/
│       ├── db/
│       ├── model/
│       ├── operations/
│       └── schema/
├── AP Invoice/
│   ├── .env.example
│   ├── README.md
│   ├── requirements.txt
│   ├── streamlit_app.py
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── agents/
│       ├── api/
│       ├── crud/
│       ├── db/
│       ├── model/
│       ├── operations/
│       └── schema/
├── Purchase Return/
│   ├── .env.example
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── agents/
│       ├── api/
│       ├── crud/
│       ├── db/
│       ├── model/
│       ├── operations/
│       └── schema/
└── Purchase Team/
    ├── .env.example
    ├── README.md
    ├── streamlit_app.py
    └── app/
        ├── config.py
        ├── agents/
        ├── model/
        └── schema/
```

## Services

| Service | Port | Purpose |
| --- | ---: | --- |
| Purchase Order API | `8002` | Create, update, fetch, close, and cancel purchase orders |
| AP Invoice API | `8003` | Create, update, fetch, close, cancel, and reopen AP invoices |
| Purchase Return API | `8004` | Create, update, fetch, close, cancel, and reopen purchase returns |
| Purchase Team UI | `8501` | Streamlit router for all purchase document agents |

## Environment Configuration

Use the root `.env` for shared configuration. Agent-specific `.env` files are optional and should only be used when one agent needs a different value.

Create your real environment file from the example:

```bash
cp .env.example .env
```

Required values:

```bash
SAP_AGENTS_DATABASE_URL=postgresql://username:password@host:5432/sap_agents_db?sslmode=require
SAP_BASE_URL=http://localhost:50000/b1s/v1
SAP_USERNAME=manager
SAP_PASSWORD=password
SAP_COMPANYDB=SBODEMOUS
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=120
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
SQL_QUERY_TIMEOUT=30
```

The `config.py` file in every agent now follows the same pattern:

1. Adds the repository root to `sys.path`.
2. Loads the root `.env`.
3. Loads the agent-local `.env` if present.
4. Exposes constants such as `SAP_BASE_URL`, `DATABASE_CONNECTION_STRING`, `JWT_SECRET`, `GROQ_API_KEY`, and `SQL_QUERY_TIMEOUT`.

## Setup

The existing virtual environment is `myvenv`. If you need to recreate it:

```bash
python -m venv myvenv
./myvenv/bin/python -m pip install -r "Purchase Order/requirements.txt"
./myvenv/bin/python -m pip install -r "AP Invoice/requirements.txt"
```

## Start The Backends

Open four terminals from the repository root.

Terminal 1:

```bash
cd "Purchase Order"
../myvenv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

Terminal 2:

```bash
cd "AP Invoice"
../myvenv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8003
```

Terminal 3:

```bash
cd "Purchase Return"
../myvenv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8004
```

Terminal 4:

```bash
cd "Purchase Team"
../myvenv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Then open:

```text
http://127.0.0.1:8501
```

## Get A JWT Token

Use any backend login endpoint. The default demo credentials are `user1` and `pass123456`.

```bash
curl -X POST "http://127.0.0.1:8002/login?username=user1&password=pass123456"
```

Copy the returned `access_token` into the Purchase Team UI sidebar.

## Smoke Tests

Check that each backend is alive:

```bash
curl http://127.0.0.1:8002/
curl http://127.0.0.1:8003/
curl http://127.0.0.1:8004/
```

Example routed request in the Streamlit UI:

```text
Show me the latest 5 purchase orders
```

Example direct API request:

```bash
TOKEN="paste-token-here"

curl -X POST "http://127.0.0.1:8002/purchase-orders/parse-and-execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Show me the latest 5 purchase orders"}'
```

## Development Notes

- Keep secrets in `.env`; do not commit them.
- Keep generated files such as `__pycache__/`, `*.pyc`, `.DS_Store`, and virtual environments out of git.
- Agent submodules now live under `app/agents/`, not `app/agents.py/`.
- Use `SAP_AGENTS_DATABASE_URL` as the shared database variable for all agents. Legacy `DATABASE_CONNECTION_STRING` and `DATABASE_URL` still work through the shared runtime fallback.
- Run without `--reload` if local file watcher permissions cause startup issues.
