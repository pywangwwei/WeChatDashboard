"""
企业微信消息展示平台 - FastAPI 后端
"""
import json
import datetime
import os
import sys
import re
import collections

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import init_db, get_db, Group, Person, Message, AnalysisResult

app = FastAPI(title="企业微信消息分析平台", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ─── 群 API ───

@app.get("/api/groups")
def list_groups(
    group_type: str = None,
    sort_by: str = "total_messages",
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """群列表"""
    q = db.query(Group)
    if group_type:
        q = q.filter(Group.group_type == group_type)
    if sort_by == "total_messages":
        q = q.order_by(Group.total_messages.desc())
    elif sort_by == "member_count":
        q = q.order_by(Group.member_count.desc())
    elif sort_by == "last_active":
        q = q.order_by(Group.last_msg_time.desc().nullslast())
    else:
        q = q.order_by(Group.total_messages.desc())

    groups = q.limit(limit).all()

    # 尝试从消息提取群名称（取群内第一条有意义的文本）
    for g in groups:
        if not g.group_name:
            first_text = db.query(Message.content_text).filter(
                Message.room_id == g.room_id,
                Message.msg_type == 'text',
                Message.content_text != '',
            ).order_by(Message.msg_time.asc()).first()
            if first_text and first_text[0]:
                # 取第一条文本前30字作为群名
                g.group_name = first_text[0][:30]

    return {
        "total": len(groups),
        "items": [
            {
                "room_id": g.room_id,
                "group_name": g.group_name or g.room_id[:12],
                "group_type": g.group_type,
                "total_messages": g.total_messages,
                "member_count": g.member_count,
                "internal_member_count": g.internal_member_count,
                "external_member_count": g.external_member_count,
                "first_msg_time": g.first_msg_time.isoformat() if g.first_msg_time else None,
                "last_msg_time": g.last_msg_time.isoformat() if g.last_msg_time else None,
            }
            for g in groups
        ],
    }


@app.get("/api/groups/{room_id}")
def get_group_detail(room_id: str, db: Session = Depends(get_db)):
    """群详情"""
    g = db.query(Group).filter(Group.room_id == room_id).first()
    if not g:
        raise HTTPException(404, "群不存在")

    # 群内发言排行
    top_speakers = db.query(
        Person.user_id, Person.display_name, Person.is_internal, Person.email,
        func.count(Message.id).label("msg_count"),
    ).join(Message, Person.user_id == Message.sender_id)\
     .filter(Message.room_id == room_id)\
     .group_by(Person.user_id)\
     .order_by(desc("msg_count"))\
     .limit(30).all()

    # 消息类型分布
    type_dist = db.query(
        Message.msg_type,
        func.count().label("cnt"),
    ).filter(Message.room_id == room_id)\
     .group_by(Message.msg_type)\
     .all()

    # 每日统计
    daily_stats_raw = db.query(
        func.date(Message.msg_time).label("date"),
        func.count().label("total"),
        func.sum(func.cast(Message.is_external, func.Integer)).label("external"),
    ).filter(Message.room_id == room_id)\
     .group_by(func.date(Message.msg_time))\
     .order_by(func.date(Message.msg_time).desc())\
     .all()

    # 发言时间分布（按小时）
    hourly = db.query(
        func.strftime("%H", Message.msg_time).label("hour"),
        func.count().label("cnt"),
    ).filter(Message.room_id == room_id)\
     .group_by("hour")\
     .order_by("hour")\
     .all()

    return {
        "room_id": g.room_id,
        "group_name": g.group_name,
        "group_type": g.group_type,
        "total_messages": g.total_messages,
        "member_count": g.member_count,
        "internal_member_count": g.internal_member_count,
        "external_member_count": g.external_member_count,
        "first_msg_time": g.first_msg_time.isoformat() if g.first_msg_time else None,
        "last_msg_time": g.last_msg_time.isoformat() if g.last_msg_time else None,
        "top_speakers": [
            {
                "user_id": s.user_id,
                "display_name": s.display_name,
                "is_internal": s.is_internal,
                "email": s.email,
                "msg_count": s.msg_count,
            }
            for s in top_speakers
        ],
        "type_distribution": {t.msg_type: t.cnt for t in type_dist},
        "daily_stats": [
            {"date": str(s.date), "total": s.total, "external": s.external or 0}
            for s in daily_stats_raw
        ],
        "hourly_distribution": {h.hour: h.cnt for h in hourly},
    }


# ─── 消息 API ───

@app.get("/api/messages")
def list_messages(
    room_id: str = None,
    sender_id: str = None,
    msg_type: str = None,
    keyword: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """消息查询"""
    q = db.query(Message)
    if room_id:
        q = q.filter(Message.room_id == room_id)
    if sender_id:
        q = q.filter(Message.sender_id == sender_id)
    if msg_type:
        q = q.filter(Message.msg_type == msg_type)
    if keyword:
        q = q.filter(Message.content_text.contains(keyword))

    total = q.count()
    msgs = q.order_by(Message.msg_time.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "msg_id": m.msg_id,
                "seq": m.seq,
                "room_id": m.room_id,
                "sender_id": m.sender_id,
                "msg_type": m.msg_type,
                "action": m.action,
                "content_text": m.content_text[:200],
                "msg_time": m.msg_time.isoformat(),
                "is_external": m.is_external,
            }
            for m in msgs
        ],
    }


# ─── 发言者 API ───

@app.get("/api/persons")
def list_persons(
    is_internal: bool = None,
    sort_by: str = "total_messages",
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """人员列表"""
    q = db.query(Person).filter(Person.total_messages > 0)
    if is_internal is not None:
        q = q.filter(Person.is_internal == is_internal)
    if sort_by == "total_messages":
        q = q.order_by(Person.total_messages.desc())
    elif sort_by == "last_seen":
        q = q.order_by(Person.last_seen.desc().nullslast())
    else:
        q = q.order_by(Person.total_messages.desc())

    persons = q.limit(limit).all()

    return {
        "total": len(persons),
        "items": [
            {
                "user_id": p.user_id,
                "display_name": p.display_name,
                "is_internal": p.is_internal,
                "email": p.email,
                "department": p.department,
                "total_messages": p.total_messages,
                "first_seen": p.first_seen.isoformat() if p.first_seen else None,
                "last_seen": p.last_seen.isoformat() if p.last_seen else None,
            }
            for p in persons
        ],
    }


@app.get("/api/persons/{user_id}")
def get_person_detail(user_id: str, db: Session = Depends(get_db)):
    """人员详情"""
    p = db.query(Person).filter(Person.user_id == user_id).first()
    if not p:
        raise HTTPException(404, "人员不存在")

    # 该人员活跃的群
    active_groups = db.query(
        Message.room_id, Group.group_type,
        func.count().label("msg_count"),
    ).join(Group, Message.room_id == Group.room_id, isouter=True)\
     .filter(Message.sender_id == user_id)\
     .group_by(Message.room_id)\
     .order_by(desc("msg_count"))\
     .limit(10).all()

    # 消息类型分布
    type_dist = db.query(
        Message.msg_type,
        func.count().label("cnt"),
    ).filter(Message.sender_id == user_id)\
     .group_by(Message.msg_type)\
     .all()

    return {
        "user_id": p.user_id,
        "display_name": p.display_name,
        "is_internal": p.is_internal,
        "email": p.email,
        "department": p.department,
        "total_messages": p.total_messages,
        "first_seen": p.first_seen.isoformat() if p.first_seen else None,
        "last_seen": p.last_seen.isoformat() if p.last_seen else None,
        "active_groups": [
            {"room_id": g.room_id, "group_type": g.group_type or "unknown", "msg_count": g.msg_count}
            for g in active_groups
        ],
        "type_distribution": {t.msg_type: t.cnt for t in type_dist},
    }


# ─── 总览/看板 API ───

@app.get("/api/overview")
def get_overview(db: Session = Depends(get_db)):
    """首页总览数据"""
    total_groups = db.query(Group).count()
    total_messages = db.query(Message).count()
    total_persons = db.query(Person).filter(Person.total_messages > 0).count()
    internal_persons = db.query(Person).filter(Person.is_internal == True, Person.total_messages > 0).count()
    external_persons = db.query(Person).filter(Person.is_internal == False, Person.total_messages > 0).count()

    # 群类型分布
    internal_groups = db.query(Group).filter(Group.group_type == "internal").count()
    external_groups = db.query(Group).filter(Group.group_type == "external").count()

    # 消息类型分布
    type_dist = db.query(Message.msg_type, func.count().label("cnt"))\
        .group_by(Message.msg_type).all()

    # 今日消息量
    today = datetime.date.today()
    today_msgs = db.query(Message).filter(
        func.date(Message.msg_time) == today
    ).count()

    # 近7天消息趋势
    trend = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        cnt = db.query(Message).filter(
            func.date(Message.msg_time) == d
        ).count()
        trend.append({"date": str(d), "count": cnt})

    # 今日最活跃群 TOP5
    top_groups_today = db.query(
        Message.room_id, Group.group_type, Group.group_name,
        func.count().label("cnt"),
    ).join(Group, Message.room_id == Group.room_id, isouter=True)\
     .filter(func.date(Message.msg_time) == today)\
     .group_by(Message.room_id)\
     .order_by(desc("cnt"))\
     .limit(5).all()

    # 最活跃发言者 TOP10
    top_speakers = db.query(Person).filter(Person.total_messages > 0)\
        .order_by(Person.total_messages.desc()).limit(10).all()

    return {
        "total_groups": total_groups,
        "total_messages": total_messages,
        "total_persons": total_persons,
        "internal_persons": internal_persons,
        "external_persons": external_persons,
        "internal_groups": internal_groups,
        "external_groups": external_groups,
        "today_messages": today_msgs,
        "message_type_distribution": {t.msg_type: t.cnt for t in type_dist},
        "message_trend_7d": trend,
        "trend_start_date": str(today - datetime.timedelta(days=6)),
        "trend_end_date": str(today),
        "top_groups_today": [
            {"room_id": g.room_id, "group_type": g.group_type or "unknown", "group_name": g.group_name or g.room_id[:12], "count": g.cnt}
            for g in top_groups_today
        ],
        "top_speakers": [
            {
                "user_id": p.user_id,
                "display_name": p.display_name,
                "is_internal": p.is_internal,
                "email": p.email,
                "total_messages": p.total_messages,
            }
            for p in top_speakers
        ],
    }


@app.get("/api/analysis")
def get_analysis(
    date_from: str = None,
    date_to: str = None,
    room_id: str = None,
    db: Session = Depends(get_db),
):
    """分析数据"""
    q = db.query(AnalysisResult)
    if room_id:
        q = q.filter(AnalysisResult.room_id == room_id)
    if date_from:
        q = q.filter(AnalysisResult.date >= datetime.date.fromisoformat(date_from))
    if date_to:
        q = q.filter(AnalysisResult.date <= datetime.date.fromisoformat(date_to))

    results = q.order_by(AnalysisResult.date.desc()).all()
    return {
        "total": len(results),
        "items": [
            {
                "date": str(r.date),
                "room_id": r.room_id,
                "total_messages": r.total_messages,
                "internal_messages": r.internal_messages,
                "external_messages": r.external_messages,
                "fault_count": r.fault_count,
                "fault_categories": json.loads(r.fault_categories) if r.fault_categories else {},
                "negative_count": r.negative_count,
                "active_senders": r.active_senders,
                "top_keywords": json.loads(r.top_keywords) if r.top_keywords else [],
            }
            for r in results
        ],
    }


# ─── 搜索 API ───

@app.get("/api/recent-messages")
def recent_messages(limit: int = Query(20), db: Session = Depends(get_db)):
    """获取最新消息"""
    msgs = db.query(Message).filter(
        Message.content_text.isnot(None),
        Message.content_text != "",
    ).order_by(Message.msg_time.desc()).limit(limit).all()

    # 获取群名映射
    group_cache = {}
    groups = db.query(Group).all()
    for g in groups:
        group_cache[g.room_id] = g.group_name or g.room_id[:12]

    # 获取人员名映射
    person_cache = {}
    persons = db.query(Person).all()
    for p in persons:
        person_cache[p.user_id] = p.display_name or p.user_id

    return {
        "items": [
            {
                "msg_id": m.msg_id,
                "room_id": m.room_id,
                "group_name": group_cache.get(m.room_id, m.room_id[:12]),
                "sender_id": m.sender_id,
                "sender_name": person_cache.get(m.sender_id, m.sender_id[:12]),
                "content_text": m.content_text[:200],
                "msg_type": m.msg_type,
                "msg_time": m.msg_time.isoformat() if hasattr(m.msg_time, 'isoformat') else str(m.msg_time),
            }
            for m in msgs
        ]
    }


@app.get("/api/search")
def search(
    q: str = Query(..., description="搜索关键词"),
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """全文搜索消息"""
    if not q or len(q) < 1:
        return {"total": 0, "items": []}

    msgs = db.query(Message).filter(
        Message.content_text.contains(q)
    ).order_by(Message.msg_time.desc()).limit(limit).all()

    return {
        "total": len(msgs),
        "items": [
            {
                "msg_id": m.msg_id,
                "room_id": m.room_id,
                "sender_id": m.sender_id,
                "content_text": m.content_text[:200],
                "msg_type": m.msg_type,
                "msg_time": m.msg_time.isoformat(),
                "is_external": m.is_external,
            }
            for m in msgs
        ],
    }


# ─── 运营看板 API ───

@app.get("/api/operations-dashboard")
def get_operations_dashboard(
    period: str = Query("month", description="时间范围: day/week/month/quarter/year"),
    db: Session = Depends(get_db)
):
    """运营看板：按时间范围筛选，内部/外部群分列展示"""
    from datetime import date, timedelta

    today = date.today()
    PRODUCT_LINES = ["QData", "QFusion", "QPlus", "QOne", "QOneX", "QCP", "QMonitor", "QQuery"]

    # 根据period计算日期范围
    period_days = {
        "day": 0,    # 当天
        "week": 6,   # 近7天
        "month": 29, # 近30天
        "quarter": 89, # 近90天
        "year": 364,  # 近365天
    }
    days_back = period_days.get(period, 29)
    start_date = today - timedelta(days=days_back)

    # ─── 1. 按日期+内/外群类型统计活跃群数 ───
    daily_raw = db.query(
        func.date(Message.msg_time).label("dt"),
        Group.group_type,
        func.count(func.distinct(Message.room_id)).label("gcount"),
    ).join(Group, Message.room_id == Group.room_id, isouter=True)\
     .filter(func.date(Message.msg_time) >= start_date)\
     .group_by("dt", Group.group_type).all()

    daily_map = {}
    for r in daily_raw:
        dt = str(r.dt)
        if dt not in daily_map:
            daily_map[dt] = {"date": dt, "internal_groups": 0, "external_groups": 0, "unknown_groups": 0}
        gtype = r.group_type or "unknown"
        if gtype == "internal":
            daily_map[dt]["internal_groups"] = r.gcount
        elif gtype == "external":
            daily_map[dt]["external_groups"] = r.gcount
        else:
            daily_map[dt]["unknown_groups"] = r.gcount

    daily = []
    for i in range(days_back, -1, -1):
        d = str(today - timedelta(days=i))
        if d in daily_map:
            entry = daily_map[d]
            entry["total_groups"] = entry["internal_groups"] + entry["external_groups"] + entry["unknown_groups"]
            daily.append(entry)
        else:
            daily.append({"date": d, "internal_groups": 0, "external_groups": 0, "unknown_groups": 0, "total_groups": 0})

    # ─── 2. 汇总统计（按内/外群分开） ───
    # 内部群活跃数
    internal_active = db.query(func.count(func.distinct(Message.room_id)))\
        .join(Group, Message.room_id == Group.room_id)\
        .filter(Group.group_type == "internal", func.date(Message.msg_time) >= start_date).scalar() or 0
    external_active = db.query(func.count(func.distinct(Message.room_id)))\
        .join(Group, Message.room_id == Group.room_id)\
        .filter(Group.group_type == "external", func.date(Message.msg_time) >= start_date).scalar() or 0

    # 内部/外部群消息量
    internal_msgs = db.query(func.count(Message.id))\
        .join(Group, Message.room_id == Group.room_id)\
        .filter(Group.group_type == "internal", func.date(Message.msg_time) >= start_date).scalar() or 0
    external_msgs = db.query(func.count(Message.id))\
        .join(Group, Message.room_id == Group.room_id)\
        .filter(Group.group_type == "external", func.date(Message.msg_time) >= start_date).scalar() or 0

    # 影响业务群
    from sqlalchemy import or_
    IMPACT_KEYWORDS = ["故障", "异常", "报错", "宕机", "连不上", "告警", "无法", "error", "ORA-", "中断"]

    # ─── 3. 连续活跃群（按内/外群分开） ───
    all_groups = db.query(Group.room_id, Group.group_name, Group.group_type).all()
    internal_continuity = []
    external_continuity = []

    for g in all_groups:
        gname = g.group_name or g.room_id[:12]
        gtype = g.group_type or "unknown"

        active_dates = [
            r[0] for r in db.query(func.date(Message.msg_time)).filter(
                Message.room_id == g.room_id,
                func.date(Message.msg_time) >= start_date
            ).group_by(func.date(Message.msg_time)).order_by(func.date(Message.msg_time)).all()
        ]

        if not active_dates:
            continue

        max_streak = 1
        current_streak = 1
        for i in range(1, len(active_dates)):
            d1 = date.fromisoformat(active_dates[i-1])
            d2 = date.fromisoformat(active_dates[i])
            if (d2 - d1).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        monthly_active_days = sum(1 for ad in active_dates if date.fromisoformat(ad) >= start_date)

        entry = {
            "room_id": g.room_id,
            "group_name": gname,
            "group_type": gtype,
            "total_active_days": len(active_dates),
            "max_consecutive_days": max_streak,
            "monthly_active_days": monthly_active_days,
            "last_active_date": active_dates[-1],
        }
        if gtype == "internal":
            internal_continuity.append(entry)
        else:
            external_continuity.append(entry)

    def filter_consecutive(groups, threshold):
        return [g for g in groups if g["max_consecutive_days"] >= threshold]

    # ─── 4. 影响业务群/产品线统计（按内/外群分开） ───
    impact_raw = db.query(
        func.date(Message.msg_time).label("dt"),
        Group.group_type,
        func.count(func.distinct(Message.room_id)).label("gcount"),
    ).join(Group, Message.room_id == Group.room_id)\
     .filter(
        func.date(Message.msg_time) >= start_date,
        or_(*[Message.content_text.contains(kw) for kw in IMPACT_KEYWORDS])
    ).group_by("dt", Group.group_type).all()

    impact_map = {}
    for r in impact_raw:
        dt = str(r.dt)
        if dt not in impact_map:
            impact_map[dt] = {"internal": 0, "external": 0}
        gtype = r.group_type or "unknown"
        if gtype in ("internal", "external"):
            impact_map[dt][gtype] = r.gcount

    daily_impact = []
    for i in range(days_back, -1, -1):
        d = str(today - timedelta(days=i))
        entry = impact_map.get(d, {"internal": 0, "external": 0})
        entry["date"] = d
        entry["impact_groups"] = entry["internal"] + entry["external"]
        daily_impact.append(entry)

    # 产品线统计（按内部/外部群分组）
    product_by_type = {}
    for prod in PRODUCT_LINES:
        product_by_type[prod] = {
            "internal": {"messages": 0, "groups": 0},
            "external": {"messages": 0, "groups": 0},
        }
        for gtype in ("internal", "external"):
            cnt = db.query(func.count(Message.id)).join(Group, Message.room_id == Group.room_id).filter(
                func.date(Message.msg_time) >= start_date,
                Group.group_type == gtype,
                Message.content_text.contains(prod),
            ).scalar() or 0
            gcnt = db.query(func.count(func.distinct(Message.room_id))).join(Group, Message.room_id == Group.room_id).filter(
                Group.group_type == gtype,
                Message.content_text.contains(prod),
            ).scalar() or 0
            product_by_type[prod][gtype] = {"messages": cnt, "groups": gcnt}

    return {
        "period": period,
        "date_range": {"from": str(start_date), "to": str(today)},
        "summary": {
            "internal": {"active_groups": internal_active, "total_messages": internal_msgs},
            "external": {"active_groups": external_active, "total_messages": external_msgs},
            "total_groups": db.query(Group).count(),
            "internal_groups": db.query(Group).filter(Group.group_type == "internal").count(),
            "external_groups": db.query(Group).filter(Group.group_type == "external").count(),
        },
        "daily_summary": daily,
        "continuity": {
            "internal": {
                "consecutive_2d": len(filter_consecutive(internal_continuity, 2)),
                "consecutive_3d": len(filter_consecutive(internal_continuity, 3)),
                "consecutive_7d": len(filter_consecutive(internal_continuity, 7)),
                "groups": internal_continuity[:30],
            },
            "external": {
                "consecutive_2d": len(filter_consecutive(external_continuity, 2)),
                "consecutive_3d": len(filter_consecutive(external_continuity, 3)),
                "consecutive_7d": len(filter_consecutive(external_continuity, 7)),
                "groups": external_continuity[:30],
            },
        },
        "daily_impact_groups": daily_impact,
        "product_by_type": product_by_type,
        "stats_30d": {
            "total_messages": internal_msgs + external_msgs,
            "total_groups": db.query(Group).count(),
            "internal_groups": db.query(Group).filter(Group.group_type == "internal").count(),
            "external_groups": db.query(Group).filter(Group.group_type == "external").count(),
        }
    }


@app.post("/api/infer-group-names")
def infer_group_names(db: Session = Depends(get_db)):
    # 为所有无群名的群，从消息内容中提取关键词生成群名
    unnamed = db.query(Group).filter(
        (Group.group_name.is_(None)) | (Group.group_name == "")
    ).all()

    results = {"total": len(unnamed), "updated": 0, "skipped": 0, "errors": []}

    # 优先提取的关键词（高价值+低噪音）
    HIGH_VALUE_PATTERNS = {
        "product": r'QData|QFusion|QPlus|QOneX?|QCP|QMonitor|QQuery|QCS|ODM|POC',
        "project": r'WQXS-\S{3,20}',
        # 客户名常见后缀/前缀
        "customer_prefix": r'[（(]\s*(POC|正式|提前实施)[^）)]*[）)]',
        # 特定场景
        "maintenance": r'维保|售后|支持|维护',
        "alert": r'告警|监控|报警',
    }
    # 常见无意义词（过滤）
    STOP_WORDS = {
        "老师","您好","我们","问题","一个","可以","进行","没有","这个","那个",
        "什么","因为","但是","如果","或者","以后","还有","然后","就是","不是",
        "时候","现在","一下","之前","好了","好的","图片","文件","可以了",
        "你说","知道","看看","是的","收到","谢谢","找到","麻烦","需要",
        "已经","你们","他们","那个","这边","之前","以后","是的","稍等",
        "安装","测试","配置","部署","升级","重启","备份","恢复","查看",
        "连接","登录","创建","修改","删除","添加","完成","提交","更新",
        "不行","不能","不用","没事","对吧","好了","相关","使用","类型",
        "数据","信息","情况","状态","方式","方法","结果","原因",
    }

    for g in unnamed:
        try:
            # 取该群所有文本消息内容（最多1000条）
            msgs = db.query(Message.content_text).filter(
                Message.room_id == g.room_id,
                Message.content_text.isnot(None),
                Message.content_text != "",
                ~Message.content_text.ilike("这是一条引用%"),
                ~Message.content_text.ilike("@%"),
            ).order_by(Message.msg_time.asc()).limit(1000).all()

            texts = [m[0] for m in msgs]
            if not texts:
                results["skipped"] += 1
                continue

            word_scores = collections.Counter()

            # 策略1: 提取高价值关键词（单次匹配高权重）
            for text in texts:
                # 产品线和项目号
                for match in re.finditer(r'(QData|QFusion|QPlus|QOneX?|QCP|QMonitor|QQuery|QCS|ODM|POC)', text, re.IGNORECASE):
                    word_scores[match.group(0).upper()] += 30
                for match in re.finditer(r'WQXS-\S{3,20}', text):
                    word_scores[match.group(0)] += 35
                # 客户标记词
                for match in re.finditer(r'（(POC|正式|提前实施)[^）]*）|\((POC|正式|提前实施)[^)]*\)', text):
                    word_scores["__has_prefix_marker__"] += 1

            # 策略2: 提取客户名/项目名——完整中文词，排除无意义词
            for text in texts:
                # 提取连续中文词(2-10个汉字)
                cn_words = re.findall(r'[\u4e00-\u9fff]{2,10}', text)
                for cw in cn_words:
                    if cw not in STOP_WORDS and len(cw) >= 2:
                        word_scores[cw] += 1

            # 排序：产品线/项目号优先，中文词按频率
            # 先分离高价值词和普通中文词
            high_value = {}
            cn_candidates = {}
            for word, score in word_scores.items():
                if word.startswith("__"):
                    continue
                if score >= 20:
                    # 高价值词（产品线、项目号）
                    if word not in high_value or score > high_value[word]:
                        high_value[word] = score
                elif score >= 2:
                    # 中文词，至少出现2次
                    cn_candidates[word] = score

            new_name = None

            # 策略优先：取高价值词（产品线+项目号）
            hv_sorted = sorted(high_value.items(), key=lambda x: -x[1])
            if hv_sorted:
                parts = []
                for word, _ in hv_sorted[:3]:
                    combined = "".join(parts) + word
                    if len(combined) > 30:
                        break
                    parts.append(word)
                if parts:
                    new_name = "-".join(parts)

            # 如果有高价值词不足，补充高频中文词
            if new_name:
                current_len = len(new_name)
                cn_sorted = sorted(cn_candidates.items(), key=lambda x: -x[1])
                for word, _ in cn_sorted[:2]:
                    if current_len + len(word) + 1 > 30:
                        break
                    # 避免重复含义
                    if any(p in word for p in new_name.split("-")):
                        continue
                    new_name += "-" + word
                    current_len += len(word) + 1
                    break

            # 无高价值词时，用第一个有意义的对话片段
            if not new_name:
                # 跳过纯表情/图片/文件消息，找真正的内容
                for t in texts:
                    t_clean = re.sub(r'\[图片\]|\[文件\]|\[视频\]|\[表情\]|\[链接\]', '', t).strip()
                    if len(t_clean) >= 4:
                        runes = list(t_clean)
                        new_name = "".join(runes[:25]) + ("..." if len(runes) > 25 else "")
                        break

            if new_name:
                g.group_name = new_name
                results["updated"] += 1
            else:
                results["skipped"] += 1

        except Exception as e:
            results["errors"].append({"room_id": g.room_id, "error": str(e)})
            results["skipped"] += 1

    db.commit()
    return results


# 手动修改群名
class GroupNameUpdate(BaseModel):
    room_id: str
    group_name: str

@app.post("/api/update-group-name")
def update_group_name(req: GroupNameUpdate, db: Session = Depends(get_db)):
    g = db.query(Group).filter(Group.room_id == req.room_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    g.group_name = req.group_name
    db.commit()
    return {"status": "ok", "room_id": req.room_id, "group_name": req.group_name}


# 获取所有群列表（含消息量）
@app.get("/api/groups-with-stats")
def groups_with_stats(db: Session = Depends(get_db)):
    groups = db.query(Group).order_by(Group.group_type, Group.group_name).all()
    result = []
    for g in groups:
        msg_count = db.query(func.count(Message.id)).filter(Message.room_id == g.room_id).scalar() or 0
        result.append({
            "room_id": g.room_id,
            "group_name": g.group_name or "(未命名)",
            "group_type": g.group_type,
            "total_messages": msg_count,
            "member_count": g.member_count,
        })
    return {"groups": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
