"""食堂菜单管理平台 - FastAPI 入口"""
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import init_db, get_db
from auth import get_current_user

from routers import dishes, menus, feedbacks, admin

app = FastAPI(title="饭点小站管理平台", version="1.0.0")

# CORS 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(dishes.router)
app.include_router(menus.router)
app.include_router(feedbacks.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup():
    init_db()


# 静态文件服务（管理后台和手机端）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

admin_dir = os.path.join(ROOT_DIR, "admin")
mobile_dir = os.path.join(ROOT_DIR, "mobile")

if os.path.isdir(admin_dir):
    app.mount("/admin", StaticFiles(directory=admin_dir, html=True), name="admin")

if os.path.isdir(mobile_dir):
    app.mount("/mobile", StaticFiles(directory=mobile_dir, html=True), name="mobile")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/daily-staples")
def get_daily_staples():
    from database import get_db
    conn = get_db()
    cur = conn.execute("SELECT * FROM daily_staples ORDER BY weekday, sort_order")
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    result = [[] for _ in range(5)]
    for item in items:
        result[item['weekday']].append(item)
    return result


@app.post("/api/daily-orders")
def submit_daily_order(customer_name: str, orders: str):
    """提交每日主食预订 orders: [{staple_id, quantity}, ...] 的JSON字符串"""
    import json
    from datetime import date
    today = date.today().isoformat()
    conn = get_db()
    for item in json.loads(orders):
        conn.execute(
            "INSERT INTO daily_orders (customer_name, staple_id, quantity, order_date) VALUES (?,?,?,?)",
            (customer_name, item['staple_id'], item['quantity'], today)
        )
    conn.commit()
    conn.close()
    return {"message": "预订成功"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8088, reload=True)
