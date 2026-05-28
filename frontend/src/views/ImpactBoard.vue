<template>
  <div style="padding: 20px;">
    <!-- 页面标题 -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <div>
        <h2 style="margin:0;font-size:22px;">🚨 影响业务群看板</h2>
        <p style="color:#909399;margin:4px 0 0 0;font-size:13px;">
          近7天检测到故障关键词的外部群，汇总内外部消息给出结论
        </p>
      </div>
      <div style="display:flex;align-items:center;gap:12px;">
        <UpdateTime :refresh="120000" />
      </div>
    </div>

    <!-- 统计条 -->
    <div style="display:flex;gap:16px;margin-bottom:16px;">
      <el-tag type="danger">🔴 严重故障 {{ stats.critical }}个群</el-tag>
      <el-tag type="warning">🟡 需关注 {{ stats.high }}个群</el-tag>
      <el-tag>📊 共 {{ stats.total }}个影响业务群</el-tag>
    </div>

    <!-- 筛选 -->
    <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
      <el-select v-model="levelFilter" size="small" style="width: 140px;" @change="loadData">
        <el-option label="全部等级" value="" />
        <el-option label="🔴 严重" :value="2" />
        <el-option label="🟡 需关注" :value="1" />
      </el-select>
      <el-input v-model="searchQuery" placeholder="搜索群名..." size="small" clearable
        style="width: 200px;" />
    </div>

    <!-- 故障群列表 -->
    <div v-if="loading" style="text-align:center;padding:40px;color:#909399;">加载中...</div>
    <div v-else-if="items.length === 0" style="text-align:center;padding:60px;color:#909399;">
      🎉 暂无检测到影响业务的群
    </div>

    <div v-for="g in filteredItems" :key="g.room_id"
      style="margin-bottom:16px;border-radius:8px;border:1px solid #ebeef5;overflow:hidden;">

      <!-- 群标题栏 -->
      <div :style="`display:flex;align-items:center;padding:14px 16px;cursor:pointer;${
        g.level === 2 ? 'background:#fef0ef;' : 'background:#fdf6ec;'
      }`" @click="toggleExpand(g)">
        <div :style="`width:10px;height:10px;border-radius:50%;flex-shrink:0;margin-right:10px;background:${
          g.level === 2 ? '#f56c6c' : '#e6a23c'
        }`"></div>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:600;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
            {{ g.group_name }}
          </div>
          <div style="font-size:12px;color:#909399;margin-top:2px;">
            关键词: {{ g.keyword }} · 近7天{{ g.total_msgs_7d }}条消息 · 最后 {{ g.last_msg_time }}
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;margin-left:8px;">
          <el-tag :type="g.level === 2 ? 'danger' : 'warning'" size="small">
            {{ g.level === 2 ? '严重' : '关注' }}
          </el-tag>
          <el-tag size="small" effect="plain">
            {{ g.internal_msg_count }}内/{{ g.external_msg_count }}外
          </el-tag>
          <span style="color:#909399;font-size:12px;">{{ g.expanded ? '收起' : '展开' }}</span>
        </div>
      </div>

      <!-- 展开详情 -->
      <div v-if="g.expanded" style="padding:0 16px 16px;">
        <!-- 结论 -->
        <div :style="`margin:12px 0;padding:12px 16px;border-radius:6px;font-size:13px;line-height:1.6;${
          g.level === 2 ? 'background:#fef0ef;border-left:3px solid #f56c6c;' : 'background:#fdf6ec;border-left:3px solid #e6a23c;'
        }`">
          <strong>📋 结论</strong><br>
          {{ g.conclusion }}
        </div>

        <!-- 关键事件时间线 -->
        <div v-if="g.key_events && g.key_events.length > 0" style="margin-top:12px;">
          <div style="font-size:13px;font-weight:500;margin-bottom:8px;">🔑 关键事件</div>
          <div v-for="(ev, i) in g.key_events" :key="i"
            style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid #f5f5f5;">
            <div style="width:80px;flex-shrink:0;color:#909399;font-size:12px;">{{ ev.time }}</div>
            <div style="width:80px;flex-shrink:0;font-size:12px;">
              <el-tag :type="ev.is_external ? 'success' : ''" size="small" effect="plain">
                {{ ev.is_external ? '外部' : '内部' }}
              </el-tag>
              <span style="margin-left:4px;color:#666;">{{ ev.sender }}</span>
            </div>
            <div style="flex:1;font-size:12px;color:#333;line-height:1.5;">{{ ev.content }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import UpdateTime from '@/components/UpdateTime.vue'

export default {
  name: 'ImpactBoard',
  components: { UpdateTime },
  setup() {
    const items = ref([])
    const loading = ref(true)
    const levelFilter = ref('')
    const searchQuery = ref('')

    const stats = computed(() => {
      const total = items.value.length
      const critical = items.value.filter(i => i.level === 2).length
      const high = items.value.filter(i => i.level === 1).length
      return { total, critical, high }
    })

    const filteredItems = computed(() => {
      let list = items.value
      if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        list = list.filter(i => i.group_name.toLowerCase().includes(q))
      }
      return list
    })

    function toggleExpand(g) {
      g.expanded = !g.expanded
    }

    async function loadData() {
      loading.value = true
      try {
        const params = {}
        if (levelFilter.value) params.level = levelFilter.value
        const res = await axios.get('/api/impact-board', { params })
        items.value = (res.data.items || []).map(i => ({ ...i, expanded: false }))
      } catch (e) {
        console.error('获取影响业务群看板失败:', e)
        items.value = []
      }
      loading.value = false
    }

    onMounted(loadData)

    return {
      items, loading, stats, levelFilter, searchQuery,
      filteredItems, toggleExpand, loadData,
    }
  }
}
</script>
