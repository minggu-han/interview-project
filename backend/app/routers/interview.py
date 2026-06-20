"""面试者路由：查看自己的面试题、提交答案。

面试者不再查看报告——提交后仅返回“面试完成”，
评分/分析/总结由后台静默处理（管理员可看报告）。
"""
from datetime import datetime, timezone
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Candidate, Interview, InterviewStatus, QARecord, User
from app.schemas import AnswerSubmit, InterviewDetail
from app.services.interview_service import process_submission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interview", tags=["interview"])


async def _my_interview(db: AsyncSession, user: User) -> Interview:
    candidate = (
        await db.execute(select(Candidate).where(Candidate.user_id == user.id))
    ).scalar_one_or_none()
    if not candidate:
        raise HTTPException(403, "当前账号不是面试者")
    interview = (
        await db.execute(
            select(Interview)
            .where(Interview.candidate_id == candidate.id)
            .options(selectinload(Interview.questions))
            .order_by(Interview.id.desc())
        )
    ).scalars().first()
    if not interview:
        raise HTTPException(404, "暂无面试安排")
    return interview


@router.get("/my", response_model=InterviewDetail)
async def my_interview(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """面试者获取自己的全部题目（一次性展示）。"""
    return await _my_interview(db, user)


@router.post("/submit")
async def submit_answers(
    payload: AnswerSubmit,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """一次性提交全部答案：落库后立即返回“面试完成”，后台静默评分。"""
    interview = await _my_interview(db, user)
    logger.info("面试者提交答案：用户=%s interview_id=%s", user.username, interview.id)

    if interview.status == InterviewStatus.reported:
        raise HTTPException(400, "本场面试已结束")

    valid_qids = {q.id for q in interview.questions}
    answers: dict[int, str] = {}
    for item in payload.answers:
        if item.question_id in valid_qids:
            answers[item.question_id] = (item.answer or "").strip()

    # 保存面试者每题原始回答到数据库
    for qid, text in answers.items():
        db.add(
            QARecord(
                interview_id=interview.id,
                question_id=qid,
                speaker="candidate",
                text=text,
            )
        )

    interview.status = InterviewStatus.finished
    interview.started_at = interview.started_at or datetime.now(timezone.utc)
    interview.finished_at = datetime.now(timezone.utc)
    await db.commit()

    # 后台静默处理：评分 + 分析 + 总结（面试者无感知）
    background.add_task(process_submission, interview.id, answers)
    logger.info("已保存 %s 题答案，触发后台评分 interview_id=%s", len(answers), interview.id)

    return {"status": "finished", "message": "面试完成"}
