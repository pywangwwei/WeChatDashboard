<template>
  <div>
    <h1 style="margin:0 0 20px 0;font-size:24px;">👥 群聊管理</h1>

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
      <div v-for="g in groups" :key="g.room_id"
           style="display:flex;align-items:center;padding:14px 0;border-bottom:1px solid #f0f0f0;cursor:pointer;"
           @click="$router.push('/groups/'+g.room_id)">
        <div style="width:40px;height:40px;border-radius:10px;background:#f0f2f5;display:flex;align-items:center;justify-content:center;font-size:20px;margin-right:14px;">
          {{ g.group_type === 'external' ? '🌐' : '🏢' }}
        </div>
        <div style="flex:1;">
          <div style="font-weight:bold;">{{ g.group_name || g.room_id.slice(0, 20)+'...' }}</div>
          <div style="font-size:12px;color:#999;margin-top:2px;">
            {{ g.total_messages }}条消息 · {{ g.member_count }}人(内部{{ g.internal_member_count }}/外部{{ g.external_member_count }})
            · 最后活跃: {{ formatTime(g.last_msg_time) }}
          </div>
        </div>
        <div>
          <el-tag :type="g.group_type === 'external' ? 'success' : 'primary'" size="small">
            {{ g.group_type === 'external' ? '外部群' : '内部群' }}
          </el-tag>
        </div>
      </div>
      <div v-if="groups.length === 0 && !loading" style="text-align:center;color:#999;padding:40px;">
        暂无群数据
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listGroups } from '@/api/index.js'

const groups = ref([])
const total = ref(0)
const filterType = ref('')
const loading = ref(false)

function formatTime(t) {
  if (!t) return '—'
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadGroups() {
  loading.value = true
  try {
    const res = await listGroups({ group_type: filterType.value || undefined, limit: 200 })
    groups.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    console.error(e)
  }
  loading.value = false
}

onMounted(loadGroups)
</script>
