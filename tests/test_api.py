"""API tests. 
This code runs automatic checks that the backend works correctly.
No Azure, internet, or a key needed: the LLM is replaced with a fake.
Run from the project root:  pytest
"""
import sys
from pathlib import Path

#tells Python where to find main.py and llm.py (because the tests are in a different folder)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from llm import LLMError  # noqa: E402

#pretends to be the real LLMClient.
#It has the same chat method, but it doesn't call Azure.
#It returns an answer we choose, or raises an error we choose.
class FakeLLM:
    def __init__(self, answer: str = "Hello!", error: LLMError | None = None):
        self.answer = answer
        self.error = error

    def chat(self, system_prompt: str, user_message: str) -> str:
        if self.error:
            raise self.error
        return self.answer

#create a TestClient (a fake browser) that sends requests to my API without starting uvicorn.
@pytest.fixture
def client():
    yield TestClient(main.app) #give the client to the test, and when the test finishes, continue to the next line.
    main.app.dependency_overrides.clear()#It removes the fake after each test, so one test can't affect another.

#answers 200 (OK) with "status": "ok".
def test_health(client):
    resp = client.get("/health")
    #assert checks that something is true. If it's not, the test fails and shows you where.
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

#It tells FastAPI: "when /api/chat asks for get_llm, give it the fake instead.
def test_chat_returns_answer(client):
    main.app.dependency_overrides[main.get_llm] = lambda: FakeLLM("Hi there")
    resp = client.post("/api/chat", json={"message": "hello"})
    assert resp.status_code == 200
    assert resp.json() == {"answer": "Hi there"}

#an empty message gets 422 (invalid input):
def test_chat_rejects_empty_message(client):
    main.app.dependency_overrides[main.get_llm] = lambda: FakeLLM()
    resp = client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 422

#the fake says "busy", and the API returns 503 with the safe message:
def test_chat_hides_llm_error_details(client):
    error = LLMError("The AI service is busy. Try again in a moment.", 503)
    main.app.dependency_overrides[main.get_llm] = lambda: FakeLLM(error=error)
    resp = client.post("/api/chat", json={"message": "hello"})
    assert resp.status_code == 503
    assert resp.json()["detail"] == "The AI service is busy. Try again in a moment."
