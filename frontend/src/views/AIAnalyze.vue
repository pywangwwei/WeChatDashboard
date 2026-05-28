<template>
  <div style="padding: 20px;">
    <h2 style="margin: 0 0 16px; font-size: 22px;">🤖 AI 群消息分析</h2>

    <!-- 查询条件 -->
    <el-card shadow="never" style="margin-bottom: 20px;">
      <el-form :inline="true" size="small">
        <el-form-item label="选择群">
          <el-select v-model="selectedGroup" filterable placeholder="输入群名搜索" style="width: 300px;">
            <el-option v-for="g in groupOptions" :key="g.room_id" :label="g.group_name" :value="g.room_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <span style="color:#666;font-size:13px;">{{ startDate }}</span>
        </el-form-item>
        <el-form-item label="结束日期">
          <span style="color:#666;font-size:13px;">{{ endDate }}</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="analyze" :loading="loading" :disabled="!selectedGroup">
            🔍 AI分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 快捷选择 -->
    <el-card shadow="never" style="margin-bottom: 20px;">
      <template #header><b>⚡ 快速分析</b></template>
      <el-tag v-for="g in quickGroups" :key="g.room_id"
        style="margin: 4px; cursor:pointer;" @click="quickAnalyze(g)">
        {{ g.group_name }}
      </el-tag>
    </el-card>

    <!-- 分析结果 -->
    <div v-if="result">
      <el-card shadow="never">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b>📊 分析报告: {{ result.group_name }}</b>
            <span style="font-size:12px;color:#999;">
              {{ result.message_count }}条消息 / {{ result.start_date }} ~ {{ result.end_date }}
            </span>
          </div>
        </template>
        <div v-if="result.error" style="color:#e6a23c; padding:20px; text-align:center;">
          {{ result.error }}
        </div>
        <div v-else class="analysis-content" v-html="renderedAnalysis"></div>
      </el-card>
    </div>

    <!-- 历史分析记录 -->
    <el-card v-if="history.length > 0" shadow="never" style="margin-top: 20px;">
      <template #header><b>📜 分析记录</b></template>
      <el-timeline>
        <el-timeline-item v-for="(h, i) in history" :key="i" :timestamp="h.time" placement="top">
          <b>{{ h.group_name }}</b>
          <span style="color:#999;margin-left:8px;">{{ h.msg_count }}条消息</span>
          <p style="font-size:13px;color:#666;margin:4px 0 0;white-space:pre-wrap;">{{ h.summary }}</p>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { marked } from 'marked'

export default {
  name: 'AIAnalyze',
  setup() {
    const selectedGroup = ref('')
    const todayStr = new Date().toISOString().slice(0, 10)
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
    const startDate = ref(weekAgo)
    const endDate = ref(todayStr)
    const loading = ref(false)
    const result = ref(null)
    const history = ref([])
    const allGroups = ref([])

    const groupOptions = computed(() => {
      return allGroups.value
        .filter(g => g.group_name && !g.group_name.startsWith('推断:') && !g.group_name.includes('沃趣售后技术支持'))
        .sort((a,b) => (b.total_messages||0) - (a.total_messages||0))
    })

    const quickGroups = computed(() => {
      return groupOptions.value
        .filter(g => (g.total_messages || 0) > 15)
        .slice(0, 20)
    })

    const formatDate = (d) => {
      if (!d) return ''
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${y}-${m}-${day}`
    }

    const renderedAnalysis = computed(() => {
      if (!result.value?.analysis) return ''
      return marked.parse(result.value.analysis)
    })

    const analyze = async () => {
      if (!selectedGroup.value) return
      loading.value = true
      result.value = null

      const group = allGroups.value.find(g => g.room_id === selectedGroup.value)

      try {
        const res = await axios.post('/api/ai-analyze-group', null, {
          params: {
            group_name: group?.group_name || selectedGroup.value,
            start_date: startDate.value,
            end_date: endDate.value,
          },
          timeout: 120000,
        })
        result.value = res.data

        // 保存到历史
        const summary = res.data.analysis?.split('\n').slice(0, 3).join(' ').substring(0, 100) || ''
        history.value.unshift({
          group_name: res.data.group_name,
          time: new Date().toLocaleString(),
          msg_count: res.data.message_count,
          summary,
        })
      } catch (e) {
        result.value = {
          group_name: group?.group_name || selectedGroup.value,
          error: `分析失败: ${e.message}`,
          analysis: '',
        }
      }
      loading.value = false
    }

    const quickAnalyze = (g) => {
      selectedGroup.value = g.room_id
      analyze()
    }

    onMounted(async () => {
      try {
        const res = await axios.get('/api/groups-with-stats')
        allGroups.value = res.data.groups || []
      } catch (e) {
        console.error('加载群列表失败:', e)
      }
    })

    return {
      selectedGroup, startDate, endDate, loading, result, history,
      allGroups, groupOptions, quickGroups, renderedAnalysis,
      analyze, quickAnalyze,
    }
  }
}
</script>

<style>
.analysis-content {
  font-size: 14px;
  line-height: 1.7;
  padding: 8px;
}
.analysis-content h3 {
  margin: 16px 0 8px;
  color: #409eff;
  border-bottom: 1px solid #eee;
  padding-bottom: 4px;
}
.analysis-content h4 { margin: 12px 0 6px; color: #333; }
.analysis-content ul { padding-left: 20px; }
.analysis-content li { margin: 4px 0; }
.analysis-content strong { color: #f56c6c; }
.analysis-content hr { border: none; border-top: 1px solid #eee; margin: 16px 0; }
</style>
