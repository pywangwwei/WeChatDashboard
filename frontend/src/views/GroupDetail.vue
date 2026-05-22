<template>
  <div>
    <el-button @click="$router.push('/groups')" text style="margin-bottom:12px;">
      ← 返回群列表
    </el-button>

    <div v-if="loading" style="text-align:center;padding:60px;color:#999;">加载中...</div>

    <template v-if="!loading && group">
      <!-- 群基本信息 -->
      <el-card shadow="never" style="margin-bottom:16px;">
        <div style="display:flex;align-items:center;gap:16px;">
          <div style="width:56px;height:56px;border-radius:14px;background:#f0f2f5;display:flex;align-items:center;justify-content:center;font-size:28px;">
            {{ group.group_type === 'external' ? '🌐' : '🏢' }}
          </div>
          <div>
            <h2 style="margin:0;">{{ group.group_name || group.room_id.slice(0, 20)+'...' }}</h2>
            <p style="color:#999;margin:4px 0 0 0;">
              {{ group.total_messages }}条消息 · {{ group.member_count }}人(内{{ group.internal_member_count }}/外{{ group.external_member_count }})
              · {{ group.group_type === 'external' ? '外部客户群' : '内部群' }}
            </p>
          </div>
        </div>
      </el-card>

      <!-- 统计行 -->
      <el-row :gutter="16" style="margin-bottom:16px;">
        <el-col :span="6" v-for="card in groupStatCards" :key="card.label">
          <el-card shadow="never" :body-style="{padding:'16px',textAlign:'center'}">
            <div style="font-size:24px;font-weight:bold;">{{ card.value }}</div>
            <div style="font-size:12px;color:#999;">{{ card.label }}</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 消息类型分布 + 时间分布 -->
      <el-row :gutter="16" style="margin-bottom:16px;">
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>📦 消息类型分布</template>
            <div ref="typeChart" style="height:240px;"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>🕐 发言时间分布</template>
            <div ref="hourChart" style="height:240px;"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 发言排行 -->
      <el-card shadow="never">
        <template #header>🏆 群内发言排行</template>
        <div v-for="(s, i) in group.top_speakers" :key="s.user_id"
             style="display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #f0f0f0;cursor:pointer;"
             @click="$router.push('/persons/'+s.user_id)">
          <div style="width:24px;font-weight:bold;color:#999;">{{ i+1 }}</div>
          <div style="margin-right:8px;">{{ s.is_internal ? '🔵' : '🟢' }}</div>
          <div style="flex:1;">{{ s.display_name }}</div>
          <div v-if="s.email" style="color:#999;font-size:12px;margin-right:8px;">{{ s.email }}</div>
          <div style="font-weight:bold;color:#409eff;">{{ s.msg_count }}条</div>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getGroupDetail } from '@/api/index.js'
import { useRoute } from 'vue-router'

const route = useRoute()
const loading = ref(true)
const group = ref(null)
const groupStatCards = ref([])
const typeChart = ref(null)
const hourChart = ref(null)
let charts = []

async function loadData() {
  try {
    const res = await getGroupDetail(route.params.roomId)
    group.value = res.data
    const g = res.data
    groupStatCards.value = [
      { label: '总消息', value: g.total_messages },
      { label: '群成员', value: g.member_count },
      { label: '发言人员', value: g.top_speakers.length },
      { label: '消息类型', value: Object.keys(g.type_distribution).length },
    ]
    nextTick(() => renderCharts(g))
  } catch (e) {
    console.error(e)
  }
  loading.value = false
}

function renderCharts(g) {
  import('echarts').then(echarts => {
    // 类型分布
    if (typeChart.value) {
      const t = echarts.init(typeChart.value)
      const typeMap = { text: '文本', image: '图片', file: '文件', mixed: '混合', link: '链接', revoke: '撤回', meeting: '会议', meeting_notification: '会议通知' }
      const data = Object.entries(g.type_distribution).map(([k, v]) => ({ name: typeMap[k] || k, value: v }))
      t.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c}条 ({d}%)' },
        series: [{
          type: 'pie', radius: ['35%', '60%'], center: ['50%', '55%'],
          data, label: { show: true, formatter: '{b}' },
        }],
      })
      charts.push(t)
    }
    // 时间分布
    if (hourChart.value) {
      const h = echarts.init(hourChart.value)
      const hours = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
      const data = hours.map(hh => g.hourly_distribution[hh] || 0)
      h.setOption({
        grid: { left: 40, right: 10, top: 20, bottom: 30 },
        xAxis: { type: 'category', data: hours, axisLabel: { interval: 3 } },
        yAxis: { type: 'value' },
        series: [{
          type: 'bar', data,
          itemStyle: {
            color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: '#409eff' },
                { offset: 1, color: '#79bbff' },
              ],
            },
          },
        }],
        tooltip: { trigger: 'axis', formatter: params => `${params[0].name}:00时<br/>${params[0].value}条消息` },
      })
      charts.push(h)
    }
  })
}

onMounted(loadData)
onUnmounted(() => {
  charts.forEach(c => c.dispose())
})
</script>
