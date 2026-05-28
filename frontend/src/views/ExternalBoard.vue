<template>
  <div style="padding: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h2 style="margin: 0; font-size: 22px;">🌐 外部售后群看板</h2>
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="color:#999;font-size:14px;">共 {{ externalGroups.length }} 个外部群 · {{ totalMessages }} 条消息</span>
        <UpdateTime :refresh="60000" />
      </div>
    </div>

    <!-- 搜索 -->
    <el-input v-model="searchQuery" placeholder="搜索客户/群名..." size="small" clearable
      style="width: 300px; margin-bottom: 16px;" />

    <!-- 四列产品线布局 -->
    <el-row :gutter="16">
      <el-col v-for="prod in filteredProducts" :key="prod.name" :xs="24" :sm="12" :md="12" :lg="6" style="margin-bottom: 16px;">
        <el-card shadow="never" style="height: 100%;">
          <template #header>
            <div style="font-size: 14px;">
              <b>{{ prod.icon }} {{ prod.name }}</b>
              <span style="font-size:12px;color:#999;margin-left:8px;">{{ prod.groups.length }}群 · {{ prod.total }}条</span>
              <el-tag v-if="prod.faultCount > 0" size="small" type="danger" style="margin-left:6px;">
                ⚠ {{ prod.faultCount }}故障
              </el-tag>
            </div>
          </template>
          <div style="max-height: 500px; overflow-y: auto;">
            <div v-for="(g, i) in prod.groups" :key="g.room_id"
              :style="groupRowStyle(g)"
              @click="goToGroup(g)">
              <span style="width:24px;font-size:12px;color:#999;flex-shrink:0;">{{ i+1 }}</span>
              <div style="flex:1;min-width:0;">
                <div style="font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                  <template v-if="g.fault_level === 2">
                    <span style="color:#f56c6c;">🚨</span>
                  </template>
                  <template v-else-if="g.fault_level === 1">
                    <span style="color:#e6a23c;">⚠️</span>
                  </template>
                  <span :style="g.fault_level === 2 ? 'color:#f56c6c;font-weight:bold;' : 'color:#409eff;'">
                    {{ g.group_name }}
                  </span>
                </div>
                <div style="font-size:11px;margin-top:2px;">
                  <template v-if="g.fault_level === 2">
                    <span style="color:#f56c6c;">🔴 </span>
                    <span style="color:#f56c6c;font-weight:bold;">{{ g.fault_keywords?.join('、') || '严重故障' }}</span>
                  </template>
                  <template v-else-if="g.fault_level === 1">
                    <span style="color:#e6a23c;">🟡 </span>
                    <span style="color:#e6a23c;">{{ g.fault_keywords?.join('、') || '需关注' }}</span>
                  </template>
                  <span style="color:#999;">
                    {{ g.total_messages || 0 }}条
                    <template v-if="g.member_count"> · {{ g.member_count }}人</template>
                    <template v-if="g.last_active"> · {{ g.last_active }}</template>
                  </span>
                </div>
              </div>
              <el-tag :type="g.total_messages >= 20 ? 'danger' : g.total_messages >= 10 ? 'warning' : 'info'"
                size="small" style="flex-shrink:0;margin-left:6px;">
                {{ g.total_messages || 0 }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 无数据 -->
    <div v-if="filteredProducts.length === 0" style="color:#999;text-align:center;padding:40px;">
      暂无匹配的外部客户群
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import UpdateTime from '@/components/UpdateTime.vue'

export default {
  name: 'ExternalBoard',
  components: { UpdateTime },
  setup() {
    const router = useRouter()
    const searchQuery = ref('')
    const allGroups = ref([])
    const allMessages = ref([])

    const PRODUCT_CONFIG = {
      'QData': { icon: '📦', name: 'QData' },
      'QFusion': { icon: '🔥', name: 'QFusion' },
      'QPlus': { icon: '➕', name: 'QPlus' },
      'QOne': { icon: '1️⃣', name: 'QOne' },
      'QCP': { icon: '🔧', name: 'QCP' },
      'QCS': { icon: '☁️', name: 'QCS' },
      'ODM': { icon: '🏭', name: 'ODM' },
      'QMonitor': { icon: '📊', name: 'QMonitor' },
      'PolarDB': { icon: '🐬', name: 'PolarDB' },
      'ZStack': { icon: '📐', name: 'ZStack' },
    }
    const PRODUCT_NAMES = Object.keys(PRODUCT_CONFIG)

    const externalGroups = computed(() =>
      allGroups.value.filter(g => g.group_type === 'external')
    )

    const totalMessages = computed(() =>
      externalGroups.value.reduce((s, g) => s + (g.total_messages || 0), 0)
    )

    const groupRowStyle = (g) => {
      const base = 'display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f0f0f0;cursor:pointer;'
      if (g.fault_level === 2) return base + 'background:#fff2f0;border-left:3px solid #f56c6c;padding-left:6px;'
      if (g.fault_level === 1) return base + 'background:#fffbe6;border-left:3px solid #e6a23c;padding-left:6px;'
      return base
    }

    const productMap = computed(() => {
      const map = {}
      PRODUCT_NAMES.forEach(n => { map[n] = [] })
      map['其他'] = []

      externalGroups.value.forEach(g => {
        const name = g.group_name || ''
        let matched = false
        for (const p of PRODUCT_NAMES) {
          if (name.includes(p)) {
            map[p].push(g)
            matched = true
            break
          }
        }
        if (!matched) map['其他'].push(g)
      })
      return map
    })

    const enrichWithLastActive = (groups) => {
      return groups.map(g => {
        const msgs = allMessages.value.filter(m => m.room_id === g.room_id)
        let lastActive = ''
        if (msgs.length > 0) {
          msgs.sort((a,b) => (b.msg_time||0) - (a.msg_time||0))
          const d = new Date(msgs[0].msg_time)
          if (!isNaN(d.getTime())) {
            lastActive = `${d.getMonth()+1}/${d.getDate()}`
          }
        }
        return { ...g, last_active: lastActive }
      })
    }

    const buildProducts = () => {
      const result = []
      for (const [name, groups] of Object.entries(productMap.value)) {
        if (groups.length === 0) continue
        const enriched = enrichWithLastActive(groups)
        enriched.sort((a,b) => (b.total_messages || 0) - (a.total_messages || 0))
        const ranked = enriched.map((g,i) => ({...g, rank: i+1}))
        const cfg = PRODUCT_CONFIG[name] || { icon: '📋', name }
        result.push({
          ...cfg,
          groups: ranked,
          total: ranked.reduce((s,g) => s + (g.total_messages || 0), 0),
          faultCount: ranked.filter(g => g.fault_level === 2).length + ranked.filter(g => g.fault_level === 1).length * 0.5,
        })
      }
      result.sort((a,b) => b.total - a.total)
      return result
    }

    const products = ref([])

    const filteredProducts = computed(() => {
      if (!searchQuery.value) return products.value
      const q = searchQuery.value.toLowerCase()
      return products.value
        .map(prod => ({
          ...prod,
          groups: prod.groups.filter(g =>
            g.group_name && g.group_name.toLowerCase().includes(q)
          ),
        }))
        .filter(prod => prod.groups.length > 0)
    })

    const fetchData = async () => {
      try {
        const res = await axios.get('/api/groups-with-stats')
        allGroups.value = res.data.groups || []
        try {
          const res2 = await axios.get('/api/messages?limit=3000&fields=room_id,msg_time')
          allMessages.value = res2.data.items || []
        } catch(e) {}
        products.value = buildProducts()
      } catch(e) {
        console.error('获取外部群数据失败:', e)
      }
    }

    const goToGroup = (row) => {
      if (row.room_id) router.push(`/groups/${row.room_id}`)
    }

    onMounted(() => { fetchData() })

    return {
      searchQuery, externalGroups, totalMessages,
      products, filteredProducts, goToGroup, groupRowStyle,
    }
  }
}
</script>
