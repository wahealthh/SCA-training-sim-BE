from pydantic import BaseModel
from typing import Optional


class CaseDetails(BaseModel):
    name: Optional[str] = None
    age: int
    presenting: str
    context: str


class ScoreRequest(BaseModel):
    transcript: str
    case_details: CaseDetails
    user_id: str

class CommentRequest(BaseModel):
    comment: str
    user_id: int