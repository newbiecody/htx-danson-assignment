from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Transcription(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    loc_transcription: str | None = Field(default=None, primary_key=True)
    audio_file_name: str | None = Field(default=None, primary_key=True)
    loc_audio: str | None = Field(default=None, primary_key=True)
