from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Session, create_engine, select
from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
import time
import logging

logging.basicConfig(level=logging.INFO)


class TranscribeJobStatus(Enum):
    IN_PROCESS = 0
    COMPLETED = 1
    FAILED = 2


DATABASE_URL = "sqlite:////app/database.db"
engine = create_engine(DATABASE_URL)


class TranscriptionJob(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    transcription_id: Optional[int] = Field(
        default=None, foreign_key="transcription.id"
    )
    loc_transcript: str
    timestamp_job_started: int
    timestamp_job_status_update: int
    job_status: TranscribeJobStatus
    transcription: Optional["Transcription"] = Relationship(back_populates="jobs")


class Transcription(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    init_file_name: str
    final_file_name: str
    loc_transcript: str
    timestamp_audio_uploaded: int
    timestamp_audio_transcribed: int
    jobs: List[TranscriptionJob] = Relationship(
        back_populates="transcription", sa_relationship_kwargs={"lazy": "subquery"}
    )


SQLModel.metadata.create_all(engine)


def upsert_transcription_job(
    loc_transcript: str,
    timestamp_job_status_updated: int,
    job_status: TranscribeJobStatus,
    timestamp_job_started: Optional[int] = None,
    job_id: Optional[int] = None,
    transcription_id: Optional[int] = None,
):
    with Session(engine) as session:
        try:
            if job_id:
                logging.info(f"Attempting to update TranscriptionJob with id: {job_id}")
                transcription_job = session.exec(
                    select(TranscriptionJob).where(TranscriptionJob.id == job_id)
                ).first()

                if not transcription_job:
                    error_message = f"TranscriptionJob with id {job_id} not found"
                    logging.error(error_message)
                    raise ValueError(error_message)

                transcription_job.loc_transcript = loc_transcript
                if timestamp_job_started:
                    transcription_job.timestamp_job_started = timestamp_job_started
                transcription_job.timestamp_job_status_update = (
                    timestamp_job_status_updated
                )
                transcription_job.job_status = job_status
                if transcription_id:
                    transcription_job.transcription_id = transcription_id
                logging.info(f"Updated TranscriptionJob: {transcription_job}")
            else:
                if not timestamp_job_started:
                    timestamp_job_started = int(time.time())

                transcription_job = TranscriptionJob(
                    loc_transcript=loc_transcript,
                    timestamp_job_started=timestamp_job_started,
                    timestamp_job_status_update=timestamp_job_status_updated,
                    job_status=job_status,
                    transcription_id=transcription_id,
                )
                session.add(transcription_job)
                logging.info(f"Adding new TranscriptionJob: {transcription_job}")

            session.commit()
            session.refresh(transcription_job)
            logging.info(
                f"Committed and refreshed TranscriptionJob with id: {transcription_job.id}"
            )
            return transcription_job.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemyError in upsert_transcription_job: {e}")
            raise e
        except ValueError as e:
            session.rollback()
            logging.error(f"ValueError in upsert_transcription_job: {e}")
            raise e


def insert_transcript(
    init_file_name: str,
    final_file_name: str,
    loc_transcript: str,
    timestamp_audio_uploaded: int,
    timestamp_audio_transcribed: int,
):
    with Session(engine) as session:
        try:
            logging.info(f"Inserting transcript with init_file_name: {init_file_name}")
            transcript = Transcription(
                init_file_name=init_file_name,
                final_file_name=final_file_name,
                loc_transcript=loc_transcript,
                timestamp_audio_uploaded=timestamp_audio_uploaded,
                timestamp_audio_transcribed=timestamp_audio_transcribed,
            )

            session.add(transcript)
            session.commit()
            logging.info(f"Transcript inserted with id: {transcript.id}")

            return transcript.id

        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Error inserting transcript: {e}")
            raise e


def get_transcripts(transcript_file_name: Optional[str] = None):
    with Session(engine) as session:
        try:
            query = select(Transcription)
            if transcript_file_name:
                query = query.where(
                    Transcription.final_file_name == transcript_file_name
                )
            results = session.exec(query).all()
            logging.info(f"Querying transcripts.  Results: {results}")
            return results
        except SQLAlchemyError as e:
            logging.error(f"Error in get_transcripts: {e}")
            raise e


def get_transcript_by_id(transcript_id: int):
    with Session(engine) as session:
        try:
            logging.info(f"Getting transcript by ID: {transcript_id}")
            transcript = session.exec(
                select(Transcription).where(Transcription.id == transcript_id)
            ).first()
            logging.info(f"Got transcript: {transcript}")
            return transcript
        except SQLAlchemyError as e:
            logging.error(f"Error in get_transcript_by_id: {e}")
            raise e


def get_job_by_id(job_id: int):
    with Session(engine) as session:
        try:
            logging.info(f"Getting job by ID: {job_id}")
            job = session.exec(
                select(TranscriptionJob).where(TranscriptionJob.id == job_id)
            ).first()
            logging.info(f"Got job: {job}")
            return job
        except SQLAlchemyError as e:
            logging.error(f"Error in get_job_by_id: {e}")
            raise e
