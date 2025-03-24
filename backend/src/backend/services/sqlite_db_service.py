from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Session, create_engine, select
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
import time

# Define enum here to avoid circular imports
class TranscribeJobStatus(str, Enum):
    PENDING = "pending"
    IN_PROCESS = "in_process"
    COMPLETED = "completed"
    FAILED = "failed"

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL)


# Define models with proper relationships
class TranscriptionJob(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    transcription_id: Optional[int] = Field(default=None, foreign_key="transcription.id")
    loc_transcript: str
    timestamp_job_started: int
    timestamp_job_status_update: int
    job_status: TranscribeJobStatus
    
    # Define relationship to parent Transcription
    transcription: Optional["Transcription"] = Relationship(back_populates="jobs")


class Transcription(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    init_file_name: str
    final_file_name: str
    loc_transcript: str
    timestamp_audio_uploaded: int
    timestamp_audio_transcribed: int
    
    # Define relationship to child TranscriptionJobs
    jobs: List[TranscriptionJob] = Relationship(
        back_populates="transcription", sa_relationship_kwargs={"lazy": "subquery"}
    )


# Create tables
SQLModel.metadata.create_all(engine)


def upsert_transcription_job(
    loc_transcript: str,
    timestamp_job_status_updated: int,
    job_status: TranscribeJobStatus,
    timestamp_job_started: Optional[int] = None,
    job_id: Optional[int] = None,
    transcription_id: Optional[int] = None,
) -> int:
    """
    Create or update a transcription job
    Returns the job ID
    """
    with Session(engine) as session:
        try:
            if job_id:
                # Update existing job
                transcription_job = session.exec(
                    select(TranscriptionJob).where(TranscriptionJob.id == job_id)
                ).first()
                
                if not transcription_job:
                    raise ValueError(f"TranscriptionJob with id {job_id} not found")
                
                transcription_job.loc_transcript = loc_transcript
                if timestamp_job_started:
                    transcription_job.timestamp_job_started = timestamp_job_started
                transcription_job.timestamp_job_status_update = timestamp_job_status_updated
                transcription_job.job_status = job_status
                if transcription_id:
                    transcription_job.transcription_id = transcription_id
            else:
                # Create new job
                if not timestamp_job_started:
                    timestamp_job_started = int(time.time())
                    
                transcription_job = TranscriptionJob(
                    loc_transcript=loc_transcript,
                    timestamp_job_started=timestamp_job_started,
                    timestamp_job_status_update=timestamp_job_status_updated,
                    job_status=job_status,
                    transcription_id=transcription_id
                )
                session.add(transcription_job)
            
            session.commit()
            session.refresh(transcription_job)
            return transcription_job.id
        except SQLAlchemyError as e:
            session.rollback()
            raise e


def insert_transcript(
    job_id: int,
    init_file_name: str,
    final_file_name: str,
    loc_transcript: str,
    timestamp_audio_uploaded: int,
    timestamp_audio_transcribed: int,
) -> int:
    """
    Insert a transcript and update its associated job
    Returns the transcript ID
    """
    with Session(engine) as session:
        try:
            # Begin transaction
            transcript = Transcription(
                init_file_name=init_file_name,
                final_file_name=final_file_name,
                loc_transcript=loc_transcript,
                timestamp_audio_uploaded=timestamp_audio_uploaded,
                timestamp_audio_transcribed=timestamp_audio_transcribed,
            )
            session.add(transcript)
            session.flush()  # Get the ID without committing
            
            # Get the job and associate it with the transcript
            job = session.exec(
                select(TranscriptionJob).where(TranscriptionJob.id == job_id)
            ).first()
            
            if job:
                job.transcription_id = transcript.id
                job.job_status = TranscribeJobStatus.COMPLETED
                job.timestamp_job_status_update = timestamp_audio_transcribed
            
            # Commit everything in a single transaction
            session.commit()
            return transcript.id
        except SQLAlchemyError as e:
            session.rollback()
            # Update job status to failed in a separate transaction
            try:
                upsert_transcription_job(
                    job_id=job_id,
                    loc_transcript=loc_transcript,
                    timestamp_job_status_updated=timestamp_audio_transcribed,
                    job_status=TranscribeJobStatus.FAILED,
                )
            except Exception:
                # Log this but don't let it overshadow the original error
                pass
            raise e


def get_transcripts(transcript_file_name: Optional[str] = None) -> List[Transcription]:
    """
    Get transcripts, optionally filtered by file name
    """
    with Session(engine) as session:
        query = select(Transcription)
        if transcript_file_name:
            query = query.where(Transcription.final_file_name == transcript_file_name)
        results = session.exec(query).all()
        return results


def get_transcript_by_id(transcript_id: int) -> Optional[Transcription]:
    """
    Get a transcript by ID
    """
    with Session(engine) as session:
        transcript = session.exec(
            select(Transcription).where(Transcription.id == transcript_id)
        ).first()
        return transcript


def get_job_by_id(job_id: int) -> Optional[TranscriptionJob]:
    """
    Get a transcription job by ID
    """
    with Session(engine) as session:
        job = session.exec(
            select(TranscriptionJob).where(TranscriptionJob.id == job_id)
        ).first()
        return job