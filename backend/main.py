"""-FastAPI backend: a small REST API in front of Azure OpenAI.
-The main.py file receives requests and sends answers.
-Run locally to start the backend:    cd backend
                                      uvicorn main:app --reload --port 8000
-API docs:     http://localhost:8000/docs
"""
import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import Settings, get_settings #all settings are in backend/config.py
from llm import LLMClient, LLMError #the Azure OpenAI client is in backend/llm.py

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

settings = get_settings()
#creates the API itself:
app = FastAPI(title="GenAI Interview Starter", version="0.1.0")

#CORS is a security rule that says which websites may call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# TODO(interview): replace this with the prompt for the idea you choose.
SYSTEM_PROMPT = "You are a helpful assistant. Answer clearly and briefly." #The instructions for the AI.

#A request must have a message that isn't empty and isn't too long
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=settings.max_input_chars)

#The answer always has an answer.
class ChatResponse(BaseModel):
    answer: str

#Prepares the connection to the AI. 
#If .env is missing values, it returns a clear error instead of crashing.
def get_llm(s: Settings = Depends(get_settings)) -> LLMClient:
    if not s.llm_configured:
        raise HTTPException(status_code=503, detail="The AI service is not configured on the server.")
    return LLMClient(s)

#a quick "are you alive?" check. It doesn't call the AI, so it's fast and free:
@app.get("/health")
def health(s: Settings = Depends(get_settings)) -> dict:
    """Cheap check for Azure and for the frontend. Never calls the LLM."""
    return {"status": "ok", "llm_configured": s.llm_configured}

#The main endpoint. It takes the message, sends it to the AI through llm.py, and returns the answer. 
@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, llm: LLMClient = Depends(get_llm)) -> ChatResponse:
    try:
        answer = llm.chat(SYSTEM_PROMPT, request.message.strip())
    except LLMError as exc: #If the AI fails, it returns a safe error message.
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return ChatResponse(answer=answer)
