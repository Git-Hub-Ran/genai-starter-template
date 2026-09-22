# <Project name>

<One or two sentences: what the app does and who it is for.>

## How it works

```
Browser -> Streamlit frontend -> FastAPI backend -> Azure OpenAI
```

The frontend only talks to my backend. The backend is the only part that calls the model,
so the API key never reaches the browser.

- `backend/main.py`: the API (`GET /health`, `POST /api/chat`)
- `backend/llm.py`: the only code that calls the model
- `backend/config.py`: reads the settings from `.env`
- `frontend/app.py`: the Streamlit page
- `scripts/check_llm.py`: quick check that the endpoint, key and deployment work
- `tests/`: API tests with a fake model, so they run without Azure

## Environment

- Model: <deployment name and model>
- Hosting: <where the app runs>
- Secrets: <where the API key is stored, locally and on Azure>
- What I used instead of the provided setup, and why: <...>

## Run locally

```
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt -r frontend/requirements.txt -r requirements-dev.txt
copy backend\.env.example backend\.env
python scripts/check_llm.py
pytest
```

On Mac, activate with `source .venv/bin/activate` and copy with `cp`.
Fill in the endpoint, key and deployment in `backend\.env` before running the check.

Then start each part in its own terminal:

```
cd backend
uvicorn main:app --reload --port 8000
```

```
cd frontend
streamlit run app.py
```

The app runs on http://localhost:8501 and the API test page on http://localhost:8000/docs.

## Deploy to Azure

Both parts run as Python web apps on Azure App Service and share one plan.

Backend:

```
cd backend
az webapp up --name <app>-api --resource-group <rg> --plan <app>-plan --runtime "PYTHON:3.12" --sku B1
az webapp config set --name <app>-api --resource-group <rg> --startup-file "gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
az webapp config appsettings set --name <app>-api --resource-group <rg> --settings AZURE_OPENAI_ENDPOINT=<endpoint> AZURE_OPENAI_API_KEY=<key> AZURE_OPENAI_DEPLOYMENT=<deployment> ALLOWED_ORIGINS=https://<app>-web.azurewebsites.net
```

Frontend:

```
cd frontend
az webapp up --name <app>-web --resource-group <rg> --plan <app>-plan --runtime "PYTHON:3.12" --sku B1
az webapp config set --name <app>-web --resource-group <rg> --web-sockets-enabled true --startup-file "python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0"
az webapp config appsettings set --name <app>-web --resource-group <rg> --settings BACKEND_URL=https://<app>-api.azurewebsites.net
```

If something fails, check the logs with `az webapp log tail --name <app>-api --resource-group <rg>`.

## Decisions

- The API key stays on the server. The frontend never sees it.
- All model calls go through `llm.py`, so I can change the model or mock it in tests.
- Users see short error messages. The details (401, 404, 429) go to the logs.
- Input length limit and timeouts, to control cost and keep the app responsive.
- <decisions I made for this project>

## Next steps

<What I would add with more time.>