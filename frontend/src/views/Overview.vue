<template>
  <div>
    <!-- 页面标题 -->
    <div style="margin-bottom: 20px;">
      <h1 style="margin:0; font-size:24px;">企业微信消息分析平台</h1>
      <p style="color:#999; margin:4px 0 0 0;">消息总览与群聊活跃度分析</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 20px;">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card shadow="hover" :body-style="{ padding: '20px' }">
          <div style="display:flex; align-items:center; gap:16px;">
            <div :style="`width:48px;height:48px;border-radius:12px;background:${card.color};display:flex;align-items:center;justify-content:center;font-size:22px;`">
              {{ card.icon }}
            </div>
            <div>
              <div style="font-size:28px;font-weight:bold;">{{ card.value }}</div>
              <div style="color:#999;font-size:13px;">{{ card.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第二行：趋势图 + 群分布 -->
    <el-row :gutter="16" style="margin-bottom: 20px;">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header><span>📈 近7天消息趋势</span></template>
          <div ref="trendChartRef" style="height:280px;"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span>🏘️ 群类型分布</span></template>
          <div style="display:flex;flex-direction:column;gap:20px;padding:20px;">
            <div v-for="gt in groupTypeDist" :key="gt.label" style="display:flex;align-items:center;gap:12px;">
              <div :style="`width:12px;height:12px;border-radius:50%;background:${gt.color};`"></div>
              <div style="flex:1;">{{ gt.label }}</div>
              <div style="font-weight:bold;font-size:18px;">{{ gt.value }}</div>
              <div style="color:#999;">个</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第三行：今日活跃群 + 发言排行 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>🔥 今日最活跃群 TOP10</span></template>
          <div v-if="todayGroups.length === 0" style="color:#999;text-align:center;padding:20px;">暂无数据</div>
          <div v-for="(g, i) in todayGroups" :key="g.room_id" 
               style="display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #f0f0f0;"
               :style="{cursor:'pointer'}" @click="$router.push('/groups/'+g.room_id)">
            <div style="width:24px;font-weight:bold;color:#999;">{{ i+1 }}</div>
            <div style="margin-right:8px;">{{ g.group_type === 'external' ? '🌐' : '🏢' }}</div>
            <div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
              {{ g.group_name || g.room_id.slice(0, 16) }}...
            </div>
            <div style="font-weight:bold;color:#409eff;">{{ g.count }}</div>
            <div style="color:#999;margin-left:4px;">条</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>🏆 发言排行 TOP10</span></template>
          <div v-if="topSpeakers.length === 0" style="color:#999;text-align:center;padding:20px;">暂无数据</div>
          <div v-for="(p, i) in topSpeakers" :key="p.user_id"
               style="display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #f0f0f0;
                      cursor:pointer;" @click="$router.push('/persons/'+p.user_id)">
            <div style="width:24px;font-weight:bold;color:#999;">{{ i+1 }}</div>
            <div style="margin-right:8px;">{{ p.is_internal ? '🔵' : '🟢' }}</div>
            <div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
              {{ p.display_name }}
            </div>
            <div v-if="p.email" style="color:#999;font-size:12px;margin-right:8px;">{{ p.email }}</div>
            <div style="font-weight:bold;color:#409eff;">{{ p.total_messages }}</div>
            <div style="color:#999;margin-left:4px;">条</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getOverview } from '@/api/index.js'

const statCards = ref([])
const todayGroups = ref([])
const topSpeakers = ref([])
const groupTypeDist = ref([])
const trendChartRef = ref(null)

let chartInstance = null

async function loadData() {
  try {
    const res = await getOverview()
    const d = res.data
    statCards.value = [
      { icon: '💬', label: '总消息数', value: d.total_messages, color: '#409eff' },
      { icon: '👥', label: '涉及群聊', value: d.total_groups, color: '#67c23a' },
      { icon: '👤', label: '发言人员', value: d.total_persons, color: '#e6a23c' },
      { icon: '📅', label: '今日消息', value: d.today_messages, color: '#f56c6c' },
    ]
    todayGroups.value = d.top_groups_today.slice(0, 10)
    topSpeakers.value = d.top_speakers
    groupTypeDist.value = [
      { label: '内部群', value: d.internal_groups, color: '#409eff' },
      { label: '外部群', value: d.external_groups, color: '#67c23a' },
    ]
    renderTrendChart(d.message_trend_7d)
  } catch (e) {
    console.error('加载数据失败', e)
  }
}

function renderTrendChart(trendData) {
  nextTick(() => {
    if (!trendChartRef.value) return
    import('echarts').then(echarts => {
      if (chartInstance) chartInstance.dispose()
      chartInstance = echarts.init(trendChartRef.value)
      chartInstance.setOption({
        grid: { left: 40, right: 20, top: 20, bottom: 30 },
        xAxis: {
          type: 'category',
          data: trendData.map(d => d.date.slice(5)),
          axisLabel: { color: '#999' },
        },
        yAxis: { type: 'value', axisLabel: { color: '#999' } },
        series: [{
          data: trendData.map(d => d.count),
          type: 'line',
          smooth: true,
          lineStyle: { color: '#409eff', width: 2 },
          areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(64,158,255,0.3)' },
                { offset: 1, color: 'rgba(64,158,255,0.02)' },
              ],
            },
          },
          itemStyle: { color: '#409eff' },
        }],
        tooltip: {
          trigger: 'axis',
          formatter: params => `${params[0].name}<br/>消息数: <b>${params[0].value}</b>`,
        },
      })
    })
  })
}

onMounted(loadData)
onUnmounted(() => {
  if (chartInstance) chartInstance.dispose()
})
</script>
