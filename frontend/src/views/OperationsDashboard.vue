<template>
  <div style="padding: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h2 style="margin: 0; font-size: 22px;">📊 运营看板</h2>
      <el-radio-group v-model="period" @change="fetchData" size="small">
        <el-radio-button value="day">当天</el-radio-button>
        <el-radio-button value="week">当周</el-radio-button>
        <el-radio-button value="month">当月</el-radio-button>
        <el-radio-button value="quarter">当季</el-radio-button>
        <el-radio-button value="year">当年</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 汇总统计卡片：内/外部群分列 -->
    <el-row :gutter="16" style="margin-bottom: 20px;">
      <el-col :span="12">
        <el-card shadow="never" style="background: linear-gradient(135deg, #409eff, #337ecc); color: white;">
          <div style="display: flex; justify-content: space-between;">
            <div>
              <div style="font-size: 13px; opacity: 0.8;">内部群</div>
              <div style="font-size: 28px; font-weight: bold;">{{ s.internal.active_groups }}</div>
              <div style="font-size: 12px; opacity: 0.7;">活跃群</div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 13px; opacity: 0.8;">消息</div>
              <div style="font-size: 22px; font-weight: bold;">{{ s.internal.total_messages }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" style="background: linear-gradient(135deg, #67c23a, #529b2e); color: white;">
          <div style="display: flex; justify-content: space-between;">
            <div>
              <div style="font-size: 13px; opacity: 0.8;">外部群</div>
              <div style="font-size: 28px; font-weight: bold;">{{ s.external.active_groups }}</div>
              <div style="font-size: 12px; opacity: 0.7;">活跃群</div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 13px; opacity: 0.8;">消息</div>
              <div style="font-size: 22px; font-weight: bold;">{{ s.external.total_messages }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 连续活跃群：内/外分列 -->
    <el-row :gutter="16" style="margin-bottom: 20px;">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <b>🏠 内部群连续活跃</b>
            <span style="font-size:12px;color:#999;margin-left:8px;">
              连2天{{ c.internal.consecutive_2d }} / 连3天{{ c.internal.consecutive_3d }} / 连7天{{ c.internal.consecutive_7d }}
            </span>
          </template>
          <el-table :data="c.internal.groups" size="small" stripe style="width: 100%" max-height="280">
            <el-table-column prop="group_name" label="群名" min-width="160" />
            <el-table-column prop="max_consecutive_days" label="最长连续" width="80" />
            <el-table-column prop="monthly_active_days" label="活跃天数" width="80" />
          </el-table>
          <!-- 当前周期活跃群 -->
          <div style="margin-top:12px; padding-top:12px; border-top:1px solid #eee;">
            <div style="font-size:13px; font-weight:bold; color:#409eff; margin-bottom:8px;">
              🔥 {{ period === 'day' ? '今天' : '当前周期' }}活跃群 ({{ c.internal.today_active?.length || 0 }}个)
            </div>
            <div v-if="c.internal.today_active?.length">
              <div v-for="g in c.internal.today_active" :key="g.room_id"
                style="display:flex; justify-content:space-between; padding:4px 0; font-size:13px; border-bottom:1px solid #f5f5f5;">
                <span style="color:#333; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{{ g.group_name }}</span>
                <span style="color:#999; margin-left:8px; white-space:nowrap;">{{ g.message_count }}条</span>
              </div>
            </div>
            <div v-else style="color:#999; font-size:13px; text-align:center; padding:8px;">今天暂无活跃内部群</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <b>🏢 外部群连续活跃</b>
            <span style="font-size:12px;color:#999;margin-left:8px;">
              连2天{{ c.external.consecutive_2d }} / 连3天{{ c.external.consecutive_3d }} / 连7天{{ c.external.consecutive_7d }}
            </span>
          </template>
          <el-table :data="c.external.groups" size="small" stripe style="width: 100%" max-height="280">
            <el-table-column prop="group_name" label="群名" min-width="160" />
            <el-table-column prop="max_consecutive_days" label="最长连续" width="80" />
            <el-table-column prop="monthly_active_days" label="活跃天数" width="80" />
          </el-table>
          <!-- 外部群当天活跃 -->
          <div style="margin-top:12px; padding-top:12px; border-top:1px solid #eee;">
            <div style="font-size:13px; font-weight:bold; color:#67c23a; margin-bottom:8px;">
              🔥 {{ period === 'day' ? '今天' : '当前周期' }}活跃群 ({{ c.external.today_active?.length || 0 }}个)
            </div>
            <div v-if="c.external.today_active?.length">
              <div v-for="g in c.external.today_active" :key="g.room_id"
                style="display:flex; justify-content:space-between; padding:4px 0; font-size:13px; border-bottom:1px solid #f5f5f5;">
                <span style="color:#333; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{{ g.group_name }}</span>
                <span style="color:#999; margin-left:8px; white-space:nowrap;">{{ g.message_count }}条</span>
              </div>
            </div>
            <div v-else style="color:#999; font-size:13px; text-align:center; padding:8px;">今天暂无活跃外部群</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 产品线监控：内/外分列 -->
    <el-row :gutter="16" style="margin-bottom: 20px;">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>🔧 内部群产品线提及</b></template>
          <el-table :data="internalProducts" size="small" stripe style="width: 100%">
            <el-table-column prop="name" label="产品线" width="100" />
            <el-table-column prop="msg_count" label="消息数" width="80" />
            <el-table-column prop="group_count" label="涉及群" width="80" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><b>🔧 外部群产品线提及</b></template>
          <el-table :data="externalProducts" size="small" stripe style="width: 100%">
            <el-table-column prop="name" label="产品线" width="100" />
            <el-table-column prop="msg_count" label="消息数" width="80" />
            <el-table-column prop="group_count" label="涉及群" width="80" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 每日明细表（近7天有数据） -->
    <el-card shadow="never">
      <template #header><b>📅 每日明细</b></template>
      <el-table :data="recentDaily" size="small" stripe style="width: 100%">
        <el-table-column prop="date" label="日期" width="100" />
        <el-table-column label="内部群" width="140">
          <template #default="{row}">
            活跃 {{ row.internal_groups }} / 消息 {{ row.internal_msgs || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="外部群" width="140">
          <template #default="{row}">
            活跃 {{ row.external_groups }} / 消息 {{ row.external_msgs || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="影响业务群" width="110">
          <template #default="{row}">
            <el-tag v-if="row.impact_internal > 0" type="danger" size="small" style="margin-right:4px">内{{row.impact_internal}}</el-tag>
            <el-tag v-if="row.impact_external > 0" type="warning" size="small">外{{row.impact_external}}</el-tag>
            <span v-if="!row.impact_internal && !row.impact_external" style="color:#999;">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 最新消息速览 -->
    <el-card shadow="never" style="margin-top: 20px;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <b>💬 最新消息</b>
          <span style="font-size:12px;color:#999;">共 {{ recentMessages.length }} 条</span>
        </div>
      </template>
      <div style="max-height: 400px; overflow-y: auto;">
        <div v-for="(msg, i) in recentMessages" :key="msg.msg_id"
          style="padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; line-height: 1.5;">
          <div style="display: flex; gap: 8px; align-items: center;">
            <el-tag :type="getGroupType(msg.room_id) === 'internal' ? '' : 'success'" size="small" style="flex-shrink:0;">
              {{ msg.group_name || '(未命名)' }}
            </el-tag>
            <span style="color: #999; font-size: 11px;">{{ formatTime(msg.msg_time) }}</span>
            <span v-if="msg.sender_name" style="color: #666; font-size: 12px; margin-left: auto;">{{ msg.sender_name }}</span>
          </div>
        </div>
        <div v-if="recentMessages.length === 0" style="color:#999; text-align:center; padding:30px;">
          暂无消息数据
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'OperationsDashboard',
  setup() {
    const period = ref('day')
    const summary = ref({ internal: { active_groups: 0, total_messages: 0 }, external: { active_groups: 0, total_messages: 0 } })
    const continuity = ref({ internal: { groups: [], consecutive_2d: 0, consecutive_3d: 0, consecutive_7d: 0 }, external: { groups: [], consecutive_2d: 0, consecutive_3d: 0, consecutive_7d: 0 } })
    const dailySummary = ref([])
    const dailyImpact = ref([])
    const productByType = ref({})
    const recentMessages = ref([])
    const groupTypeMap = ref({})

    const s = computed(() => summary.value)
    const c = computed(() => continuity.value)

    const recentDaily = computed(() => {
      const last = dailySummary.value.slice(-14)
      return last.map(d => {
        const impact = dailyImpact.value.find(i => i.date === d.date)
        return {
          ...d,
          impact_internal: impact ? impact.internal : 0,
          impact_external: impact ? impact.external : 0,
        }
      }).filter(d => d.total_groups > 0).reverse()
    })

    const internalProducts = computed(() => {
      return Object.entries(productByType.value).map(([name, data]) => ({
        name,
        msg_count: data.internal.messages,
        group_count: data.internal.groups,
      })).filter(p => p.msg_count > 0 || p.group_count > 0)
    })

    const externalProducts = computed(() => {
      return Object.entries(productByType.value).map(([name, data]) => ({
        name,
        msg_count: data.external.messages,
        group_count: data.external.groups,
      })).filter(p => p.msg_count > 0 || p.group_count > 0)
    })

    const fetchData = async () => {
      try {
        const res = await axios.get(`/api/operations-dashboard?period=${period.value}`)
        const data = res.data
        summary.value = data.summary
        continuity.value = data.continuity
        dailySummary.value = data.daily_summary
        dailyImpact.value = data.daily_impact_groups
        productByType.value = data.product_by_type
      } catch (e) {
        console.error('获取运营数据失败:', e)
      }
    }

    const fetchRecentMessages = async () => {
      try {
        const res = await axios.get('/api/recent-messages?limit=30')
        recentMessages.value = res.data.items
      } catch (e) {
        console.error('获取最新消息失败:', e)
      }
    }

    const fetchGroupTypes = async () => {
      try {
        const res = await axios.get('/api/groups-with-stats')
        const map = {}
        res.data.groups.forEach(g => { map[g.room_id] = g.group_type })
        groupTypeMap.value = map
      } catch (e) {}
    }

    const getGroupType = (roomId) => groupTypeMap.value[roomId] || 'external'

    const formatTime = (t) => {
      if (!t) return ''
      return t.slice(11, 19)
    }

    const truncate = (text, max) => {
      if (!text) return ''
      return text.length > max ? text.slice(0, max) + '...' : text
    }

    onMounted(() => {
      fetchData()
      fetchRecentMessages()
      fetchGroupTypes()
    })

    return { period, s, c, dailySummary, dailyImpact, productByType, recentDaily, internalProducts, externalProducts, recentMessages, getGroupType, formatTime, truncate, fetchData }
  }
}
</script>
