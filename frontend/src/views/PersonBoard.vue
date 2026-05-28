<template>
  <div style="padding: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h2 style="margin: 0; font-size: 22px;">👤 人员看板</h2>
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="color:#999;font-size:14px;">共 {{ stats?.top_int_msgs?.length ? (stats.top_int_msgs.length + stats.top_ext_msgs.length) : '-' }} 类 · 查看最近 {{ viewDays }} 天</span>
        <UpdateTime :refresh="60000" />
      </div>
    </div>

    <!-- 统计面板：内部群 vs 外部群 -->
    <el-row :gutter="16" style="margin-bottom: 16px;">
      <!-- 内部群列 -->
      <el-col :span="6" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #409eff;border-radius:8px;height:100%;">
          <template #header>
            <span style="font-size:13px;font-weight:600;color:#409eff;">🏢 内部群 · 消息最多 TOP5</span>
          </template>
          <div style="max-height:200px;overflow-y:auto;">
            <div v-for="(p, i) in (stats?.top_int_msgs || []).slice(0,5)" :key="'im'+i"
              style="display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f5f5f5;">
              <div style="width:20px;font-size:11px;color:#909399;flex-shrink:0;">{{ i+1 }}</div>
              <div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;">{{ p.name }}</div>
              <div style="font-size:12px;font-weight:600;color:#409eff;">{{ p.msg_count }}</div>
              <div style="font-size:10px;color:#909399;margin-left:2px;">条</div>
            </div>
            <div v-if="!stats?.top_int_msgs?.length" style="color:#ccc;text-align:center;padding:12px;font-size:12px;">暂无</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #409eff;border-radius:8px;height:100%;">
          <template #header>
            <span style="font-size:13px;font-weight:600;color:#409eff;">🏘️ 内部群 · 按群数 TOP5</span>
          </template>
          <div style="max-height:200px;overflow-y:auto;">
            <div v-for="(p, i) in (stats?.top_int_groups || []).slice(0,5)" :key="'ig'+i"
              style="display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f5f5f5;">
              <div style="width:20px;font-size:11px;color:#909399;flex-shrink:0;">{{ i+1 }}</div>
              <div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;">{{ p.name }}</div>
              <div style="font-size:12px;font-weight:600;color:#409eff;">{{ p.group_count }}</div>
              <div style="font-size:10px;color:#909399;margin-left:2px;">个群</div>
            </div>
            <div v-if="!stats?.top_int_groups?.length" style="color:#ccc;text-align:center;padding:12px;font-size:12px;">暂无</div>
          </div>
        </el-card>
      </el-col>

      <!-- 外部群列 -->
      <el-col :span="6" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #67c23a;border-radius:8px;height:100%;">
          <template #header>
            <span style="font-size:13px;font-weight:600;color:#67c23a;">🌐 外部群 · 消息最多 TOP5</span>
          </template>
          <div style="max-height:200px;overflow-y:auto;">
            <div v-for="(p, i) in (stats?.top_ext_msgs || []).slice(0,5)" :key="'em'+i"
              style="display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f5f5f5;">
              <div style="width:20px;font-size:11px;color:#909399;flex-shrink:0;">{{ i+1 }}</div>
              <div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;">{{ p.name }}</div>
              <div style="font-size:12px;font-weight:600;color:#67c23a;">{{ p.msg_count }}</div>
              <div style="font-size:10px;color:#909399;margin-left:2px;">条</div>
            </div>
            <div v-if="!stats?.top_ext_msgs?.length" style="color:#ccc;text-align:center;padding:12px;font-size:12px;">暂无</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6" style="margin-bottom:12px;">
        <el-card shadow="never" style="border:1px solid #67c23a;border-radius:8px;height:100%;">
          <template #header>
            <span style="font-size:13px;font-weight:600;color:#67c23a;">🏘️ 外部群 · 按群数 TOP5</span>
          </template>
          <div style="max-height:200px;overflow-y:auto;">
            <div v-for="(p, i) in (stats?.top_ext_groups || []).slice(0,5)" :key="'eg'+i"
              style="display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f5f5f5;">
              <div style="width:20px;font-size:11px;color:#909399;flex-shrink:0;">{{ i+1 }}</div>
              <div style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;">{{ p.name }}</div>
              <div style="font-size:12px;font-weight:600;color:#67c23a;">{{ p.group_count }}</div>
              <div style="font-size:10px;color:#909399;margin-left:2px;">个群</div>
            </div>
            <div v-if="!stats?.top_ext_groups?.length" style="color:#ccc;text-align:center;padding:12px;font-size:12px;">暂无</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索和筛选 -->
    <div class="filter-bar">
      <el-input v-model="searchQuery" placeholder="搜索人员姓名..." size="small" clearable
        style="width: 160px;" @input="onSearch" />
      <el-select v-model="activeDept" size="small" style="width: 160px;" @change="loadData">
        <el-option label="全部人员" value="" />
        <el-option v-for="d in deptNames" :key="d" :label="d" :value="d" />
      </el-select>
      <el-select v-model="statusFilter" size="small" style="width: 150px;" @change="loadData">
        <el-option label="全部状态" value="" />
        <el-option label="🔴 连续≥3天无消息" value="silent3" />
        <el-option label="🟡 连续2天无消息" value="silent2" />
        <el-option label="🟢 有发言" value="active" />
        <el-option label="📅 连续N天无消息" value="custom" />
      </el-select>
      <el-input-number v-if="statusFilter === 'custom'" v-model="customSilentDays"
        :min="1" :max="30" size="small" style="width: 80px;"
        @change="loadData" />
      <el-select v-model="viewDays" size="small" style="width: 120px;" @change="loadData">
        <el-option label="近3天" :value="3" />
        <el-option label="近7天" :value="7" />
        <el-option label="近14天" :value="14" />
        <el-option label="近30天" :value="30" />
      </el-select>
      <el-select v-model="selectedDepts" size="small" style="width: 220px;" clearable multiple collapse-tags
        placeholder="按子部门筛选（可多选）" @change="onDeptChange">
        <el-option v-for="d in allDepts" :key="d" :label="d" :value="d" />
      </el-select>
      <el-checkbox v-model="realNameOnly" @change="loadData" size="small">
        仅显示真实姓名
      </el-checkbox>
    </div>

    <!-- 统计条 -->
    <div class="stats-bar">
      <el-tag type="danger">🔴 连续≥3天无消息: {{ silent3Count }}人</el-tag>
      <el-tag type="warning">🟡 连续2天: {{ silent2Count }}人</el-tag>
      <el-tag type="success">🟢 有发言: {{ activeCount }}人</el-tag>
    </div>

    <!-- 按部门分组显示 -->
    <div v-for="(group, di) in filteredDeptGroups" :key="di" style="margin-bottom: 20px;">
      <div class="dept-header">
        {{ group.dept_name }}
        <span style="font-size:12px;color:#999;font-weight:normal;margin-left:8px;">
          {{ group.persons.length }}人 · {{ group.silent3 }}人无消息
        </span>
      </div>
      
      <!-- 人员卡片网格 -->
      <div class="person-grid">
        <div v-for="p in group.persons" :key="p.user_id"
          class="person-card"
          :class="{
            'card-silent3': p.consecutive_silent_days >= 3,
            'card-silent2': p.consecutive_silent_days >= 2 && p.consecutive_silent_days < 3,
          }"
          @click="togglePersonDetail(p)">
          
          <!-- 姓名行 -->
          <div class="person-name-row">
            <span class="status-dot" :style="{
              background: p.consecutive_silent_days >= 3 ? '#f56c6c' : p.consecutive_silent_days >= 2 ? '#e6a23c' : '#67c23a',
            }"></span>
            <span class="person-name">{{ p.name }}</span>
            <span v-if="p.consecutive_silent_days >= 3" class="badge-danger">
              🔇{{ p.consecutive_silent_days }}天
            </span>
            <span v-else-if="p.consecutive_silent_days >= 2" class="badge-warning">
              ⚠️{{ p.consecutive_silent_days }}天
            </span>
          </div>

          <!-- 日期小方块 -->
          <div class="day-blocks">
            <div v-for="d in p.day_status" :key="d.date"
              :title="d.date + ': ' + d.count + '条'"
              class="day-block"
              :class="{ 'day-active': d.active, 'day-zero': !d.active && d.count === 0 }"
              :style="d.active ? 'background:#409eff;color:#fff;' : 'background:#f0f0f0;color:#ccc;'">
              {{ d.count > 0 ? d.count : '' }}
            </div>
          </div>
          
          <!-- 消息摘要 -->
          <div class="msg-summary">
            共{{ p.total_messages }}条
          </div>
          
          <!-- 点击展开详情 -->
          <div v-if="expandedPerson === p.user_id" class="expanded-detail">
            最近消息摘录：
            <div v-for="(msg, mi) in p.recent_msgs" :key="mi" style="padding:2px 0;border-bottom:1px solid #f5f5f5;">
              <span style="color:#999;font-size:10px;">{{ msg.time.slice(5,16) }}</span>
              <span v-if="msg.group_name" style="color:#409eff;font-size:10px;margin:0 4px;">{{ msg.group_name.slice(0,12) }}:</span>
              {{ msg.content.slice(0, 40) }}{{ msg.content.length > 40 ? '...' : '' }}
            </div>
            <div v-if="(!p.recent_msgs || p.recent_msgs.length === 0)" style="color:#ccc;text-align:center;padding:8px;">
              暂无消息记录
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 无数据 -->
    <div v-if="filteredDeptGroups.length === 0" style="color:#999;text-align:center;padding:40px;">
      没有匹配的人员
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import UpdateTime from '@/components/UpdateTime.vue'

export default {
  name: 'PersonBoard',
  components: { UpdateTime },
  setup() {
    const searchQuery = ref('')
    const activeDept = ref('')
    const statusFilter = ref('')
    const viewDays = ref(7)
    const customSilentDays = ref(3)
    const realNameOnly = ref(true)
    const activeDepartments = ref(['售后,交付,驻场,生态支撑', 'Oracle技术部,MySQL技术部,OceanBase技术部,PolarDB技术部,SQLServer技术部'])
    const allPersons = ref([])
    const expandedPerson = ref(null)
    const deptNames = ref([])
    const stats = ref(null)
    const selectedDepts = ref([])
    const allDepts = ref([])

    const silent3Count = computed(() => allPersons.value.filter(p => p.consecutive_silent_days >= 3).length)
    const silent2Count = computed(() => allPersons.value.filter(p => p.consecutive_silent_days >= 2 && p.consecutive_silent_days < 3).length)
    const activeCount = computed(() => allPersons.value.filter(p => p.consecutive_silent_days === 0).length)

    const filteredDeptGroups = computed(() => {
      let filtered = allPersons.value
      if (statusFilter.value === 'silent3') filtered = filtered.filter(p => p.consecutive_silent_days >= 3)
      else if (statusFilter.value === 'silent2') filtered = filtered.filter(p => p.consecutive_silent_days >= 2)
      else if (statusFilter.value === 'active') filtered = filtered.filter(p => p.consecutive_silent_days === 0)
      else if (statusFilter.value === 'custom') filtered = filtered.filter(p => p.consecutive_silent_days >= customSilentDays.value)
      if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        filtered = filtered.filter(p => p.name.toLowerCase().includes(q))
      }

      const map = {}
      filtered.forEach(p => {
        const d = p.department || '其他'
        if (!map[d]) map[d] = { dept_name: d, persons: [], silent3: 0 }
        map[d].persons.push(p)
        if (p.consecutive_silent_days >= 3) map[d].silent3++
      })
      
      return Object.values(map).sort((a,b) => b.persons.length - a.persons.length)
    })

    const loadData = async () => {
      try {
        // 加载部门列表（首次）
        if (allDepts.value.length === 0) {
          const deptRes = await axios.get('/api/persons/dept-list')
          allDepts.value = deptRes.data.items || []
        }
        // 加载统计
        const statsRes = await axios.get('/api/persons/stats')
        stats.value = statsRes.data

        // 加载人员明细
        const params = { days: viewDays.value, limit: 500 }
        if (activeDept.value) params.department = activeDept.value
        if (statusFilter.value === 'custom') params.silent_days = customSilentDays.value
        if (realNameOnly.value) params.real_name_only = true
        if (selectedDepts.value && selectedDepts.value.length > 0) {
          params.departments = selectedDepts.value.join(',')
        }
        
        const res = await axios.get('/api/persons', { params })
        allPersons.value = res.data.items || []
        
        const depts = new Set()
        for (const p of allPersons.value) {
          if (p.department) {
            p.department.split(/\s+/).forEach(d => depts.add(d))
          }
        }
        deptNames.value = Array.from(depts).sort()
      } catch (e) {
        console.error('获取人员看板失败:', e)
      }
    }

    const togglePersonDetail = async (p) => {
      if (expandedPerson.value === p.user_id) {
        expandedPerson.value = null
        return
      }
      expandedPerson.value = p.user_id
      try {
        const res = await axios.get('/api/messages', {
          params: { sender_id: p.user_id, limit: 5 }
        })
        p.recent_msgs = (res.data.items || []).map(m => ({
          time: m.msg_time || '',
          content: m.content_text || '',
          group_name: m.group_name || '',
        }))
      } catch(e) {
        p.recent_msgs = []
      }
    }

    const onSearch = () => {}
    const onDeptChange = () => { loadData() }

    onMounted(loadData)

    return {
      searchQuery, activeDept, statusFilter, viewDays, customSilentDays, realNameOnly, activeDepartments,
      allPersons, expandedPerson, deptNames, stats,
      selectedDepts, allDepts, onDeptChange,
      silent3Count, silent2Count, activeCount,
      filteredDeptGroups,
      loadData, togglePersonDetail, onSearch,
    }
  }
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.stats-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}
.dept-header {
  font-size: 15px;
  font-weight: bold;
  margin-bottom: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
}
.person-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 10px;
}
.person-card {
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e8e8e8;
  background: #fff;
}
.person-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.card-silent3 {
  background: #fff2f0;
  border-color: #ffccc7;
}
.card-silent2 {
  background: #fffbe6;
  border-color: #ffe58f;
}
.person-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}
.person-name {
  font-weight: bold;
  font-size: 14px;
}
.badge-danger {
  color: #f56c6c;
  font-size: 11px;
  font-weight: bold;
}
.badge-warning {
  color: #e6a23c;
  font-size: 11px;
}
.day-blocks {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
}
.day-block {
  width: 20px;
  height: 20px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 8px;
}
.day-active {
  opacity: 1;
}
.day-zero {
  opacity: 0.5;
}
.msg-summary {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}
.expanded-detail {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid #eee;
  font-size: 12px;
  color: #666;
}
</style>