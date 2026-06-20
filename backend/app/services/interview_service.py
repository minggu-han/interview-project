"""业务编排服务：把多 agent 与数据库串起来。"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents import (
    AnalystAgent,
    QualityCheckerAgent,
    QuestionGeneratorAgent,
    ScorerAgent,
    SummaryAgent,
)
from app.models import (
    Candidate,
    Interview,
    InterviewStatus,
    QARecord,
    Question,
    Report,
)

logger = logging.getLogger(__name__)


async def generate_questions_for_interview(db: AsyncSession, interview: Interview) -> None:
    """生成 agent + 质检 agent：为面试生成题库并落库。"""
    candidate = (
        await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    ).scalar_one()

    gen = QuestionGeneratorAgent()
    checker = QualityCheckerAgent()

    num = getattr(interview, "_num_questions", 5)
    logger.info("[题库] 生成 agent 开始：岗位=%s 题量=%s", candidate.position, num)
    raw_questions = await gen.generate(
        position=candidate.position,
        skills=candidate.skills or [],
        seniority=candidate.seniority,
        num_questions=num,
    )
    logger.info("[题库] 生成 agent 产出 %s 道题，开始逐题质检", len(raw_questions))

    order = 0
    for q in raw_questions:
        try:
            quality = await checker.check(q, candidate.position)
        except Exception:
            # 质检调用失败（网关错误等）不应让整个题库生成中断，放行该题
            logger.warning("[题库] 质检调用失败，放行该题：%s", q.get("skill"))
            quality = {"quality_score": 0, "passed": True, "feedback": "质检调用失败，已放行"}
        logger.info(
            "[题库] 质检 技术点=%s 分数=%s 通过=%s",
            q.get("skill"), quality["quality_score"], quality["passed"],
        )
        # 质检不通过的题目跳过，保证题库质量
        if not quality["passed"]:
            continue
        db.add(
            Question(
                interview_id=interview.id,
                order=order,
                skill=q.get("skill"),
                difficulty=q.get("difficulty"),
                content=q.get("content", ""),
                reference_answer=q.get("reference_answer"),
                quality_score=quality["quality_score"],
                quality_passed=True,
                quality_feedback=quality["feedback"],
            )
        )
        order += 1

    # 兜底：若全部被过滤，至少保留原始题目
    if order == 0:
        logger.warning("[题库] 所有题目质检均未通过，启用兜底保留原始题目")
        for i, q in enumerate(raw_questions):
            db.add(
                Question(
                    interview_id=interview.id,
                    order=i,
                    skill=q.get("skill"),
                    difficulty=q.get("difficulty"),
                    content=q.get("content", ""),
                    reference_answer=q.get("reference_answer"),
                    quality_score=0,
                    quality_passed=False,
                    quality_feedback="质检未通过（兜底保留）",
                )
            )

    await db.commit()
    logger.info("[题库] 入库完成，最终有效题目数=%s", order if order else len(raw_questions))


async def build_report(db: AsyncSession, interview: Interview) -> Report:
    """分析 agent + 总结 agent：生成最终报告。"""
    interview = (
        await db.execute(
            select(Interview)
            .where(Interview.id == interview.id)
            .options(selectinload(Interview.questions), selectinload(Interview.candidate))
        )
    ).scalar_one()

    # 取每题候选人的评分记录
    records = (
        await db.execute(
            select(QARecord).where(
                QARecord.interview_id == interview.id, QARecord.speaker == "candidate"
            )
        )
    ).scalars().all()
    rec_by_q = {r.question_id: r for r in records}

    qa_items = []
    per_question = []
    scores = []
    for q in interview.questions:
        rec = rec_by_q.get(q.id)
        score = rec.score if rec else 0
        scores.append(score or 0)
        qa_items.append(
            {
                "skill": q.skill,
                "question": q.content,
                "answer": rec.text if rec else "",
                "score": score,
                "comment": (rec.score_detail or {}).get("comment", "") if rec else "",
            }
        )
        per_question.append(
            {"question": q.content, "skill": q.skill, "score": score,
             "answer": rec.text if rec else "",
             "comment": (rec.score_detail or {}).get("comment", "") if rec else ""}
        )

    overall = round(sum(scores) / len(scores), 1) if scores else 0
    logger.info("[报告] 综合得分=%s，开始分析 agent", overall)

    analyst = AnalystAgent()
    summarizer = SummaryAgent()
    candidate = interview.candidate
    analysis = await analyst.analyze(candidate.position, candidate.skills or [], qa_items)
    logger.info("[报告] 分析完成，开始总结 agent")
    summary = await summarizer.summarize(
        candidate.position, overall, analysis["strengths"],
        analysis["weaknesses"], analysis["skill_mastery"],
    )
    logger.info("[报告] 总结完成，写入数据库")

    report = (
        await db.execute(select(Report).where(Report.interview_id == interview.id))
    ).scalar_one_or_none()
    if report is None:
        report = Report(interview_id=interview.id)
        db.add(report)

    report.overall_score = overall
    report.per_question = per_question
    report.strengths = analysis["strengths"]
    report.weaknesses = analysis["weaknesses"]
    report.skill_mastery = analysis["skill_mastery"]
    report.summary = summary["summary"]
    report.recommendation = summary["recommendation"]

    interview.status = InterviewStatus.reported
    interview.finished_at = interview.finished_at or datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(report)
    return report


async def process_submission(interview_id: int, answers: dict[int, str]) -> None:
    """后台静默处理：对面试者一次性提交的全部答案逐题评分，并生成报告。

    面试者无感知——提交时答案已落库并返回“面试完成”，本函数在后台运行。
    使用独立 session（由 BackgroundTasks 调度，脱离请求生命周期）。
    """
    from app.database import SessionLocal

    scorer = ScorerAgent()

    logger.info("[评分] 开始后台处理 interview_id=%s", interview_id)
    try:
        async with SessionLocal() as db:
            interview = (
                await db.execute(
                    select(Interview)
                    .where(Interview.id == interview_id)
                    .options(selectinload(Interview.questions))
                )
            ).scalar_one()

            # 取提交时已落库的候选人原始回答记录
            records = (
                await db.execute(
                    select(QARecord).where(
                        QARecord.interview_id == interview_id,
                        QARecord.speaker == "candidate",
                    )
                )
            ).scalars().all()
            rec_by_q = {r.question_id: r for r in records}

            # 逐题：评分 agent 打分，更新到已有记录（回答原文照录，不润色）
            for idx, q in enumerate(interview.questions, 1):
                raw = answers.get(q.id, "")
                try:
                    result = await scorer.score(q.content, q.reference_answer, raw)
                    logger.info("[评分] 第 %s 题 得分=%s", idx, result["overall"])
                except Exception:
                    # 单题评分失败不应中断整份报告
                    logger.warning("[评分] 第 %s 题评分调用失败，记 0 分", idx)
                    result = {"overall": 0, "dimensions": {}, "comment": "评分调用失败"}

                rec = rec_by_q.get(q.id)
                if rec is None:
                    rec = QARecord(
                        interview_id=interview_id, question_id=q.id, speaker="candidate", text=""
                    )
                    db.add(rec)
                rec.text = raw  # 原封不动记录面试者的回答
                rec.score = result["overall"]
                rec.score_detail = result

            await db.commit()

            # 分析 agent + 总结 agent
            await build_report(db, interview)
        logger.info("[评分] 后台处理完成，报告已生成 interview_id=%s", interview_id)
    except Exception:
        logger.exception("[评分] 后台报告生成失败 interview_id=%s", interview_id)


