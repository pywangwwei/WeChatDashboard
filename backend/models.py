"""
企业微信消息推送展示平台 - 数据库模型
SQLite起步，后续可切换MySQL/PostgreSQL
"""
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, '..', 'data', 'wechat_dashboard.db')}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Group(Base):
    """群聊信息"""
    __tablename__ = "groups"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    room_id = sa.Column(sa.String(128), unique=True, nullable=False, index=True)  # 企微群ID
    group_name = sa.Column(sa.String(256), default="")  # 群名称（从消息推断）
    group_type = sa.Column(sa.String(16), default="unknown")  # internal / external / unknown
    first_msg_time = sa.Column(sa.DateTime, nullable=True)
    last_msg_time = sa.Column(sa.DateTime, nullable=True)
    total_messages = sa.Column(sa.Integer, default=0)
    member_count = sa.Column(sa.Integer, default=0)  # 总人数
    internal_member_count = sa.Column(sa.Integer, default=0)  # 内部员工数
    external_member_count = sa.Column(sa.Integer, default=0)  # 外部客户数
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Person(Base):
    """发言用户"""
    __tablename__ = "persons"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.String(128), unique=True, nullable=False, index=True)  # 企微userid/邮箱
    display_name = sa.Column(sa.String(128), default="")  # 显示名称
    is_internal = sa.Column(sa.Boolean, default=False)  # 是否内部员工
    email = sa.Column(sa.String(256), default="")  # 企业邮箱
    department = sa.Column(sa.String(128), default="")  # 部门
    first_seen = sa.Column(sa.DateTime, nullable=True)
    last_seen = sa.Column(sa.DateTime, nullable=True)
    total_messages = sa.Column(sa.Integer, default=0)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)


class Message(Base):
    """聊天消息"""
    __tablename__ = "messages"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    msg_id = sa.Column(sa.String(128), unique=True, nullable=False, index=True)  # 企微msgid
    seq = sa.Column(sa.BigInteger, nullable=False, index=True)  # 消息序号
    room_id = sa.Column(sa.String(128), nullable=False, index=True)  # 群ID
    sender_id = sa.Column(sa.String(128), nullable=False, index=True)  # 发送者userid
    msg_type = sa.Column(sa.String(32), default="")  # text/image/file/mixed等
    action = sa.Column(sa.String(16), default="send")  # send/recall/switch
    content_text = sa.Column(sa.Text, default="")  # 文本内容（文本消息直接存，其他类型存描述）
    raw_content = sa.Column(sa.Text, default="")  # 原始JSON
    msg_time = sa.Column(sa.DateTime, nullable=False, index=True)  # 消息时间
    is_external = sa.Column(sa.Boolean, default=False)  # 是否外部群消息
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)


class AnalysisResult(Base):
    """每日分析结果"""
    __tablename__ = "analysis_results"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    date = sa.Column(sa.Date, nullable=False, index=True)  # 分析日期
    room_id = sa.Column(sa.String(128), nullable=False, index=True)
    total_messages = sa.Column(sa.Integer, default=0)
    internal_messages = sa.Column(sa.Integer, default=0)
    external_messages = sa.Column(sa.Integer, default=0)
    fault_count = sa.Column(sa.Integer, default=0)  # 问题/故障消息数
    fault_categories = sa.Column(sa.Text, default="{}")  # JSON: {"性能":5, "网络":3}
    sentiment_score = sa.Column(sa.Float, default=0.0)  # 情感分 0~100
    negative_count = sa.Column(sa.Integer, default=0)  # 不满意消息数
    active_senders = sa.Column(sa.Integer, default=0)  # 活跃发言人数
    top_keywords = sa.Column(sa.Text, default="[]")  # JSON: 高频关键词
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)


class IssueTicket(Base):
    """问题工单（持续追踪的问题）"""
    __tablename__ = "issue_tickets"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    issue_id = sa.Column(sa.String(64), unique=True, nullable=False)
    room_id = sa.Column(sa.String(128), nullable=False, index=True)
    category = sa.Column(sa.String(32), default="other")  # 性能/网络/数据/功能/接口/其他
    status = sa.Column(sa.String(16), default="open")  # open/resolved
    title = sa.Column(sa.String(256), default="")
    first_seen = sa.Column(sa.DateTime, nullable=True)
    last_seen = sa.Column(sa.DateTime, nullable=True)
    message_count = sa.Column(sa.Integer, default=0)
    involved_persons = sa.Column(sa.Text, default="[]")  # JSON: 相关人员列表
    resolution = sa.Column(sa.Text, default="")  # 解决方案
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)


class PersonBoard(Base):
    """人员看板（组织架构+活跃状态）"""
    __tablename__ = "person_board"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.String(128), unique=True, nullable=False, index=True)
    name = sa.Column(sa.String(128), default="")
    dept_name = sa.Column(sa.String(64), default="")
    dept_path = sa.Column(sa.String(256), default="")
    is_service_center = sa.Column(sa.Boolean, default=False)
    is_db_tech = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


def init_db():
    """初始化数据库，创建所有表"""
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库初始化完成")


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
