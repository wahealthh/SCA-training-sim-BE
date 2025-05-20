from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.schema.case import CaseDetails


class ScoreRequest(BaseModel):
    transcript: str
    case_details: CaseDetails
    user_id: str


class CommentRequest(BaseModel):
    comment: str
    user_id: str

    class Config:
        orm_mode = True