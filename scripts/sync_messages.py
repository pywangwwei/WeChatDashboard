#!/usr/bin/env python3
"""从容器DB同步新消息到Dashboard DB（每15分钟运行一次）"""

import sqlite3
import os

SRC = os.path.expanduser("~/.hermes/enterprise-wechat/wechat-finance-service/data/wechat_messages.db")
DST = os.path.expanduser("~/Desktop/WeChatDashboard/data/wechat_dashboard.db")

src = sqlite3.connect(SRC)
src.row_factory = sqlite3.Row
dst = sqlite3.connect(DST)

last_seq = dst.execute("SELECT COALESCE(MAX(seq), 0) FROM messages").fetchone()[0]
new_rows = src.execute("SELECT * FROM chat_messages WHERE seq > ? ORDER BY seq", (last_seq,)).fetchall()

if not new_rows:
    print(f"sync: 无新消息 (last_seq={last_seq})")
    src.close()
    dst.close()
    exit(0)

inserted = 0
new_rooms = set()
for row in new_rows:
    d = dict(row)
    msgid = d.get('msgid', '')
    if not msgid:
        continue
    existing = dst.execute('SELECT id FROM messages WHERE msg_id = ?', (msgid,)).fetchone()
    if existing:
        continue
    dst.execute('''
        INSERT OR IGNORE INTO messages 
        (msg_id, seq, room_id, sender_id, msg_type, action, content_text, raw_content, msg_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (
        d['msgid'], d['seq'], d['room_id'], d.get('from_id', ''),
        d.get('msg_type', ''), d.get('action', ''), d.get('content', ''),
        d.get('raw_json', ''), d['msg_time_str']
    ))
    new_rooms.add(d['room_id'])
    inserted += 1

dst.commit()

# 新群自动创建记录
for rid in new_rooms:
    existing = dst.execute("SELECT id FROM groups WHERE room_id=?", (rid,)).fetchone()
    if not existing:
        dst.execute('''
            INSERT OR IGNORE INTO groups (room_id, group_type, created_at, updated_at)
            VALUES (?, 'external', datetime('now'), datetime('now'))
        ''', (rid,))

dst.commit()
print(f"sync: {inserted}条新消息, {len(new_rooms)}个新群 (seq>{last_seq})")
dst.close()
src.close()
