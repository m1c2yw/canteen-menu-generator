"""投诉建议接口（公开）"""
from fastapi import APIRouter, HTTPException, Query
from database import get_db
from models import FeedbackCreate

router = APIRouter(prefix="/api/feedbacks", tags=["feedbacks"])


@router.post("")
def submit_feedback(body: FeedbackCreate):
    conn = get_db()
    conn.execute(
        "INSERT INTO feedbacks (nickname, content, type) VALUES (?,?,?)",
        (body.nickname, body.content, body.type)
    )
    conn.commit()
    feedback_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"id": feedback_id, "message": "提交成功，感谢您的反馈！"}


@router.get("")
def list_feedbacks(nickname: str = Query(None)):
    conn = get_db()
    if not nickname:
        raise HTTPException(status_code=400, detail="请提供昵称查询")
    cur = conn.execute(
        "SELECT * FROM feedbacks WHERE nickname = ? ORDER BY created_at DESC", (nickname,)
    )
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return items
