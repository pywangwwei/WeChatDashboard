<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;">
      <h1 style="margin:0;font-size:24px;">👥 群聊管理</h1>
      <UpdateTime :refresh="60000" />
    </div>

    <!-- 过滤 -->
    <el-card shadow="never" style="margin-bottom:16px;">
      <el-radio-group v-model="filterType" @change="loadGroups" style="margin-right:16px;">
        <el-radio-button value="">全部 ({{ total }})</el-radio-button>
        <el-radio-button value="internal">🏢 内部群</el-radio-button>
        <el-radio-button value="external">🌐 外部群</el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- 群列表 -->
    <el-card shadow="never" v-loading="loading">
      <div v-for="g in filteredGroups" :key="g.room_id"
           style="display:flex;align-items:center;padding:14px 0;border-bottom:1px solid #f0f0f0;cursor:pointer;"
           @click="$router.push('/groups/'+g.room_id)">
        <div style="width:40px;height:40px;border-radius:10px;background:#f0f2f5;display:flex;align-items:center;justify-content:center;font-size:20px;margin-right:14px;">
          {{ g.group_type === 'external' ? '🌐' : '🏢' }}
        </div>
        <div style="flex:1;">
          <div style="font-weight:bold;display:flex;align-items:center;gap:8px;">
            {{ g.group_name || g.room_id.slice(0, 20)+'...' }}
            <el-tag v-if="g.today_count > 0" type="danger" size="small" effect="plain">
              今日{{ g.today_count }}条
            </el-tag>
          </div>
          <div style="font-size:12px;color:#999;margin-top:2px;">
            {{ g.total_messages }}条(累计) · {{ g.member_count }}人(内部{{ g.internal_member_count }}/外部{{ g.external_member_count }})
            · 最后活跃: {{ formatTime(g.last_msg_time) }}
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <el-button size="small" type="warning" plain @click.stop="aiAnalyze(g)">
            🤖 AI总结
          </el-button>
          <el-tag :type="g.group_type === 'external' ? 'success' : 'primary'" size="small">
            {{ g.group_type === 'external' ? '外部群' : '内部群' }}
          </el-tag>
        </div>
      </div>
      <div v-if="filteredGroups.length === 0 && !loading" style="text-align:center;color:#999;padding:40px;">
        暂无群数据
      </div>
    </el-card>

    <!-- AI总结弹窗 -->
    <el-dialog v-model="dialogVisible" :title="'🤖 AI分析：' + (analysisGroup?.group_name || '')"
      width="700px" top="5vh">
      <div v-loading="analyzing" style="min-height:200px;">
        <div v-if="analysisResult" style="white-space:pre-wrap;line-height:1.8;font-size:14px;">{{ analysisResult }}</div>
        <div v-if="!analyzing && !analysisResult" style="color:#999;text-align:center;padding:40px;">
          点击按钮开始AI分析
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import UpdateTime from '@/components/UpdateTime.vue'

const groups = ref([])
const total = ref(0)
const filterType = ref('')
const loading = ref(false)

// AI分析
const dialogVisible = ref(false)
const analyzing = ref(false)
const analysisGroup = ref(null)
const analysisResult = ref('')

// 按当天消息排序
const filteredGroups = computed(() => {
  const list = groups.value.filter(g => {
    if (!filterType.value) return true
    return g.group_type === filterType.value
  })
  // 按今日消息数降序，无今日消息的按总消息数
  return list.sort((a, b) => {
    if (a.today_count !== b.today_count) return (b.today_count || 0) - (a.today_count || 0)
    return (b.total_messages || 0) - (a.total_messages || 0)
  })
})

function formatTime(t) {
  if (!t) return '—'
  const d = new Date(t)
  if (isNaN(d.getTime())) return t
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${m}/${day} ${h}:${min}`
}

async function loadGroups() {
  loading.value = true
  try {
    // 获取所有群
    const res = await axios.get('/api/groups-with-stats')
    let items = res.data.groups || []

    // 获取当天消息计数（按群）
    const today = new Date().toISOString().slice(0, 10)
    const msgsRes = await axios.get(`/api/messages?limit=5000&fields=room_id,msg_time`)
    const allMsgs = msgsRes.data.items || []

    // 统计今天每个群的消息数
    const todayCounts = {}
    allMsgs.forEach(m => {
      if (m.msg_time && m.msg_time.startsWith(today)) {
        const rid = m.room_id
        todayCounts[rid] = (todayCounts[rid] || 0) + 1
      }
    })

    // 合并数据
    items = items.map(g => ({
      ...g,
      today_count: todayCounts[g.room_id] || 0,
    }))

    groups.value = items
    total.value = items.length
  } catch (e) {
    console.error('获取群列表失败:', e)
  }
  loading.value = false
}

async function aiAnalyze(g) {
  analysisGroup.value = g
  dialogVisible.value = true
  analyzing.value = true
  analysisResult.value = ''

  try {
    // 取今天该群的消息
    const today = new Date().toISOString().slice(0, 10)
    const res = await axios.get(`/api/messages?room_id=${encodeURIComponent(g.room_id)}&limit=100`)
    const msgs = res.data.items || []

    if (msgs.length === 0) {
      analysisResult.value = '该群今天没有消息，无需分析。'
      analyzing.value = false
      return
    }

    // 构建分析文本
    const lines = msgs.slice(-30).map(m => {
      const t = m.msg_time ? new Date(m.msg_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : ''
      const sender = (m.sender_name || m.sender_id || 'unknown').slice(0, 10)
      const content = (m.content_text || '').slice(0, 200)
      return `[${t}] ${sender}: ${content}`
    })

    const prompt = `你是一个企业微信售后群消息分析专家。以下是对"${g.group_name}"群今天消息的摘要（${msgs.length}条），请分析：

1. **当天讨论主题**：今天讨论了什么问题
2. **问题类型**：是故障处理、需求咨询、产品Bug还是日常沟通
3. **关键事件**：列出重要的事件和时间
4. **后续行动**：有什么待办事项或建议

群消息：
${lines.join('\n')}`

    const aiRes = await axios.post('/api/ai-analyze', {
      group_name: g.group_name,
      messages: prompt,
    })
    analysisResult.value = aiRes.data.analysis || '分析失败，请稍后重试'
  } catch (e) {
    analysisResult.value = `⚠️ AI分析失败: ${e.message}`
  }
  analyzing.value = false
}

onMounted(loadGroups)
</script>
