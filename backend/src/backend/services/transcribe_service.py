import os
import time
from src.backend.services.sqlite_db_service import (
    upsert_transcription_job,
    TranscribeJobStatus,
    insert_transcript,
)
from src.backend.utils.file_utils import is_audio_file
from fastapi import HTTPException
import logging
from transformers import pipeline
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
COMPLETED_TRANSCRIPTS_DIR = "/app/completed_transcripts"
os.makedirs(COMPLETED_TRANSCRIPTS_DIR, exist_ok=True)


def initialize_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        logger.info(f"Initializing Whisper model on {device}")
        transcriber = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-tiny",
            device=device,
        )
        return transcriber
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {str(e)}")
        return None


def transcribe_audio_file(file_path):
    file_name = os.path.basename(file_path)
    reserved_transcript_loc = os.path.join(COMPLETED_TRANSCRIPTS_DIR, file_name)
    os.makedirs(COMPLETED_TRANSCRIPTS_DIR, exist_ok=True)

    time_of_job_start = int(time.time()) * 1000  # In milliseconds
    try:
        if not is_audio_file(file_path):
            raise HTTPException(status_code=422)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        transcriber = initialize_model()
        if transcriber is None:
            upsert_transcription_job(
                loc_transcript=reserved_transcript_loc,
                timestamp_job_started=time_of_job_start,
                timestamp_job_status_updated=time_of_job_start,
                job_status=TranscribeJobStatus.FAILED,
            )
            raise RuntimeError("Whisper model failed to initialize")
        else:
            job_id = upsert_transcription_job(
                loc_transcript=reserved_transcript_loc,
                timestamp_job_started=time_of_job_start,
                timestamp_job_status_updated=time_of_job_start,
                job_status=TranscribeJobStatus.IN_PROCESS,
            )

            transcription = transcriber(file_path)

            transcription_text = transcription["text"]

            with open(reserved_transcript_loc, "w") as file:
                file.write(transcription_text)

            time_of_job_completion = int(time.time()) * 1000
            res = upsert_transcription_job(
                job_id=job_id,
                loc_transcript=reserved_transcript_loc,
                timestamp_job_started=time_of_job_start,
                timestamp_job_status_updated=time_of_job_completion,
                job_status=TranscribeJobStatus.COMPLETED,
            )

            insert_transcript(
                init_file_name=file_name,
                final_file_name=file_name,
                loc_transcript=reserved_transcript_loc,
                timestamp_audio_uploaded=time_of_job_start,
                timestamp_audio_transcribed=time_of_job_completion,
            )

    except Exception as e:
        upsert_transcription_job(
            loc_transcript=reserved_transcript_loc,
            timestamp_job_started=time_of_job_start,
            timestamp_job_status_updated=time_of_job_start,
            job_status=TranscribeJobStatus.FAILED,
        )
        raise e
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to remove temporary file: {str(e)}")
