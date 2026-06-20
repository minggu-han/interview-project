"""Pydantic schemas（请求/响应模型）。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------- Auth ----------
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


# ---------- Candidate ----------
class CandidateCreate(BaseModel):
    name: str
    position: str
    skills: list[str] = []
    seniority: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    num_questions: int = 5  # 生成多少道题


class CandidateCreated(BaseModel):
    """创建面试者后返回，含自动生成的登录账号密码。"""
    candidate_id: int
    interview_id: int
    name: str
    position: str
    login_username: str
    login_password: str  # 明文，仅创建时返回一次


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    position: str
    skills: list[str]
    seniority: str | None
    email: str | None
    phone: str | None
    created_at: datetime


# ---------- Question ----------
class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order: int
    skill: str | None
    difficulty: str | None
    content: str
    quality_score: float | None
    quality_passed: bool


# ---------- Interview ----------
class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    status: str
    current_index: int
    created_at: datetime


class InterviewDetail(InterviewOut):
    questions: list[QuestionOut] = []


# ---------- QA ----------
class QARecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int | None
    speaker: str
    text: str
    score: float | None
    created_at: datetime


# ---------- Answer Submit ----------
class AnswerItem(BaseModel):
    question_id: int
    answer: str = ""


class AnswerSubmit(BaseModel):
    answers: list[AnswerItem]


# ---------- Report ----------
class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    interview_id: int
    overall_score: float | None
    per_question: list | None
    strengths: list | None
    weaknesses: list | None
    skill_mastery: dict | None
    summary: str | None
    recommendation: str | None
    created_at: datetime
