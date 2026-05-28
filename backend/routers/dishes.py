"""菜品查询接口（公开）"""
from fastapi import APIRouter, Query
from database import get_db

router = APIRouter(prefix="/api/dishes", tags=["dishes"])


@router.get("")
def list_dishes(category: str = Query(None)):
    conn = get_db()
    if category:
        cur = conn.execute(
            "SELECT * FROM dishes WHERE enabled = 1 AND category = ? ORDER BY id", (category,)
        )
    else:
        cur = conn.execute("SELECT * FROM dishes WHERE enabled = 1 ORDER BY category, id")
    dishes = [dict(row) for row in cur.fetchall()]
    conn.close()
    return dishes


@router.get("/{dish_id}")
def get_dish(dish_id: int):
    conn = get_db()
    cur = conn.execute("SELECT * FROM dishes WHERE id = ?", (dish_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"detail": "菜品不存在"}, 404
    return dict(row)
