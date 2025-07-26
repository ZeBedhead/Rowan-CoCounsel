from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from orchestrator.orchestrator import run_pipeline
import os
import boto3

app = FastAPI(title="Rowan Orchestration API", version="2.0")

# ===== Orchestrator API =====
class OrchestrationRequest(BaseModel):
    user_input: str
    mode: str = None
    session_id: str = "default"

@app.get("/")
def root():
    return {"status": "ok", "message": "Rowan Orchestration API with Docs Upload is live"}

@app.post("/orchestrate")
def orchestrate(request: OrchestrationRequest):
    try:
        return run_pipeline(request.user_input, request.mode, request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== AWS S3 Setup =====
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION
)

# ===== Document Upload =====
@app.post("/docs/upload")
async def upload_doc(side: str, file: UploadFile = File(...)):
    """
    Upload a document to S3 under a folder named by 'side' (e.g., 'plaintiff' or 'defense').
    """
    try:
        key = f"{side}/{file.filename}"
        s3.upload_fileobj(file.file, AWS_S3_BUCKET, key)
        return {"message": "File uploaded successfully", "s3_key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/docs/signed-url")
async def get_signed_url(key: str):
    """
    Generate a temporary download URL for a file stored in S3.
    """
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_S3_BUCKET, 'Key': key},
            ExpiresIn=3600  # 1 hour
        )
        return {"signed_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
