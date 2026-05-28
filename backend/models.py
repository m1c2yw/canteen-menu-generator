"""Pydantic 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# ─── 菜品 ───
class DishCreate(BaseModel):
    name: str
    category: str
    cuisine: str
    protein: str = ''


class DishUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    cuisine: Optional[str] = None
    protein: Optional[str] = None
    enabled: Optional[int] = None


class DishResponse(BaseModel):
    id: int
    name: str
    category: str
    cuisine: str
    protein: str
    enabled: int


# ─── 菜单 ───
class ReplaceItem(BaseModel):
    menu_id: int
    day_date: str
    slot: str
    new_dish_id: int


class MenuItemResponse(BaseModel):
    id: int
    day_date: str
    day_name: str = ''
    is_holiday: bool
    slot: str
    dish_id: Optional[int] = None
    dish_name: str
    category: str
    cuisine: str
    protein: str = ''


class DayMenu(BaseModel):
    date: str
    day_name: str
    is_holiday: bool
    dishes: Optional[dict] = None  # { bigMeat: [...], otherMeat: [...], vegetables: [...], soup: {...}, noodle: {...} }


class WeekMenuResponse(BaseModel):
    week_key: str
    repeat_rate: float
    generated_at: str
    days: list[DayMenu]


# ─── 投诉建议 ───
class FeedbackCreate(BaseModel):
    nickname: str = '匿名'
    content: str
    type: str = 'suggestion'  # suggestion / complaint / praise


class FeedbackReply(BaseModel):
    reply: str


class FeedbackResponse(BaseModel):
    id: int
    nickname: str
    content: str
    type: str
    status: str
    reply: str
    created_at: str


# ─── 认证 ───
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


# ─── 节假日 ───
class HolidayCreate(BaseModel):
    date: str
    name: str
