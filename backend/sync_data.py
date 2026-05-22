"""
企业微信消息增量入库脚本
从Docker容器拉取最新的decrypted_messages.json，与数据库已有消息做增量合并
"""
import json, datetime, re, os, sys, subprocess
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import init_db, SessionLocal, Group, Person, Message

DOCKER_JSON = "/app/data/decrypted_messages.json"
LOCAL_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "decrypted_messages.json")


def sync_from_docker():
    """从容器复制解密消息文件到本地"""
    os.makedirs(os.path.dirname(LOCAL_JSON), exist_ok=True)
    r = subprocess.run(
        ["docker", "cp", f"wechat-finance:{DOCKER_JSON}", LOCAL_JSON],
        capture_output=True, text=True
    )
    return r.returncode == 0


def import_into_db():
    """增量导入消息到数据库"""
    if not os.path.exists(LOCAL_JSON):
        print(f"❌ JSON文件不存在: {LOCAL_JSON}")
        return False

    with open(LOCAL_JSON, encoding='utf-8') as f:
        msgs = json.load(f)

    db = SessionLocal()
    try:
        # 去重
        existing_ids = set(r[0] for r in db.query(Message.msg_id).all())
        total_old = len(existing_ids)

        new_msgs = [m for m in msgs if m.get('msgid','') and m['msgid'] not in existing_ids]
        if not new_msgs:
            print(f"✅ 无新消息 (当前{total_old}条)")
            db.close()
            return True

        print(f"📥 发现 {len(new_msgs)} 条新消息")

        for m in new_msgs:
            mid = m.get('msgid','')
            t = m.get('msgtime',0) or 0
            mt = datetime.datetime.fromtimestamp(t/1000) if t else datetime.datetime.utcnow()
            mtype = m.get('msgtype','') or ''
            
            if mtype == 'text': ct = (m.get('text') or {}).get('content','') or ''
            elif mtype == 'image': ct = '[图片]'
            elif mtype == 'file': ct = '[文件]'
            elif mtype == 'mixed': ct = '[混合消息]'
            elif mtype == 'revoke': ct = '[消息撤回]'
            elif mtype in ('meeting','meeting_notification'): ct = '[会议通知]'
            elif mtype == 'link': ct = '[链接]'
            else: ct = f'[{mtype}]'

            db.add(Message(
                msg_id=mid, seq=m.get('seq',0),
                room_id=m.get('roomid','') or '', sender_id=m.get('from','') or '',
                msg_type=mtype, action=m.get('action','send') or 'send',
                content_text=ct, raw_content=json.dumps(m, ensure_ascii=False),
                msg_time=mt, is_external='_external' in mid,
            ))

        db.commit()
        new_total = db.query(Message).count()
        print(f"✅ 入库完成: 新增{len(new_msgs)}条, 现有{new_total}条")

        # 更新群信息和人员信息
        _update_groups(db)
        _update_persons(db)
        print("✅ 群/人员信息更新完成")
        db.close()
        return True

    except Exception as e:
        db.rollback()
        db.close()
        print(f"❌ 入库失败: {e}")
        return False


def _update_groups(db):
    """更新群统计"""
    from sqlalchemy import func
    
    groups_stats = db.query(
        Message.room_id,
        func.count().label('total'),
        func.max(Message.msg_time).label('last'),
        func.min(Message.msg_time).label('first'),
    ).group_by(Message.room_id).all()

    for gs in groups_stats:
        rid = gs.room_id
        total = gs.total

        # 查该群外部消息数
        ext_count = db.query(Message).filter(
            Message.room_id == rid, Message.is_external == True
        ).count()

        # 成员统计
        members = db.query(Message.sender_id).filter(
            Message.room_id == rid
        ).distinct().all()
        member_ids = set(m[0] for m in members if m[0])

        # 获取tolist中的成员（从原始JSON）
        tolist_members = set()
        raw_msgs = db.query(Message.raw_content).filter(
            Message.room_id == rid, Message.raw_content != ''
        ).limit(50).all()
        for rm in raw_msgs:
            try:
                d = json.loads(rm[0])
                for t in d.get('tolist', []):
                    if t: tolist_members.add(t)
            except: pass

        all_members = member_ids | tolist_members
        ic = sum(1 for u in all_members if u and (u.endswith('@woqutech.com') or re.match(r'^\d{4}$', u) or not u.startswith('wmTn')))
        ec = len(all_members) - ic
        gt = 'external' if ext_count > total/2 else 'internal'

        existing = db.query(Group).filter(Group.room_id == rid).first()
        if existing:
            existing.total_messages = total
            existing.last_msg_time = gs.last
            existing.first_msg_time = gs.first
            existing.group_type = gt
            existing.member_count = len(all_members)
            existing.internal_member_count = ic
            existing.external_member_count = ec
        else:
            db.add(Group(
                room_id=rid, group_type=gt,
                first_msg_time=gs.first, last_msg_time=gs.last,
                total_messages=total, member_count=len(all_members),
                internal_member_count=ic, external_member_count=ec,
            ))
    db.commit()


def _update_persons(db):
    """更新人员统计"""
    from sqlalchemy import func
    
    persons = db.query(
        Message.sender_id,
        func.count().label('total'),
        func.min(Message.msg_time).label('first'),
        func.max(Message.msg_time).label('last'),
    ).filter(Message.sender_id != '').group_by(Message.sender_id).all()

    for ps in persons:
        uid = ps.sender_id
        if not uid: continue
        has_email = '@' in uid
        is_digit_id = bool(re.match(r'^\d{4}$', uid))
        internal = has_email or is_digit_id or not uid.startswith('wmTn')
        dname = uid.split('@')[0] if has_email else uid

        existing = db.query(Person).filter(Person.user_id == uid).first()
        if existing:
            existing.total_messages = ps.total
            existing.is_internal = internal
            existing.email = uid if has_email else ''
            existing.display_name = dname
        else:
            db.add(Person(
                user_id=uid, display_name=dname, is_internal=internal,
                email=uid if has_email else '',
                first_seen=ps.first, last_seen=ps.last, total_messages=ps.total,
            ))
    db.commit()


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    init_db()

    print("📦 同步企业微信消息...")
    if sync_from_docker():
        print("✅ 从Docker复制JSON成功")
    else:
        # 用本地缓存
        if not os.path.exists(LOCAL_JSON):
            print(f"⚠️ 无法从Docker复制，本地也无缓存")
            sys.exit(1)
        print("⚠️ 使用本地缓存")

    import_into_db()
