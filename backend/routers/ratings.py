"""评分相关路由"""
from typing import List
from fastapi import APIRouter, HTTPException
from database import get_db
from models import RatingCreate

router = APIRouter(prefix="/api/ratings", tags=["ratings"])


@router.post("/batch")
def submit_ratings_batch(data: List[RatingCreate]):
    """批量提交菜品评分（同一设备每天仅限一次）"""
    if not data:
        raise HTTPException(status_code=400, detail="评分数据为空")

    device_id = data[0].device_id
    menu_date = data[0].menu_date

    conn = get_db()

    # 检查该设备今日是否已提交过
    cur = conn.execute(
        "SELECT COUNT(*) as cnt FROM dish_ratings WHERE device_id = ? AND menu_date = ? AND device_id != ''",
        (device_id, menu_date)
    )
    if cur.fetchone()["cnt"] > 0:
        conn.close()
        raise HTTPException(status_code=409, detail="今日已提交过评分，每人每天仅限一次")

    for item in data:
        conn.execute(
            "INSERT INTO dish_ratings (dish_name, menu_date, score, nickname, device_id) VALUES (?,?,?,?,?)",
            (item.dish_name, item.menu_date, item.score, item.nickname, item.device_id)
        )
    conn.commit()
    conn.close()
    return {"message": f"已提交 {len(data)} 条评分"}


@router.get("/check/{menu_date}")
def check_submitted(menu_date: str, device_id: str = ""):
    """检查该设备今日是否已提交过评分"""
    if not device_id:
        return {"submitted": False}
    conn = get_db()
    cur = conn.execute(
        "SELECT COUNT(*) as cnt FROM dish_ratings WHERE device_id = ? AND menu_date = ? AND device_id != ''",
        (device_id, menu_date)
    )
    submitted = cur.fetchone()["cnt"] > 0
    conn.close()
    return {"submitted": submitted}


@router.get("/{menu_date}")
def get_ratings(menu_date: str):
    """获取某日所有菜品的评分汇总"""
    conn = get_db()
    cur = conn.execute(
        """SELECT dish_name,
                  ROUND(AVG(score), 1) as avg_score,
                  COUNT(*) as count
           FROM dish_ratings
           WHERE menu_date = ?
           GROUP BY dish_name""",
        (menu_date,)
    )
    rows = cur.fetchall()
    conn.close()
    return [{"dish_name": r["dish_name"], "avg_score": r["avg_score"], "count": r["count"]} for r in rows]
