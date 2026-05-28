"""管理后台接口（需 JWT 认证）"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from auth import get_current_user, verify_password, create_token
from models import (
    LoginRequest, DishCreate, DishUpdate, ReplaceItem,
    FeedbackReply, HolidayCreate,
)
from generator import generate_weekly_menu, get_monday, format_date

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─── 登录 ───
@router.post("/login")
def login(body: LoginRequest):
    conn = get_db()
    cur = conn.execute("SELECT * FROM admins WHERE username = ?", (body.username,))
    admin = cur.fetchone()
    conn.close()
    if not admin or not verify_password(body.password, admin['password_hash']):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(body.username)
    return {"access_token": token, "token_type": "bearer"}


# ─── 菜品管理 ───
@router.get("/dishes")
def admin_list_dishes(category: str = None, user=Depends(get_current_user)):
    conn = get_db()
    if category:
        cur = conn.execute(
            "SELECT * FROM dishes WHERE category = ? ORDER BY id", (category,)
        )
    else:
        cur = conn.execute("SELECT * FROM dishes ORDER BY category, id")
    dishes = [dict(row) for row in cur.fetchall()]
    conn.close()
    return dishes


@router.post("/dishes")
def admin_create_dish(body: DishCreate, user=Depends(get_current_user)):
    conn = get_db()
    conn.execute(
        "INSERT INTO dishes (name, category, cuisine, protein) VALUES (?,?,?,?)",
        (body.name, body.category, body.cuisine, body.protein)
    )
    conn.commit()
    dish_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"id": dish_id, "message": "菜品已添加"}


@router.put("/dishes/{dish_id}")
def admin_update_dish(dish_id: int, body: DishUpdate, user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.execute("SELECT * FROM dishes WHERE id = ?", (dish_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="菜品不存在")

    updates = {}
    for key in ('name', 'category', 'cuisine', 'protein', 'enabled'):
        val = getattr(body, key, None)
        if val is not None:
            updates[key] = val

    if updates:
        set_clause = ', '.join(f"{k} = ?" for k in updates)
        conn.execute(f"UPDATE dishes SET {set_clause} WHERE id = ?", (*updates.values(), dish_id))
        conn.commit()
    conn.close()
    return {"message": "菜品已更新"}


@router.delete("/dishes/{dish_id}")
def admin_delete_dish(dish_id: int, user=Depends(get_current_user)):
    conn = get_db()
    conn.execute("UPDATE dishes SET enabled = 0 WHERE id = ?", (dish_id,))
    conn.commit()
    conn.close()
    return {"message": "菜品已禁用"}


# ─── 菜单管理 ───
@router.post("/menus/generate")
def admin_generate_menu(week_key: str = None, force: bool = True, user=Depends(get_current_user)):
    if week_key:
        monday = date.fromisoformat(week_key)
    else:
        monday = get_monday(date.today())
    result = generate_weekly_menu(monday, force=force)
    if result is None:
        # 返回已有菜单
        conn = get_db()
        cur = conn.execute(
            "SELECT * FROM weekly_menus WHERE week_key = ?", (format_date(monday),)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "week_key": row['week_key'],
                "repeat_rate": row['repeat_rate'],
                "message": "该周菜单已存在，使用 force=true 强制重新生成",
            }
        raise HTTPException(status_code=500, detail="菜单生成失败")
    return result


@router.put("/menus/replace")
def admin_replace_item(body: ReplaceItem, user=Depends(get_current_user)):
    """替换菜单中的某道菜"""
    conn = get_db()

    # 查找待替换的 item
    cur = conn.execute(
        "SELECT mi.*, wm.week_key FROM menu_items mi JOIN weekly_menus wm ON mi.menu_id = wm.id WHERE wm.id = ? AND mi.day_date = ? AND mi.slot = ?",
        (body.menu_id, body.day_date, body.slot)
    )
    old_item = cur.fetchone()
    if not old_item:
        conn.close()
        raise HTTPException(status_code=404, detail="菜单项不存在")

    # 获取新菜品信息
    cur = conn.execute("SELECT * FROM dishes WHERE id = ? AND enabled = 1", (body.new_dish_id,))
    new_dish = cur.fetchone()
    if not new_dish:
        conn.close()
        raise HTTPException(status_code=404, detail="菜品不存在")

    old_name = old_item['dish_name']
    new_name = new_dish['name']

    # 检查当天是否已有同名菜品
    cur = conn.execute(
        "SELECT id FROM menu_items WHERE menu_id = ? AND day_date = ? AND dish_name = ?",
        (body.menu_id, body.day_date, new_name)
    )
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="当天已有该菜品")

    # 更新 menu_items
    conn.execute(
        "UPDATE menu_items SET dish_id = ?, dish_name = ?, category = ?, cuisine = ?, protein = ? WHERE id = ?",
        (body.new_dish_id, new_name, new_dish['category'], new_dish['cuisine'], new_dish['protein'], old_item['id'])
    )

    # 更新 dish_history
    conn.execute(
        "UPDATE dish_history SET dish_name = ? WHERE week_key = ? AND dish_name = ?",
        (new_name, old_item['week_key'], old_name)
    )

    conn.commit()
    conn.close()
    return {"message": f"已替换：{old_name} → {new_name}"}


# ─── 投诉建议管理 ───
@router.get("/feedbacks")
def admin_list_feedbacks(status: str = None, user=Depends(get_current_user)):
    conn = get_db()
    if status:
        cur = conn.execute(
            "SELECT * FROM feedbacks WHERE status = ? ORDER BY created_at DESC", (status,)
        )
    else:
        cur = conn.execute("SELECT * FROM feedbacks ORDER BY created_at DESC")
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return items


@router.put("/feedbacks/{feedback_id}/reply")
def admin_reply_feedback(feedback_id: int, body: FeedbackReply, user=Depends(get_current_user)):
    conn = get_db()
    conn.execute(
        "UPDATE feedbacks SET reply = ?, status = 'replied' WHERE id = ?",
        (body.reply, feedback_id)
    )
    conn.commit()
    conn.close()
    return {"message": "已回复"}


# ─── 节假日管理 ───
@router.get("/holidays")
def admin_list_holidays(user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.execute("SELECT * FROM holidays ORDER BY date")
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return items


@router.post("/holidays")
def admin_add_holiday(body: HolidayCreate, user=Depends(get_current_user)):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO holidays (date, name) VALUES (?,?)", (body.date, body.name))
    conn.commit()
    conn.close()
    return {"message": "节假日已添加"}


@router.delete("/holidays/{date_str}")
def admin_delete_holiday(date_str: str, user=Depends(get_current_user)):
    conn = get_db()
    conn.execute("DELETE FROM holidays WHERE date = ?", (date_str,))
    conn.commit()
    conn.close()
    return {"message": "节假日已删除"}


# ─── 每日主食管理 ───
@router.get("/daily-staples")
def admin_list_staples(user=Depends(get_current_user)):
    conn = get_db()
    cur = conn.execute("SELECT * FROM daily_staples ORDER BY weekday, sort_order")
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    result = [[] for _ in range(5)]
    for item in items:
        result[item['weekday']].append(item)
    return result


@router.post("/daily-staples")
def admin_add_staple(weekday: int, name: str, user=Depends(get_current_user)):
    conn = get_db()
    conn.execute(
        "INSERT INTO daily_staples (weekday, name) VALUES (?,?)",
        (weekday, name)
    )
    conn.commit()
    sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"id": sid, "message": "主食已添加"}


@router.delete("/daily-staples/{staple_id}")
def admin_delete_staple(staple_id: int, user=Depends(get_current_user)):
    from datetime import date
    today = date.today().isoformat()
    conn = get_db()
    cur = conn.execute(
        "SELECT id FROM daily_orders WHERE staple_id = ? AND order_date = ? LIMIT 1",
        (staple_id, today)
    )
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="该主食今日已有预订，无法删除")
    conn.execute("DELETE FROM daily_orders WHERE staple_id = ?", (staple_id,))
    conn.execute("DELETE FROM daily_staples WHERE id = ?", (staple_id,))
    conn.commit()
    conn.close()
    return {"message": "主食已删除"}


# ─── 评分统计 ───
@router.get("/ratings/summary")
def admin_ratings_summary(date_from: str = None, date_to: str = None, user=Depends(get_current_user)):
    """菜品评分汇总排行"""
    conn = get_db()
    conditions = []
    params = []
    if date_from:
        conditions.append("menu_date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("menu_date <= ?")
        params.append(date_to)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    cur = conn.execute(
        f"""SELECT dish_name,
                  ROUND(AVG(score), 1) as avg_score,
                  COUNT(*) as count,
                  SUM(CASE WHEN score = 5 THEN 1 ELSE 0 END) as star5,
                  SUM(CASE WHEN score = 4 THEN 1 ELSE 0 END) as star4,
                  SUM(CASE WHEN score = 3 THEN 1 ELSE 0 END) as star3,
                  SUM(CASE WHEN score = 2 THEN 1 ELSE 0 END) as star2,
                  SUM(CASE WHEN score = 1 THEN 1 ELSE 0 END) as star1
           FROM dish_ratings
           {where}
           GROUP BY dish_name
           ORDER BY avg_score DESC""",
        params
    )
    items = [dict(row) for row in cur.fetchall()]
    total_count = sum(r["count"] for r in items)
    overall_avg = round(sum(r["avg_score"] * r["count"] for r in items) / total_count, 1) if total_count > 0 else 0
    conn.close()
    return {
        "total_ratings": total_count,
        "dish_count": len(items),
        "overall_avg": overall_avg,
        "dishes": items
    }


@router.get("/ratings/detail")
def admin_ratings_detail(date_from: str = None, date_to: str = None, dish_name: str = None, page: int = 1, page_size: int = 50, user=Depends(get_current_user)):
    """评分明细列表"""
    conn = get_db()
    conditions = []
    params = []
    if date_from:
        conditions.append("menu_date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("menu_date <= ?")
        params.append(date_to)
    if dish_name:
        conditions.append("dish_name LIKE ?")
        params.append(f"%{dish_name}%")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    cur = conn.execute(
        f"SELECT COUNT(*) as total FROM dish_ratings {where}", params
    )
    total = cur.fetchone()["total"]

    offset = (page - 1) * page_size
    cur = conn.execute(
        f"""SELECT * FROM dish_ratings
           {where}
           ORDER BY created_at DESC
           LIMIT ? OFFSET ?""",
        params + [page_size, offset]
    )
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


# ─── 预订记录
@router.get("/daily-orders")
def admin_list_orders(date_str: str = None, user=Depends(get_current_user)):
    from datetime import date
    if not date_str:
        date_str = date.today().isoformat()
    conn = get_db()
    cur = conn.execute(
        """SELECT do.*, ds.name as staple_name FROM daily_orders do
           JOIN daily_staples ds ON do.staple_id = ds.id
           WHERE do.order_date = ? ORDER BY do.created_at DESC""",
        (date_str,)
    )
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return items
