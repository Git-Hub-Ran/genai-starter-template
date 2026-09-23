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
Replace `<app>` with a short unique name, `<rg>` with the resource group,
and `<region>` with the region of my Azure OpenAI resource.

Deploy early: the first deploy of each app takes 5 to 10 minutes.

First, log in and find the resource group:

```
az login
az group list --output table
```


If the login fails with a multi-factor message, run it again with the tenant id
from the error: `az login --tenant <tenant-id>`.
If no resource group is assigned to me, create one:
`az group create --name <rg> --location <region>`

Backend:

```
cd backend
az webapp up --name <app>-api --resource-group <rg> --plan <app>-plan --runtime "PYTHON:3.12" --sku B1 --location <region>
az webapp config set --name <app>-api --resource-group <rg> --startup-file "gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000"
az webapp config appsettings set --name <app>-api --resource-group <rg> --settings AZURE_OPENAI_ENDPOINT=<endpoint> AZURE_OPENAI_API_KEY=<key> AZURE_OPENAI_DEPLOYMENT=<deployment> AZURE_OPENAI_API_VERSION=<api-version> ALLOWED_ORIGINS=https://<app>-web.azurewebsites.net
```


Check: `https://<app>-api.azurewebsites.net/health` should show `"llm_configured": true`.

Frontend:

```
cd ../frontend
az webapp up --name <app>-web --resource-group <rg> --plan <app>-plan --runtime "PYTHON:3.12" --sku B1 --location <region>
az webapp config set --name <app>-web --resource-group <rg> --web-sockets-enabled true --startup-file "python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0"
az webapp config appsettings set --name <app>-web --resource-group <rg> --settings BACKEND_URL=https://<app>-api.azurewebsites.net
az webapp restart --name <app>-web --resource-group <rg>
```


Then open `https://<app>-web.azurewebsites.net`.

Good to know:

- The first deploy runs before the startup command is set, so it can end with
  "Site failed to start" after 10 minutes. That is expected: set the startup
  command, restart, and it works.
- `az webapp up` is deprecated but still works. The replacement is
  `az webapp create` plus `az webapp deploy`.
- `az webapp up` saves defaults in a `.azure` folder inside the folder it runs
  in, so later commands there can be shorter. It is in `.gitignore`.
- Logs: `az webapp log tail --name <app>-api --resource-group <rg>`
- Delete everything when finished (only a group I created myself):
  `az group delete --name <rg> --yes --no-wait`
  

  
## Decisions

- The API key stays on the server. The frontend never sees it.
- All model calls go through `llm.py`, so I can change the model or mock it in tests.
- Users see short error messages. The details (401, 404, 429) go to the logs.
- Input length limit and timeouts, to control cost and keep the app responsive.
- <decisions I made for this project>

## Next steps

<What I would add with more time.>