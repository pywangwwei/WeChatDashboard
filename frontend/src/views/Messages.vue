<template>
  <div>
    <h1 style="margin:0 0 20px 0;font-size:24px;">💬 消息记录</h1>

    <!-- 搜索 -->
    <el-card shadow="never" style="margin-bottom:16px;">
      <el-input v-model="keyword" placeholder="搜索消息内容..." clearable style="width:300px;margin-right:12px;" @keyup.enter="search"/>
      <el-button type="primary" @click="search">搜索</el-button>
    </el-card>

    <!-- 消息列表 -->
    <el-card shadow="never" v-loading="loading">
      <div v-for="m in messages" :key="m.msg_id"
           style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
          <el-tag :type="m.msg_type === 'text' ? '' : 'warning'" size="small">
            {{ typeLabel(m.msg_type) }}
          </el-tag>
          <el-tag :type="m.is_external ? 'success' : 'primary'" size="small" effect="plain">
            {{ m.is_external ? '外部群' : '内部群' }}
          </el-tag>
          <span style="font-size:12px;color:#999;">
            {{ m.room_id.slice(0, 12) }}... · {{ formatTime(m.msg_time) }}
          </span>
        </div>
        <div style="margin:4px 0;font-size:13px;">
          <strong>{{ m.sender_id.includes('@') ? m.sender_id.split('@')[0] : m.sender_id }}</strong>
          : {{ m.content_text }}
        </div>
        <div v-if="m.msg_type === 'image' || m.msg_type === 'file'" style="font-size:12px;color:#e6a23c;">
          📎 已上传资源文件
        </div>
      </div>
      <div v-if="messages.length === 0 && !loading" style="text-align:center;color:#999;padding:40px;">
        暂无消息记录
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listMessages, searchMessages } from '@/api/index.js'

const messages = ref([])
const keyword = ref('')
const loading = ref(false)

function typeLabel(t) {
  const map = { text: '文本', image: '图片', file: '文件', mixed: '混合', link: '链接', revoke: '撤回', meeting: '会议', meeting_notification: '会议通知' }
  return map[t] || t
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadMessages() {
  loading.value = true
  try {
    const res = await listMessages({ limit: 50 })
    messages.value = res.data.items
  } catch (e) {
    console.error(e)
  }
  loading.value = false
}

async function search() {
  if (!keyword.value.trim()) {
    loadMessages()
    return
  }
  loading.value = true
  try {
    const res = await searchMessages(keyword.value)
    messages.value = res.data.items
  } catch (e) {
    console.error(e)
  }
  loading.value = false
}

onMounted(loadMessages)
</script>
