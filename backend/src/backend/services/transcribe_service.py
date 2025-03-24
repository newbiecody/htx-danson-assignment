import os
import time
from backend.services.sqlite_db_service import upsert_transcription_job
from backend.utils.file_utils import is_audio_file
from fastapi import HTTPException
import logging
from transformers import pipeline
import torch
from backend.enum import TranscribeJobStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
COMPLETED_TRANSCRIPTS_DIR = "completed_transcripts"


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
    try:
        if not is_audio_file(file_path):
            raise HTTPException(status_code=422)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        reserved_transcript_loc = os.path.join(COMPLETED_TRANSCRIPTS_DIR, file_name)
        time_of_job_start = int(time.time()) * 1000  # In milliseconds

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

            with open(reserved_transcript_loc, "w") as file:
                file.write(transcription)

            time_of_job_completion = int(time.time()) * 1000
            upsert_transcription_job(
                job_id=job_id,
                loc_transcript=reserved_transcript_loc,
                timestamp_job_started=time_of_job_start,
                timestamp_job_status_updated=time_of_job_completion,
                job_status=TranscribeJobStatus.COMPLETED,
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
