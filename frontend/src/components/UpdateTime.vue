<template>
  <div style="display:flex;align-items:center;gap:12px;">
    <span v-if="loading" style="font-size:12px;color:#999;">加载中...</span>
    <span v-else style="font-size:12px;color:#999;display:flex;align-items:center;gap:4px;">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12,6 12,12 16,14"/>
      </svg>
      ⏱ {{ formattedTime }}
      <span v-if="messageCount">· {{ messageCount }}条消息</span>
    </span>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'UpdateTime',
  props: {
    refresh: { type: Number, default: 60000 },
  },
  setup(props) {
    const lastTime = ref('')
    const messageCount = ref(0)
    const loading = ref(true)

    const formattedTime = computed(() => {
      if (!lastTime.value) return '暂无数据'
      const d = new Date(lastTime.value)
      if (isNaN(d.getTime())) return lastTime.value
      const month = d.getMonth() + 1
      const day = d.getDate()
      const h = String(d.getHours()).padStart(2, '0')
      const m = String(d.getMinutes()).padStart(2, '0')
      return `${month}/${day} ${h}:${m}`
    })

    const fetchTime = async () => {
      try {
        const res = await axios.get('/api/last-update')
        lastTime.value = res.data.last_msg_time || ''
        messageCount.value = res.data.total_messages || 0
      } catch(e) {
        console.error('获取更新时间失败:', e)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      fetchTime()
      if (props.refresh > 0) {
        setInterval(fetchTime, props.refresh)
      }
    })

    return { loading, formattedTime, messageCount }
  }
}
</script>
