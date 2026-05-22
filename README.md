# WeChatDashboard - 企业微信群运营看板

企业微信会话存档消息的展示和运营分析平台。

## 架构

- `backend/` — FastAPI 后端（端口 8001）
  - `main.py` — 所有API（群管理、运营看板、最新消息等）
  - `models.py` — SQLAlchemy模型
- `frontend/` — Vue3 + Element Plus 前端（端口 5175）
  - `src/views/OperationsDashboard.vue` — 运营看板（内/外部群分列+时间筛选+最新消息）
  - `src/views/GroupManager.vue` — 群管理（手动编辑群名）
- `scripts/sync_messages.py` — 从容器DB同步新消息到Dashboard DB

## 启动

```bash
# 后端
cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8001

# 前端
cd frontend && npx vite --host 0.0.0.0 --port 5175
```

## 容器

企微会话存档采集运行在 `wechat-finance` Docker容器中，每15分钟采集一次。
消息自动同步到 Dashboard DB（cron: */15 * * * *）。
