from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from orchestrator.orchestrator import run_pipeline

app = FastAPI(title="Rowan Orchestration API", version="1.0")

# Request schema
class OrchestrationRequest(BaseModel):
    user_input: str
    mode: str = None
    session_id: str = "default"

@app.get("/")
def root():
    return {"status": "ok", "message": "Rowan Orchestration API is live"}

@app.post("/orchestrate")
def orchestrate(request: OrchestrationRequest):
    try:
        result = run_pipeline(request.user_input, request.mode, request.session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
