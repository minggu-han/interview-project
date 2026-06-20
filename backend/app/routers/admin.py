"""管理员路由：添加面试者、生成账号、查看列表与报告。"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import SessionLocal, get_db
from app.deps import require_admin
from app.models import Candidate, Interview, InterviewStatus, Question, Report, Role, User
from app.schemas import (
    CandidateCreate,
    CandidateCreated,
    CandidateOut,
    InterviewDetail,
    ReportOut,
)
from app.security import generate_password, hash_password
from app.services.interview_service import generate_questions_for_interview

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


async def _generate_questions_task(interview_id: int, num_questions: int):
    """后台任务：调用生成/质检 agent。使用独立 session。"""
    logger.info("[后台] 开始生成题库 interview_id=%s 题量=%s", interview_id, num_questions)
    try:
        async with SessionLocal() as db:
            interview = (
                await db.execute(select(Interview).where(Interview.id == interview_id))
            ).scalar_one()
            interview._num_questions = num_questions  # 传给 service
            await generate_questions_for_interview(db, interview)
        logger.info("[后台] 题库生成完成 interview_id=%s", interview_id)
    except Exception:
        # 后台任务异常需打印，否则会被框架静默吞掉，导致题库一直生成不出来
        logger.exception("[后台] 题库生成失败 interview_id=%s", interview_id)


@router.post("/candidates", response_model=CandidateCreated)
async def create_candidate(
    payload: CandidateCreate,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """添加面试者：创建登录账号(自动生成密码) + 候选人档案 + 面试，并后台生成题库。"""
    logger.info("添加面试者：姓名=%s 岗位=%s 技术=%s", payload.name, payload.position, payload.skills)
    # 生成唯一登录名
    base_login = (payload.email or payload.name).split("@")[0]
    login = base_login
    suffix = 1
    while (await db.execute(select(User).where(User.username == login))).scalar_one_or_none():
        login = f"{base_login}{suffix}"
        suffix += 1

    raw_password = generate_password()
    user = User(username=login, hashed_password=hash_password(raw_password), role=Role.candidate)
    db.add(user)
    await db.flush()

    candidate = Candidate(
        user_id=user.id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        position=payload.position,
        skills=payload.skills,
        seniority=payload.seniority,
        notes=payload.notes,
    )
    db.add(candidate)
    await db.flush()

    interview = Interview(candidate_id=candidate.id, status=InterviewStatus.pending)
    db.add(interview)
    await db.commit()
    await db.refresh(interview)

    # 后台生成题库（题库生成 + 质检 agent）
    background.add_task(_generate_questions_task, interview.id, payload.num_questions)
    logger.info(
        "面试者已创建 candidate_id=%s interview_id=%s 登录名=%s",
        candidate.id, interview.id, login,
    )

    return CandidateCreated(
        candidate_id=candidate.id,
        interview_id=interview.id,
        name=candidate.name,
        position=candidate.position,
        login_username=login,
        login_password=raw_password,
    )


@router.get("/candidates", response_model=list[CandidateOut])
async def list_candidates(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Candidate).order_by(Candidate.id.desc()))).scalars().all()
    return rows


@router.get("/candidates/{candidate_id}/interview", response_model=InterviewDetail)
async def candidate_interview(candidate_id: int, db: AsyncSession = Depends(get_db)):
    interview = (
        await db.execute(
            select(Interview)
            .where(Interview.candidate_id == candidate_id)
            .options(selectinload(Interview.questions))
            .order_by(Interview.id.desc())
        )
    ).scalars().first()
    if not interview:
        raise HTTPException(404, "未找到面试")
    return interview


@router.get("/interviews/{interview_id}/report", response_model=ReportOut)
async def get_report(interview_id: int, db: AsyncSession = Depends(get_db)):
    report = (
        await db.execute(select(Report).where(Report.interview_id == interview_id))
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(404, "报告尚未生成")
    return report


@router.post("/candidates/{candidate_id}/reset-password")
async def reset_password(candidate_id: int, db: AsyncSession = Depends(get_db)):
    candidate = (
        await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    ).scalar_one_or_none()
    if not candidate:
        raise HTTPException(404, "未找到面试者")
    user = (await db.execute(select(User).where(User.id == candidate.user_id))).scalar_one()
    new_pw = generate_password()
    user.hashed_password = hash_password(new_pw)
    await db.commit()
    return {"login_username": user.username, "login_password": new_pw}
