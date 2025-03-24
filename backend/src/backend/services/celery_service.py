from src.backend.services.transcribe_service import transcribe_audio_file
from celery import Celery

celery = Celery("tasks", broker="redis://redis:6379/0", backend="redis://redis:6379/0")


@celery.task
def celery_transcribe_audio(file_path):
    print(file_path)
    transcribe_audio_file(file_path)
