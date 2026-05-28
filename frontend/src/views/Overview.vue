<template>
  <div>
    <!-- 页面标题 -->
    <div style="margin-bottom: 20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <h1 style="margin:0; font-size:22px; font-weight:600;">总览看板</h1>
          <p style="color:#909399; margin:4px 0 0 0; font-size:13px;">消息总览与群聊活跃度分析</p>
        </div>
        <UpdateTime :refresh="60000" />
      </div>
    </div>

    <!-- Row 1: 4统计卡片 等宽 -->
    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="6" v-for="card in statCards" :key="card.label" style="margin-bottom:12px;">
        <el-card shadow="never" :body-style="{ padding: '18px 20px' }"
          style="border:1px solid #ebeef5; border-radius:8px;">
          <div style="display:flex; align-items:center; gap:14px;">
            <div :style="`width:44px;height:44px;border-radius:12px;background:${card.color}12;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;`">
              {{ card.icon }}
            </div>
            <div style="min-width:0;">
              <div style="font-size:24px;font-weight:700;line-height:1.2;">{{ card.value }}</div>
              <div style="color:#909399;font-size:12px;margin-top:2px;">{{ card.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 2: 4列等宽 今日活跃 / 群类型 / 故障 / 产品线 -->
    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="6" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #ebeef5; border-radius:8px; height:100%;">
          <template #header><span style="font-size:13px; font-weight:500;">🔥 今日活跃群</span></template>
          <div style="padding:4px 0;">
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f2f2f2;">
              <span style="font-size:13px;">🏢 内部群</span>
              <span style="font-size:22px;font-weight:700;color:#409eff;">{{ overview.today_internal_active ?? '-' }}</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f2f2f2;">
              <span style="font-size:13px;">🌐 外部群</span>
              <span style="font-size:22px;font-weight:700;color:#67c23a;">{{ overview.today_external_active ?? '-' }}</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;">
              <span style="font-size:13px;font-weight:500;">合计</span>
              <span style="font-size:22px;font-weight:700;">{{ (overview.today_internal_active || 0) + (overview.today_external_active || 0) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #ebeef5; border-radius:8px; height:100%;">
          <template #header><span style="font-size:13px; font-weight:500;">🏘️ 群类型分布</span></template>
          <div style="padding:16px 4px;">
            <div v-for="gt in groupTypeDist" :key="gt.label" style="display:flex;align-items:center;gap:12px;padding:8px 0;">
              <div :style="`width:10px;height:10px;border-radius:50%;background:${gt.color};flex-shrink:0;`"></div>
              <div style="flex:1;font-size:13px;">{{ gt.label }}</div>
              <div style="font-weight:700;font-size:20px;">{{ gt.value }}</div>
              <div style="color:#909399;font-size:12px;">个</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #ebeef5; border-radius:8px; height:100%;">
          <template #header><span style="font-size:13px; font-weight:500;">🚨 外部群故障统计</span></template>
          <div style="padding:4px 0;">
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f2f2f2;">
              <span style="font-size:13px;">🔴 严重故障</span>
              <span style="font-size:22px;font-weight:700;color:#f56c6c;">{{ overview.ext_fault_critical || 0 }}</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f2f2f2;">
              <span style="font-size:13px;">🟡 需关注</span>
              <span style="font-size:22px;font-weight:700;color:#e6a23c;">{{ overview.ext_fault_high || 0 }}</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;">
              <span style="font-size:13px;font-weight:500;">影响业务合计</span>
              <span style="font-size:22px;font-weight:700;color:#f56c6c;">{{ (overview.ext_fault_critical || 0) + (overview.ext_fault_high || 0) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #ebeef5; border-radius:8px; height:100%;">
          <template #header><span style="font-size:13px; font-weight:500;">📦 外部群产品线分布</span></template>
          <div style="padding:4px 0;max-height:190px;overflow-y:auto;">
            <div v-for="([name, cnt], i) in productList" :key="name"
              style="display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f5f5f5;">
              <div style="flex:1;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ name }}</div>
              <div style="width:32px;text-align:right;font-weight:600;font-size:13px;">{{ cnt }}</div>
              <div style="flex:1;margin-left:8px;">
                <div style="height:5px;border-radius:3px;background:#e8f4fd;overflow:hidden;">
                  <div :style="`height:100%;border-radius:3px;background:#409eff;width:${maxProduct > 0 ? (cnt/maxProduct*100) : 0}%;transition:width 0.3s;`"></div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="24" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #ebeef5; border-radius:8px;">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:13px; font-weight:500;">🔔 需要关注（售后负责人）</span>
              <el-tag v-if="attentionItems.length" :type="attentionSeverityType" size="small">
                {{ attentionItems.length }} 条待关注
              </el-tag>
            </div>
          </template>
          <div v-if="attentionItems.length === 0" style="color:#909399;text-align:center;padding:24px;font-size:13px;">
            今日暂无需要特别关注的事项
          </div>
          <div v-for="(item, i) in attentionItems" :key="item.room_id + i"
               style="display:flex;align-items:flex-start;padding:14px 0;border-bottom:1px solid #f5f5f5;cursor:pointer;"
               @click="$router.push('/groups/'+item.room_id)">
            <div :style="`width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;margin-right:12px;background:${
              item.severity === 'high' ? '#f56c6c12' : '#e6a23c12'
            }`">
              {{ item.severity === 'high' ? '🔴' : (item.severity === 'medium' ? '🟡' : '🟢') }}
            </div>
            <div style="flex:1;min-width:0;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <el-tag :type="item.severity === 'high' ? 'danger' : 'warning'" size="small" effect="plain">
                  {{ item.type }}
                </el-tag>
                <span style="font-size:13px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                  {{ item.group_name }}
                </span>
              </div>
              <div style="font-size:12px;color:#606266;line-height:1.5;">{{ item.summary }}</div>
              <div style="font-size:11px;color:#909399;margin-top:2px;">{{ item.detail }}</div>
            </div>
            <div style="margin-left:8px;font-size:11px;color:#c0c4cc;flex-shrink:0;">→</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 3: 2列 趋势图 + 今日最活跃群 -->
    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="12" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #ebeef5; border-radius:8px; height:100%;">
          <template #header><span style="font-size:13px; font-weight:500;">📈 近7天消息趋势</span></template>
          <div ref="trendChartRef" style="height:280px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #ebeef5; border-radius:8px; height:100%;">
          <template #header><span style="font-size:13px; font-weight:500;">🔥 今日最活跃群 TOP10</span></template>
          <div v-if="todayGroups.length === 0" style="color:#909399;text-align:center;padding:30px;font-size:13px;">暂无数据</div>
          <div v-for="(g, i) in todayGroups" :key="g.room_id" 
               style="display:flex;align-items:center;padding:9px 0;border-bottom:1px solid #f2f2f2;cursor:pointer;"
               @click="$router.push('/groups/'+g.room_id)">
            <div :style="`width:22px;height:22px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;margin-right:10px;flex-shrink:0;${
              i < 3 ? 'background:#f56c6c15;color:#f56c6c;' : 'background:#f2f2f2;color:#909399;'
            }`">{{ i+1 }}</div>
            <div style="margin-right:8px;flex-shrink:0;">{{ g.group_type === 'external' ? '🌐' : '🏢' }}</div>
            <div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;">
              {{ g.group_name || g.room_id.slice(0, 16) }}
            </div>
            <div style="font-weight:700;color:#409eff;font-size:15px;">{{ g.count }}</div>
            <div style="color:#909399;margin-left:4px;font-size:12px;">条</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 4: 2列等宽 外部群故障 + 发言排行 -->
    <el-row :gutter="16">
      <el-col :span="12" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #ebeef5; border-radius:8px;">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:13px; font-weight:500;">🚨 外部群故障检测</span>
              <el-tag v-if="faultGroups.length > 0" size="small" :type="criticalCount > 0 ? 'danger' : 'warning'">
                {{ criticalCount }}严重 / {{ highCount }}关注
              </el-tag>
            </div>
          </template>
          <div v-if="faultGroups.length === 0" style="color:#909399;text-align:center;padding:30px;font-size:13px;">今日暂无故障</div>
          <div v-for="g in faultGroups" :key="g.room_id"
               style="display:flex;align-items:flex-start;padding:10px 0;border-bottom:1px solid #f2f2f2;cursor:pointer;"
               @click="showFaultDetail(g)">
            <div :style="`width:8px;height:8px;border-radius:50%;margin-top:5px;margin-right:10px;flex-shrink:0;background:${
              g.level === 2 ? '#f56c6c' : '#e6a23c'
            }`"></div>
            <div style="flex:1;min-width:0;">
              <div style="font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ g.name }}</div>
              <div style="font-size:11px;color:#909399;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                {{ g.snippet || '无消息内容' }}
              </div>
            </div>
            <div :style="`font-size:11px;padding:2px 8px;border-radius:4px;flex-shrink:0;margin-left:8px;${
              g.level === 2 ? 'background:#f56c6c15;color:#f56c6c;' : 'background:#e6a23c15;color:#e6a23c;'
            }`">{{ g.level === 2 ? '严重' : '关注' }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #ebeef5; border-radius:8px; height:100%;">
          <template #header><span style="font-size:13px; font-weight:500;">🌐 外部群·消息最多 TOP5</span></template>
          <div v-if="topExtGroups.length === 0" style="color:#909399;text-align:center;padding:30px;font-size:13px;">暂无数据</div>
          <div v-for="(g, i) in topExtGroups" :key="g.room_id"
               style="display:flex;align-items:center;padding:9px 0;border-bottom:1px solid #f2f2f2;cursor:pointer;"
               @click="$router.push('/groups/'+g.room_id)">
            <div :style="`width:22px;height:22px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;margin-right:10px;flex-shrink:0;${
              i < 3 ? 'background:#67c23a15;color:#67c23a;' : 'background:#f2f2f2;color:#909399;'
            }`">{{ i+1 }}</div>
            <div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;">
              {{ g.group_name || '(未命名)' }}
            </div>
            <div style="font-weight:700;color:#67c23a;font-size:15px;">{{ g.total_messages }}</div>
            <div style="color:#909399;margin-left:4px;font-size:12px;">条</div>
            <div v-if="g.member_count" style="color:#909399;margin-left:8px;font-size:11px;">· {{ g.member_count }}人</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row 5: 发言排行 -->
    <el-row :gutter="16" style="margin-bottom: 16px;">
      <el-col :span="24" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #ebeef5; border-radius:8px;">
          <template #header><span style="font-size:13px; font-weight:500;">🏆 发言排行 TOP10</span></template>
          <div v-if="topSpeakers.length === 0" style="color:#909399;text-align:center;padding:30px;font-size:13px;">暂无数据</div>
          <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:0;">
            <div v-for="(p, i) in topSpeakers" :key="p.user_id"
                 style="display:flex;align-items:center;padding:9px 12px;border-bottom:1px solid #f2f2f2;cursor:pointer;"
                 @click="$router.push('/persons/'+p.user_id)">
              <div :style="`width:22px;height:22px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;margin-right:10px;flex-shrink:0;${
                i < 3 ? 'background:#f56c6c15;color:#f56c6c;' : 'background:#f2f2f2;color:#909399;'
              }`">{{ i+1 }}</div>
              <div style="margin-right:8px;flex-shrink:0;">{{ p.is_internal ? '🔵' : '🟢' }}</div>
              <div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;">
                {{ p.display_name }}
              </div>
              <div style="font-weight:700;color:#409eff;font-size:15px;">{{ p.total_messages }}</div>
              <div style="color:#909399;margin-left:4px;font-size:12px;">条</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>

  <!-- 故障详情弹窗 -->
  <el-dialog v-model="faultDialogVisible" :title="'🚨 故障详情'" width="500px">
    <template v-if="selectedFault">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="群名称">{{ selectedFault.name }}</el-descriptions-item>
        <el-descriptions-item label="故障等级">
          <el-tag :type="selectedFault.level === 2 ? 'danger' : 'warning'" size="small">
            {{ selectedFault.level === 2 ? '严重' : '需关注' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="匹配关键词">{{ selectedFault.keyword || '-' }}</el-descriptions-item>
        <el-descriptions-item label="近50条消息数">{{ selectedFault.msg_count }}</el-descriptions-item>
        <el-descriptions-item label="相关消息片段">
          <div style="background:#f5f7fa;padding:10px;border-radius:4px;font-size:12px;line-height:1.6;word-break:break-all;">
            {{ selectedFault.snippet || '无' }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
      <div style="margin-top:16px;text-align:center;">
        <el-button size="small" @click="$router.push('/groups/'+selectedFault.room_id)">查看群详情</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import UpdateTime from '@/components/UpdateTime.vue'

export default {
  name: 'Overview',
  components: { UpdateTime },
  setup() {
    const overview = ref({})
    const todayGroups = ref([])
    const topSpeakers = ref([])
    const groupTypeDist = ref([])
    const trendChartRef = ref(null)
    const faultGroups = ref([])
    const faultDialogVisible = ref(false)
    const selectedFault = ref(null)
    const attentionItems = ref([])
    const topExtGroups = ref([])
    let chartInstance = null

    const criticalCount = computed(() => faultGroups.value.filter(g => g.level === 2).length)
    const highCount = computed(() => faultGroups.value.filter(g => g.level === 1).length)

    const attentionSeverityType = computed(() => {
      const hasHigh = attentionItems.value.some(i => i.severity === 'high')
      return hasHigh ? 'danger' : 'warning'
    })

    const statCards = computed(() => [
      { icon: '💬', label: '总消息', value: overview.value.total_messages ?? '-', color: '#409eff' },
      { icon: '🏢', label: '今日内部消息', value: overview.value.today_internal_messages ?? '-', color: '#409eff' },
      { icon: '🌐', label: '今日外部消息', value: overview.value.today_external_messages ?? '-', color: '#67c23a' },
      { icon: '👥', label: '涉事群聊', value: overview.value.total_groups ?? '-', color: '#909399' },
    ])

    const productList = computed(() => {
      const pc = overview.value.product_counts || {}
      return Object.entries(pc).sort((a, b) => b[1] - a[1])
    })

    const maxProduct = computed(() => {
      return Math.max(...productList.value.map(([_, v]) => v), 1)
    })

    function showFaultDetail(g) {
      selectedFault.value = g
      faultDialogVisible.value = true
    }

    async function loadData() {
      try {
        const res = await axios.get('/api/overview')
        const d = res.data
        overview.value = d
        todayGroups.value = (d.top_groups_today || []).slice(0, 10)
        topSpeakers.value = d.top_speakers || []
        faultGroups.value = d.ext_fault_groups || []
        attentionItems.value = d.attention_items || []
        groupTypeDist.value = [
          { label: '内部群', value: d.internal_groups, color: '#409eff' },
          { label: '外部群', value: d.external_groups, color: '#67c23a' },
        ]
        renderTrendChart((d.message_trend_7d || []).filter(t => t && t.date))
      } catch (e) {
        console.error('加载数据失败', e)
      }
      // 加载外部群TOP5
      try {
        const res2 = await axios.get('/api/groups-with-stats')
        const allGroups = res2.data.groups || []
        const extSorted = allGroups
          .filter(g => g.group_type === 'external')
          .sort((a, b) => (b.total_messages || 0) - (a.total_messages || 0))
        topExtGroups.value = extSorted.slice(0, 5)
      } catch(e) {
        console.error('加载外部群TOP5失败', e)
      }
    }

    function renderTrendChart(trendData) {
      nextTick(() => {
        if (!trendChartRef.value) return
        import('echarts').then(echarts => {
          if (chartInstance) chartInstance.dispose()
          chartInstance = echarts.init(trendChartRef.value)
          chartInstance.setOption({
            grid: { left: 50, right: 20, top: 20, bottom: 30 },
            xAxis: {
              type: 'category',
              data: trendData.map(d => d.date.slice(5)),
              axisLabel: { color: '#909399', fontSize: 11 },
              axisLine: { lineStyle: { color: '#ebeef5' } },
              axisTick: { show: false },
            },
            yAxis: {
              type: 'value',
              axisLabel: { color: '#909399', fontSize: 11 },
              splitLine: { lineStyle: { color: '#f5f5f5', type: 'dashed' } },
            },
            series: [{
              data: trendData.map(d => d.count),
              type: 'line',
              smooth: true,
              lineStyle: { color: '#409eff', width: 2.5 },
              areaStyle: {
                color: {
                  type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                  colorStops: [
                    { offset: 0, color: 'rgba(64,158,255,0.25)' },
                    { offset: 1, color: 'rgba(64,158,255,0.02)' },
                  ],
                },
              },
              itemStyle: { color: '#409eff' },
              symbol: 'circle',
              symbolSize: 6,
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

    return {
      overview, statCards, todayGroups, topSpeakers, groupTypeDist,
      trendChartRef, productList, maxProduct, faultGroups,
      faultDialogVisible, selectedFault, showFaultDetail,
      criticalCount, highCount, attentionItems, attentionSeverityType,
      topExtGroups,
    }
  }
}
</script>
