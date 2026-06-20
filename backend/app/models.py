"""数据库模型。

角色说明：
  - User: 系统账号，role 区分 admin / candidate
  - Candidate: 面试者档案（岗位、所需技能等），关联一个 candidate 角色的 User
  - Interview: 一场面试，关联 Candidate
  - Question: 题库题目（由生成 agent 产出、质检 agent 校验）
  - QARecord: 面试过程中每一句问答的实时记录
  - Report: 面试结束后由评分/分析/总结 agent 产出的报告
"""
import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(str, enum.Enum):
    admin = "admin"
    candidate = "candidate"


class InterviewStatus(str, enum.Enum):
    pending = "pending"        # 已创建，未开始
    in_progress = "in_progress"  # 进行中
    finished = "finished"      # 答题完成
    reported = "reported"      # 报告已生成


class User(Base):
    __tablename__ = "interview_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.candidate)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate: Mapped["Candidate"] = relationship(back_populates="user", uselist=False)


class Candidate(Base):
    __tablename__ = "interview_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("interview_users.id"))
    name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # 面试岗位与所需技术
    position: Mapped[str] = mapped_column(String(128))
    skills: Mapped[list] = mapped_column(JSON, default=list)  # 岗位所需技术列表
    seniority: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 初/中/高级
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="candidate")
    interviews: Mapped[list["Interview"]] = relationship(back_populates="candidate")


class Interview(Base):
    __tablename__ = "interview_interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("interview_candidates.id"))
    status: Mapped[InterviewStatus] = mapped_column(Enum(InterviewStatus), default=InterviewStatus.pending)
    current_index: Mapped[int] = mapped_column(Integer, default=0)  # 当前进行到第几题
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    candidate: Mapped["Candidate"] = relationship(back_populates="interviews")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="interview", order_by="Question.order", cascade="all, delete-orphan"
    )
    qa_records: Mapped[list["QARecord"]] = relationship(
        back_populates="interview", cascade="all, delete-orphan"
    )
    report: Mapped["Report"] = relationship(
        back_populates="interview", uselist=False, cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interview_interviews.id"))
    order: Mapped[int] = mapped_column(Integer, default=0)
    skill: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 考察的技术点
    difficulty: Mapped[str | None] = mapped_column(String(16), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 质检 agent 结果
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    interview: Mapped["Interview"] = relationship(back_populates="questions")


class QARecord(Base):
    """面试过程中每一句问答的实时记录（记录 agent / WebSocket 产出）。"""
    __tablename__ = "interview_qa_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interview_interviews.id"))
    question_id: Mapped[int | None] = mapped_column(ForeignKey("interview_questions.id"), nullable=True)
    speaker: Mapped[str] = mapped_column(String(16))  # "interviewer" | "candidate"
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # 评分 agent 针对某题完整回答的结果
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    interview: Mapped["Interview"] = relationship(back_populates="qa_records")


class Report(Base):
    __tablename__ = "interview_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interview_interviews.id"))
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 各题评分明细
    per_question: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # 优缺点分析 agent
    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list | None] = mapped_column(JSON, nullable=True)
    skill_mastery: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 各技术点掌握度
    # 总结 agent
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)  # 录用建议
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    interview: Mapped["Interview"] = relationship(back_populates="report")
