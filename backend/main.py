import os
from typing import List

from src.backend.services.celery_service import celery_transcribe_audio, celery
from src.backend.services.sqlite_db_service import Transcription, get_transcripts
from celery.result import AsyncResult

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "/app/temp"
os.makedirs(TEMP_DIR, exist_ok=True)


@app.get("/health")
async def health_check():
    # whisper_status = "ready" if transcriber else "not loaded"
    whisper_status = "ready"
    test_task = celery.send_task("celery.ping")
    celery_status = AsyncResult(test_task.id).state

    try:
        redis_status = "connected" if celery.control.inspect().ping() else "unreachable"
    except Exception:
        redis_status = "unreachable"

    return {
        "whisper_model": whisper_status,
        "celery_worker": celery_status,
        "redis": redis_status,
    }


@app.post("/transcribe")
async def add_transcribe_job(files: List[UploadFile]):
    task_ids = []

    for file in files:
        file_path = os.path.join(TEMP_DIR, file.filename)
        print(file_path)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        task = celery_transcribe_audio.delay(file_path)
        task_ids.append({"file": file.filename, "task_id": task.id})

    return {"message": "Transcription job started", "jobs": task_ids}


@app.get("/transcriptions", response_model=List[Transcription])
def get_all_transcriptions():
    return get_transcripts()


@app.post("/search", response_model=List[Transcription])
async def get_transcription_by_name(file_name: str):
    transcript_metadata = get_transcripts(file_name)
    loc_transcript = transcript_metadata.loc_transcript

    if not os.path.exists(loc_transcript):
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")
    return FileResponse(loc_transcript)
