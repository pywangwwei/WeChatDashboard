"""
企业微信消息入库脚本
从Docker容器的decrypted_messages.json读取数据，写入SQLite数据库
自动识别：群名称、内部/外部群、发言人信息
"""
import json
import datetime
import re
import os
import sys
import sqlalchemy as sa
from collections import defaultdict

# 确保能找到backend目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import init_db, SessionLocal, Group, Person, Message, AnalysisResult, IssueTicket

# 内部企业邮箱后缀
INTERNAL_EMAIL_SUFFIXES = ['woqutech.com']
# 内部用户ID前缀特征（企微内部userid通常为拼音/邮箱前缀）
INTERNAL_USER_PATTERNS = [
    r'.+@woqutech\.com$',  # 企业邮箱
    r'^techsupport$',      # 技术支持
    r'^\d{4}$',            # 4位数字工号
    r'^[a-z]+\.[a-z]+@',  # 拼音.姓格式
]
# 外部客户userid特征（企微外部用户以 wmT/wrT 开头）
EXTERNAL_USER_PREFIXES = ['wmTn', 'wrTn', 'woTn']

# 故障/问题关键词
FAULT_KEYWORDS = [
    '故障', '异常', '报错', '无法', '失败', 'down', 'error', '问题',
    '错误', '中断', '崩溃', '卡顿', '延迟', '超时', '告警', '警告',
    '不通', '连不上', '坏了', '挂了', '宕机', '恢复', '修复',
    'bug', 'issue', '宕了', '闪退', '死锁', '阻塞', 'OOM',
]

# 负面情绪关键词
NEGATIVE_KEYWORDS = [
    '不满意', '投诉', '太差', '垃圾', '不行', '很差', '受不了',
    '愤怒', '失望', '无语', '醉了', '坑', '烦', '难受',
]


def is_internal_user(user_id: str) -> bool:
    """判断用户是否内部员工"""
    if not user_id:
        return False
    # 企业邮箱
    if any(suffix in user_id for suffix in INTERNAL_EMAIL_SUFFIXES):
        return True
    # 数字工号
    if re.match(r'^\d{4}$', user_id):
        return True
    # wmT/wrT开头的企微外部用户
    if any(user_id.startswith(prefix) for prefix in EXTERNAL_USER_PREFIXES):
        return False
    # 内部userid通常不含特殊前缀，默认内部
    return True


def extract_email(user_id: str) -> str:
    """从userid中提取邮箱"""
    if '@' in user_id:
        return user_id
    return ''


def get_display_name(user_id: str) -> str:
    """获取显示名称"""
    if '@' in user_id:
        return user_id.split('@')[0]
    return user_id


def classify_fault(content: str) -> list:
    """识别消息中的问题类型"""
    if not content:
        return []
    categories = []
    # 性能问题
    if any(k in content for k in ['慢', '延迟', '卡顿', '超时', '性能', 'oom', 'OOM', '高负载']):
        categories.append('性能')
    # 网络问题
    if any(k in content for k in ['不通', '连不上', '网络', '连接失败', 'timeout', '丢包']):
        categories.append('网络')
    # 数据问题
    if any(k in content for k in ['数据丢失', '数据异常', '数据不一致', '数据错乱', '少数据']):
        categories.append('数据')
    # 功能问题
    if any(k in content for k in ['报错', '错误', '异常', '失败', 'bug', '不生效', '不能用']):
        categories.append('功能')
    # 接口问题
    if any(k in content for k in ['接口', 'api', 'API', '调用失败']):
        categories.append('接口')
    return categories


def is_fault_message(content: str) -> bool:
    """判断是否故障/问题消息"""
    if not content:
        return False
    return any(kw in content for kw in FAULT_KEYWORDS)


def is_negative_message(content: str) -> bool:
    """判断是否负面/不满消息"""
    if not content:
        return False
    return any(kw in content for kw in NEGATIVE_KEYWORDS)


def import_messages(json_path: str):
    """从解密JSON文件导入消息到数据库"""
    with open(json_path, 'r', encoding='utf-8') as f:
        msgs = json.load(f)

    db = SessionLocal()
    try:
        total = len(msgs)
        imported = 0
        skipped = 0

        # 缓存已存在的记录
        existing_msgids = set(
            row[0] for row in db.query(Message.msg_id).all()
        )

        for m in msgs:
            msg_id = m.get('msgid', '')
            if not msg_id or msg_id in existing_msgids:
                skipped += 1
                continue

            room_id = m.get('roomid', '')
            sender_id = m.get('from', '')
            msg_type = m.get('msgtype', '')
            action = m.get('action', 'send')
            is_external = '_external' in msg_id

            # 提取文本内容
            content_text = ''
            if msg_type == 'text':
                content_text = m.get('text', {}).get('content', '')
            elif msg_type == 'image':
                content_text = '[图片]'
            elif msg_type == 'file':
                content_text = '[文件]'
            elif msg_type == 'mixed':
                content_text = '[混合消息]'
            elif msg_type == 'revoke':
                content_text = '[消息撤回]'
            elif msg_type == 'meeting' or msg_type == 'meeting_notification':
                content_text = '[会议通知]'
            else:
                content_text = f'[{msg_type}]'

            # 时间
            msgtime = m.get('msgtime', 0)
            if msgtime:
                msg_time = datetime.datetime.fromtimestamp(msgtime / 1000)
            else:
                msg_time = datetime.datetime.utcnow()

            # 入库消息
            message = Message(
                msg_id=msg_id,
                seq=m.get('seq', 0),
                room_id=room_id,
                sender_id=sender_id,
                msg_type=msg_type,
                action=action,
                content_text=content_text,
                raw_content=json.dumps(m, ensure_ascii=False),
                msg_time=msg_time,
                is_external=is_external,
            )
            db.add(message)
            existing_msgids.add(msg_id)
            imported += 1

        db.commit()
        print(f"✅ 入库完成: 共{total}条, 导入{imported}条, 跳过{skipped}条(已存在)")

        # 更新群信息
        update_groups(db, msgs)
        # 更新用户信息
        update_persons(db, msgs)
        # 生成每日分析
        generate_daily_analysis(db)

    except Exception as e:
        db.rollback()
        print(f"❌ 入库失败: {e}")
        raise
    finally:
        db.close()


def update_groups(db, msgs):
    """更新群信息"""
    # 按群聚合
    group_data = defaultdict(lambda: {
        'first': None, 'last': None, 'count': 0,
        'internal_msgs': 0, 'external_msgs': 0,
        'senders': set(), 'users': set()
    })

    for m in msgs:
        rid = m.get('roomid', '')
        if not rid:
            continue

        g = group_data[rid]
        msgtime = m.get('msgtime', 0)
        if msgtime:
            dt = datetime.datetime.fromtimestamp(msgtime / 1000)
            if g['first'] is None or dt < g['first']:
                g['first'] = dt
            if g['last'] is None or dt > g['last']:
                g['last'] = dt

        g['count'] += 1
        if '_external' in m.get('msgid', ''):
            g['external_msgs'] += 1
        else:
            g['internal_msgs'] += 1

        if m.get('from'):
            g['senders'].add(m['from'])
        for t in m.get('tolist', []):
            if t:
                g['users'].add(t)

    for rid, data in group_data.items():
        # 判断群类型
        if data['external_msgs'] > data['internal_msgs']:
            group_type = 'external'
        elif data['internal_msgs'] > 0:
            group_type = 'internal'
        else:
            group_type = 'unknown'

        # 统计成员
        all_members = data['senders'] | data['users']
        internal_count = sum(1 for u in all_members if is_internal_user(u))
        external_count = len(all_members) - internal_count

        # 尝试从第一个文本消息推断群名
        group_name = ''
        for m in msgs:
            if m.get('roomid') == rid and m.get('msgtype') == 'text':
                text = m.get('text', {}).get('content', '')
                # 如果第一条消息 @了某人，群名可能是技术讨论
                if not group_name and text:
                    # 默认用第一个外部客户的名称或内部讨论主题
                    pass
                break

        # 更新或创建群
        existing = db.query(Group).filter(Group.room_id == rid).first()
        if existing:
            existing.total_messages = data['count']
            existing.last_msg_time = data['last']
            existing.group_type = group_type
            existing.member_count = len(all_members)
            existing.internal_member_count = internal_count
            existing.external_member_count = external_count
        else:
            group = Group(
                room_id=rid,
                group_name=group_name,
                group_type=group_type,
                first_msg_time=data['first'],
                last_msg_time=data['last'],
                total_messages=data['count'],
                member_count=len(all_members),
                internal_member_count=internal_count,
                external_member_count=external_count,
            )
            db.add(group)

    db.commit()
    total_groups = db.query(Group).count()
    print(f"✅ 群信息更新完成: {total_groups}个群")


def update_persons(db, msgs):
    """更新发言用户信息"""
    person_set = set()
    for m in msgs:
        if m.get('from'):
            person_set.add(m['from'])
        for t in m.get('tolist', []):
            if t:
                person_set.add(t)

    for uid in person_set:
        internal = is_internal_user(uid)
        existing = db.query(Person).filter(Person.user_id == uid).first()

        # 统计该用户的消息数
        msg_count = db.query(Message).filter(
            Message.sender_id == uid
        ).count()

        # 首次/最后出现时间
        first_msg = db.query(Message).filter(
            Message.sender_id == uid
        ).order_by(Message.msg_time.asc()).first()
        last_msg = db.query(Message).filter(
            Message.sender_id == uid
        ).order_by(Message.msg_time.desc()).first()

        if existing:
            existing.total_messages = msg_count
            existing.display_name = get_display_name(uid)
            existing.is_internal = internal
            existing.email = extract_email(uid)
            if first_msg:
                existing.first_seen = first_msg.msg_time
            if last_msg:
                existing.last_seen = last_msg.msg_time
        else:
            person = Person(
                user_id=uid,
                display_name=get_display_name(uid),
                is_internal=internal,
                email=extract_email(uid),
                first_seen=first_msg.msg_time if first_msg else None,
                last_seen=last_msg.msg_time if last_msg else None,
                total_messages=msg_count,
            )
            db.add(person)

    db.commit()
    total_persons = db.query(Person).count()
    print(f"✅ 用户信息更新完成: {total_persons}人")


def generate_daily_analysis(db):
    """生成每日分析数据"""
    # 直接取所有消息，按python处理日期分组
    all_msgs = db.query(Message).all()
    
    # 按(日期, 群)分组
    from collections import defaultdict as ddict
    groups = ddict(list)
    for m in all_msgs:
        date_key = m.msg_time.date()
        groups[(date_key, m.room_id)].append(m)

    for (date, room_id), day_msgs in groups.items():
        fault_count = 0
        negative_count = 0
        fault_cats = ddict(int)
        keywords = []
        external_count = 0
        senders = set()

        for m in day_msgs:
            if m.is_external:
                external_count += 1
            senders.add(m.sender_id)
            text = m.content_text
            if is_fault_message(text):
                fault_count += 1
                for cat in classify_fault(text):
                    fault_cats[cat] += 1
            if is_negative_message(text):
                negative_count += 1
            if text and len(text) > 2:
                for i in range(len(text) - 1):
                    word = text[i:i+2]
                    if word.isalpha() and len(word) == 2:
                        keywords.append(word)

        # 关键词频次
        from collections import Counter
        top_keywords = [w for w, _ in Counter(keywords).most_common(20) if len(w) >= 2]

        existing = db.query(AnalysisResult).filter(
            AnalysisResult.date == date,
            AnalysisResult.room_id == room_id
        ).first()

        total = len(day_msgs)
        if existing:
            existing.total_messages = total
            existing.external_messages = external_count
            existing.internal_messages = total - external_count
            existing.fault_count = fault_count
            existing.fault_categories = json.dumps(dict(fault_cats), ensure_ascii=False)
            existing.negative_count = negative_count
            existing.active_senders = len(senders)
            existing.top_keywords = json.dumps(top_keywords, ensure_ascii=False)
        else:
            analysis = AnalysisResult(
                date=date,
                room_id=room_id,
                total_messages=total,
                internal_messages=total - external_count,
                external_messages=external_count,
                fault_count=fault_count,
                fault_categories=json.dumps(dict(fault_cats), ensure_ascii=False),
                negative_count=negative_count,
                active_senders=len(senders),
                top_keywords=json.dumps(top_keywords, ensure_ascii=False),
            )
            db.add(analysis)

    db.commit()
    total_analysis = db.query(AnalysisResult).count()
    print(f"✅ 每日分析完成: {total_analysis}条记录")


if __name__ == '__main__':
    # 初始化数据库
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    init_db()

    import sys
    json_path = sys.argv[1] if len(sys.argv) > 1 else '../data/decrypted_messages.json'
    if not os.path.exists(json_path):
        # 尝试从docker复制
        print("本地JSON不存在，尝试从Docker容器复制...")
        os.system(f"docker cp wechat-finance:/app/data/decrypted_messages.json {json_path}")

    if os.path.exists(json_path):
        import_messages(json_path)
    else:
        print(f"❌ JSON文件不存在: {json_path}")
        print(f"请先运行: docker cp wechat-finance:/app/data/decrypted_messages.json data/")
