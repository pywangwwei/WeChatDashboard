<template>
  <div style="padding: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h2 style="margin: 0; font-size: 22px;">📋 当日看板</h2>
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="color:#999;font-size:14px;">{{ selectedDate }}</span>
        <UpdateTime :refresh="60000" />
      </div>
    </div>

    <!-- Tab切换 -->
    <el-tabs v-model="activeTab" type="border-card" style="margin-bottom: 16px;">
      <el-tab-pane label="📋 当日看板" name="daily">
        <!-- 筛选 -->
        <el-input v-model="searchQuery" placeholder="搜索群名..." size="small" clearable
          style="width: 300px; margin-bottom: 16px;" @input="onSearch" />

        <!-- 四大模块 -->
        <el-row :gutter="16" style="margin-bottom: 20px;">
          <!-- 内部群当日活跃 -->
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <b>🏠 内部群 · 当日活跃</b>
                  <span style="font-size: 12px; color: #999;">共 {{ internalToday.length }} 个群</span>
                </div>
              </template>
              <el-table :data="filteredInternalToday" size="small" stripe style="width: 100%" max-height="420"
                @row-click="goToGroup">
                <el-table-column prop="rank" label="#" width="36" align="center" />
                <el-table-column prop="group_name" label="群名" min-width="180">
                  <template #default="{ row }">
                    <span style="cursor:pointer; color:#409eff;">{{ row.group_name }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="message_count" label="消息" width="60" align="center" sortable />
              </el-table>
              <div v-if="filteredInternalToday.length === 0" style="color:#999; text-align:center; padding:30px;">
                暂无数据
              </div>
            </el-card>
          </el-col>

          <!-- 外部群当日活跃 -->
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <b>🌐 外部群 · 当日活跃</b>
                  <span style="font-size: 12px; color: #999;">共 {{ externalToday.length }} 个群</span>
                </div>
              </template>
              <el-table :data="filteredExternalToday" size="small" stripe style="width: 100%" max-height="420"
                @row-click="goToGroup">
                <el-table-column prop="rank" label="#" width="36" align="center" />
                <el-table-column prop="group_name" label="群名" min-width="180">
                  <template #default="{ row }">
                    <span style="cursor:pointer; color:#409eff;">{{ row.group_name }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="message_count" label="消息" width="60" align="center" sortable />
              </el-table>
              <div v-if="filteredExternalToday.length === 0" style="color:#999; text-align:center; padding:30px;">
                暂无数据
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <!-- 内部群总消息排行 -->
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <b>📊 内部群 · 总消息排行</b>
                  <span style="font-size: 12px; color: #999;">共 {{ internalTotal.length }} 个群</span>
                </div>
              </template>
              <el-table :data="filteredInternalTotal" size="small" stripe style="width: 100%" max-height="420"
                @row-click="goToGroup">
                <el-table-column prop="rank" label="#" width="36" align="center" />
                <el-table-column prop="group_name" label="群名" min-width="180">
                  <template #default="{ row }">
                    <span style="cursor:pointer; color:#409eff;">{{ row.group_name }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="total_messages" label="消息" width="60" align="center" sortable />
              </el-table>
              <div v-if="filteredInternalTotal.length === 0" style="color:#999; text-align:center; padding:30px;">
                暂无数据
              </div>
            </el-card>
          </el-col>

          <!-- 外部群总消息排行 -->
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <b>📊 外部群 · 总消息排行</b>
                  <span style="font-size: 12px; color: #999;">共 {{ externalTotal.length }} 个群</span>
                </div>
              </template>
              <el-table :data="filteredExternalTotal" size="small" stripe style="width: 100%" max-height="420"
                @row-click="goToGroup">
                <el-table-column prop="rank" label="#" width="36" align="center" />
                <el-table-column prop="group_name" label="群名" min-width="180">
                  <template #default="{ row }">
                    <span style="cursor:pointer; color:#409eff;">{{ row.group_name }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="total_messages" label="消息" width="60" align="center" sortable />
              </el-table>
              <div v-if="filteredExternalTotal.length === 0" style="color:#999; text-align:center; padding:30px;">
                暂无数据
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="🧪 POC/测试群" name="poc">
        <el-input v-model="pocSearch" placeholder="搜索POC群..." size="small" clearable
          style="width: 300px; margin-bottom: 16px;" />
        <el-row :gutter="16">
          <el-col v-for="prod in pocByProduct" :key="prod.name" :span="12" style="margin-bottom: 16px;">
            <el-card shadow="never">
              <template #header>
                <b>{{ prod.icon }} {{ prod.name }}</b>
                <span style="font-size:12px;color:#999;margin-left:8px;">{{ prod.groups.length }}个POC / {{ prod.total }}条</span>
              </template>
              <el-table :data="filteredPoc(prod)" size="small" stripe style="width: 100%" max-height="300"
                @row-click="goToGroup">
                <el-table-column prop="rank" label="#" width="30" align="center" />
                <el-table-column prop="group_name" label="群名" min-width="150">
                  <template #default="{ row }"><span style="cursor:pointer;color:#409eff;">{{ row.group_name }}</span></template>
                </el-table-column>
                <el-table-column prop="group_type" label="类型" width="50" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.group_type === 'internal' ? '' : 'success'" size="small">{{ row.group_type === 'internal' ? '内' : '外' }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="message_count" label="消息" width="60" align="center" sortable />
              </el-table>
            </el-card>
          </el-col>
        </el-row>
        <div v-if="pocByProduct.length === 0" style="color:#999; text-align:center; padding:30px;">暂无POC群</div>
      </el-tab-pane>

      <el-tab-pane label="🔧 产品问题群" name="product">
        <el-input v-model="prodSearch" placeholder="搜索产品问题群..." size="small" clearable
          style="width: 300px; margin-bottom: 16px;" />
        <el-row :gutter="16">
          <el-col v-for="prod in productGroups" :key="prod.name" :span="12" style="margin-bottom: 16px;">
            <el-card shadow="never">
              <template #header>
                <b>{{ prod.name }}</b>
                <span style="font-size:12px;color:#999;margin-left:8px;">{{ prod.groups.length }}个群 / {{ prod.total }}条</span>
              </template>
              <el-table :data="filteredProduct(prod)" size="small" stripe style="width: 100%" max-height="300"
                @row-click="goToGroup">
                <el-table-column prop="rank" label="#" width="30" align="center" />
                <el-table-column prop="group_name" label="群名" min-width="160">
                  <template #default="{ row }"><span style="cursor:pointer;color:#409eff;">{{ row.group_name }}</span></template>
                </el-table-column>
                <el-table-column prop="group_type" label="类型" width="50" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.group_type === 'internal' ? '' : 'success'" size="small">{{ row.group_type === 'internal' ? '内' : '外' }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="message_count" label="消息" width="60" align="center" sortable />
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="⏰ 超期POC群" name="overdue">
        <el-alert title="连续10个工作日内仍有消息的POC项目（超期未结束）" type="warning" :closable="false" show-icon
          style="margin-bottom: 16px;" />
        <el-input v-model="overdueSearch" placeholder="搜索超期POC群..." size="small" clearable
          style="width: 300px; margin-bottom: 16px;" />
        <el-row :gutter="16">
          <el-col v-for="prod in overdueByProduct" :key="prod.name" :span="12" style="margin-bottom: 16px;">
            <el-card shadow="never">
              <template #header>
                <b>{{ prod.icon }} {{ prod.name }}</b>
                <span style="font-size:12px;color:#f56c6c;margin-left:8px;">{{ prod.groups.length }}个超期POC / {{ prod.total }}条消息</span>
              </template>
              <el-table :data="filteredOverdue(prod)" size="small" stripe style="width: 100%" max-height="300"
                @row-click="goToGroup">
                <el-table-column prop="rank" label="#" width="30" align="center" />
                <el-table-column prop="group_name" label="群名" min-width="150">
                  <template #default="{ row }"><span style="cursor:pointer;color:#f56c6c;">{{ row.group_name }}</span></template>
                </el-table-column>
                <el-table-column prop="message_count" label="消息" width="60" align="center" sortable />
                <el-table-column prop="last_active" label="最后活跃" width="100" align="center" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>
        <div v-if="overdueByProduct.length === 0" style="color:#999; text-align:center; padding:30px;">
          没有超期POC群
        </div>
      </el-tab-pane>

      <el-tab-pane label="⭐ VIP客户群" name="vip">
        <el-input v-model="vipSearch" placeholder="搜索VIP客户群..." size="small" clearable
          style="width: 300px; margin-bottom: 16px;" />
        <el-row :gutter="16">
          <el-col v-for="prod in vipByProduct" :key="prod.name" :span="12" style="margin-bottom: 16px;">
            <el-card shadow="never">
              <template #header>
                <b>{{ prod.icon }} {{ prod.name }}</b>
                <span style="font-size:12px;color:#e6a23c;margin-left:8px;">{{ prod.groups.length }}个VIP / {{ prod.total }}条</span>
              </template>
              <el-table :data="filteredVip(prod)" size="small" stripe style="width: 100%" max-height="300"
                @row-click="goToGroup">
                <el-table-column prop="rank" label="#" width="30" align="center" />
                <el-table-column prop="group_name" label="群名" min-width="150">
                  <template #default="{ row }"><span style="cursor:pointer;color:#e6a23c;">{{ row.group_name }}</span></template>
                </el-table-column>
                <el-table-column prop="group_type" label="类型" width="50" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.group_type === 'internal' ? '' : 'success'" size="small">{{ row.group_type === 'internal' ? '内' : '外' }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="message_count" label="消息" width="60" align="center" sortable />
                <el-table-column prop="last_active" label="最后活跃" width="90" align="center" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>
        <div v-if="vipByProduct.length === 0" style="color:#999; text-align:center; padding:30px;">
          暂无VIP客户群
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import UpdateTime from '@/components/UpdateTime.vue'

export default {
  name: 'DailyBoard',
  components: { UpdateTime },
  setup() {
    const router = useRouter()
    const todayStr = new Date().toISOString().slice(0, 10)
    const selectedDate = ref(todayStr)
    const searchQuery = ref('')
    const pocSearch = ref('')
    const prodSearch = ref('')
    const overdueSearch = ref('')
    const vipSearch = ref('')
    const activeTab = ref('daily')
    const internalToday = ref([])
    const externalToday = ref([])
    const internalTotal = ref([])
    const externalTotal = ref([])
    const allGroups = ref([])
    const allMessages = ref([])
    const productGroups = ref([])
    const displayLimit = 20

    const formatDate = (d) => {
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${y}-${m}-${day}`
    }

    const filterBySearch = (list) => {
      if (!searchQuery.value) return list.slice(0, displayLimit)
      const q = searchQuery.value.toLowerCase()
      return list.filter(g => g.group_name.toLowerCase().includes(q)).slice(0, displayLimit)
    }

    const addRank = (list) => list.map((g, i) => ({ ...g, rank: i + 1 }))

    const filteredInternalToday = computed(() => addRank(filterBySearch(internalToday.value)))
    const filteredExternalToday = computed(() => addRank(filterBySearch(externalToday.value)))
    const filteredInternalTotal = computed(() => addRank(filterBySearch(internalTotal.value)))
    const filteredExternalTotal = computed(() => addRank(filterBySearch(externalTotal.value)))

    // POC群过滤
    const filteredPocGroups = computed(() => {
      const list = allGroups.value.filter(g =>
        /POC|poc|测试|Pilot/.test(g.group_name)
      ).sort((a,b) => (b.total_messages || 0) - (a.total_messages || 0)).map((g,i)=>({...g, rank:i+1, message_count: g.total_messages}))
      if (!pocSearch.value) return list.slice(0, displayLimit)
      const q = pocSearch.value.toLowerCase()
      return list.filter(g => g.group_name.toLowerCase().includes(q)).slice(0, displayLimit)
    })

    // 产品线
    const PRODUCT_NAMES = ['QData', 'QFusion', 'QPlus', 'QOne', 'QCP', 'QCS', 'ODM', 'QMonitor', 'PolarDB', 'ZStack']

    const filteredProduct = (prod) => {
      let list = prod.groups || []
      if (!prodSearch.value) return list.slice(0, displayLimit)
      const q = prodSearch.value.toLowerCase()
      return list.filter(g => g.group_name.toLowerCase().includes(q)).slice(0, displayLimit)
    }

    // POC群按产品类型分组
    const pocByProduct = computed(() => {
      const groups = allGroups.value.filter(g =>
        /POC|poc|测试|Pilot/.test(g.group_name)
      )
      return buildProductGroups(groups)
    })

    const filteredPoc = (prod) => {
      let list = prod.groups || []
      if (!pocSearch.value) return list.slice(0, displayLimit)
      const q = pocSearch.value.toLowerCase()
      return list.filter(g => g.group_name.toLowerCase().includes(q)).slice(0, displayLimit)
    }

    // 超期POC群：按产品类型分组
    const PRODUCT_ICONS = {
      'QData': '📦', 'QFusion': '🔥', 'QPlus': '➕', 'QOne': '1️⃣',
      'QCP': '🔧', 'QCS': '☁️', 'ODM': '🏭', 'QMonitor': '📊',
      'PolarDB': '🐬', 'ZStack': '📐', '其他': '🧪'
    }
    const tenWorkdaysAgo = () => {
      const d = new Date()
      let wd = 0
      while (wd < 10) {
        d.setDate(d.getDate() - 1)
        const day = d.getDay()
        if (day !== 0 && day !== 6) wd++
      }
      return d
    }

    const overdueByProduct = computed(() => {
      const cutoff = tenWorkdaysAgo()
      const pocGroups = allGroups.value.filter(g =>
        /POC|poc|测试/.test(g.group_name)
      )
      
      // 获取每个POC群的最后消息时间
      const overdue = pocGroups.filter(g => {
        const msgs = allMessages.value.filter(m => m.room_id === g.room_id)
        if (msgs.length === 0) return false
        // 按msg_time排序取最新
        msgs.sort((a,b) => (b.msg_time || 0) - (a.msg_time || 0))
        const lastTime = new Date(msgs[0].msg_time)
        return lastTime >= cutoff
      }).map(g => {
        const msgs = allMessages.value.filter(m => m.room_id === g.room_id)
        msgs.sort((a,b) => (b.msg_time || 0) - (a.msg_time || 0))
        const lastTs = msgs[0]?.msg_time || 0
        const lastDate = new Date(lastTs)
        const lastStr = `${lastDate.getMonth()+1}/${lastDate.getDate()}`
        
        // 识别产品类型
        const prods = PRODUCT_NAMES.filter(p => g.group_name && g.group_name.includes(p))
        return {
          ...g,
          message_count: g.total_messages || 0,
          product: prods.length > 0 ? prods[0] : '其他',
          last_active: lastStr,
          last_ts: lastTs,
        }
      }).sort((a,b) => b.message_count - a.message_count)

      // 按产品分组
      const grouped = {}
      overdue.forEach(g => {
        if (!grouped[g.product]) grouped[g.product] = []
        grouped[g.product].push(g)
      })
      
      return Object.entries(grouped)
        .map(([name, groups]) => ({
          name,
          icon: PRODUCT_ICONS[name] || '🧪',
          groups: groups.map((g,i) => ({...g, rank: i+1})),
          total: groups.reduce((s,g) => s + g.message_count, 0),
        }))
        .sort((a,b) => b.total - a.total)
    })

    const filteredOverdue = (prod) => {
      let list = prod.groups || []
      if (!overdueSearch.value) return list.slice(0, displayLimit)
      const q = overdueSearch.value.toLowerCase()
      return list.filter(g => g.group_name.toLowerCase().includes(q)).slice(0, displayLimit)
    }

    // VIP客户群：群名包含VIP/屈臣氏/中信证券等关键词，按产品分组
    const VIP_KEYWORDS = ['VIP', 'vip', '屈臣氏', '中信证券', '招商证券', '财通证券', '华夏银行', '上海证券', '集美大学']

    const vipByProduct = computed(() => {
      const filtered = allGroups.value.filter(g =>
        VIP_KEYWORDS.some(kw => g.group_name && g.group_name.includes(kw))
      )
      return buildProductGroups(filtered)
    })

    const filteredVip = (prod) => {
      let list = prod.groups || []
      if (!vipSearch.value) return list.slice(0, displayLimit)
      const q = vipSearch.value.toLowerCase()
      return list.filter(g => g.group_name.toLowerCase().includes(q)).slice(0, displayLimit)
    }

    // 通用的按产品分组函数
    const buildProductGroups = (groups) => {
      const grouped = {}
      groups.forEach(g => {
        const prods = PRODUCT_NAMES.filter(p => g.group_name && g.group_name.includes(p))
        const key = prods.length > 0 ? prods[0] : '其他'
        if (!grouped[key]) grouped[key] = []
        grouped[key].push({...g, message_count: g.total_messages || 0, last_active: ''})
      })
      // 获取最后活跃时间
      Object.values(grouped).flat().forEach(g => {
        const msgs = allMessages.value.filter(m => m.room_id === g.room_id)
        if (msgs.length > 0) {
          msgs.sort((a,b) => (b.msg_time||0) - (a.msg_time||0))
          const d = new Date(msgs[0].msg_time)
          g.last_active = `${d.getMonth()+1}/${d.getDate()}`
        }
      })
      return Object.entries(grouped)
        .map(([name, gs]) => ({
          name,
          icon: PRODUCT_ICONS[name] || '⭐',
          groups: gs.sort((a,b) => b.message_count - a.message_count).map((g,i) => ({...g, rank: i+1})),
          total: gs.reduce((s,g) => s + g.message_count, 0),
        }))
        .sort((a,b) => b.total - a.total)
    }

    const fetchData = async () => {
      const date = selectedDate.value
      try {
        // 当日活跃数据（从operations-dashboard取today_active）
        const res = await axios.get(`/api/operations-dashboard?period=day`)
        const c = res.data.continuity
        internalToday.value = (c.internal.today_active || []).sort((a,b) => b.message_count - a.message_count)
        externalToday.value = (c.external.today_active || []).sort((a,b) => b.message_count - a.message_count)
      } catch (e) {
        console.error('获取当日活跃数据失败:', e)
      }

      try {
        // 总消息排行
        const res2 = await axios.get(`/api/groups-with-stats`)
        const groups = res2.data.groups || []
        allGroups.value = groups
        internalTotal.value = groups.filter(g => g.group_type === 'internal')
          .sort((a,b) => (b.total_messages || 0) - (a.total_messages || 0))
        externalTotal.value = groups.filter(g => g.group_type === 'external')
          .sort((a,b) => (b.total_messages || 0) - (a.total_messages || 0))

        // 加载消息列表用于超期POC计算
        try {
          const res3 = await axios.get(`/api/messages?limit=5000&fields=room_id,msg_time`)
          allMessages.value = res3.data.items || []
        } catch(e) {}

        // 产品线群分组
        const prodMap = {}
        PRODUCT_NAMES.forEach(name => { prodMap[name] = [] })
        groups.forEach(g => {
          PRODUCT_NAMES.forEach(name => {
            if (g.group_name && g.group_name.includes(name)) {
              prodMap[name].push({...g, message_count: g.total_messages})
            }
          })
        })
        productGroups.value = PRODUCT_NAMES
          .filter(name => prodMap[name].length > 0)
          .map(name => ({
            name,
            groups: prodMap[name].sort((a,b) => (b.total_messages||0)-(a.total_messages||0)).map((g,i)=>({...g, rank:i+1})),
            total: prodMap[name].reduce((s,g) => s + (g.total_messages||0), 0),
          }))
      } catch (e) {
        console.error('获取总排行数据失败:', e)
      }
    }

    const onSearch = () => {}

    const goToGroup = (row) => {
      if (row.room_id) {
        router.push(`/groups/${row.room_id}`)
      }
    }

    onMounted(() => {
      fetchData()
    })

    return {
      selectedDate, searchQuery, pocSearch, prodSearch, overdueSearch, activeTab,
      internalToday, externalToday, internalTotal, externalTotal,
      allGroups, allMessages, productGroups,
      filteredInternalToday, filteredExternalToday,
      filteredInternalTotal, filteredExternalTotal,
      filteredPocGroups, filteredProduct,
      pocByProduct, filteredPoc,
      overdueByProduct, filteredOverdue,
      vipByProduct, filteredVip,
      fetchData, onSearch, goToGroup,
    }
  }
}
</script>
