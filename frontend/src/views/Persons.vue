<template>
  <div>
    <h1 style="margin:0 0 20px 0;font-size:24px;">👤 人员分析</h1>

    <el-card shadow="never" style="margin-bottom:16px;">
      <el-radio-group v-model="filterInternal" @change="loadPersons">
        <el-radio-button :value="undefined">全部 ({{ total }})</el-radio-button>
        <el-radio-button :value="true">🔵 内部员工</el-radio-button>
        <el-radio-button :value="false">🟢 外部客户</el-radio-button>
      </el-radio-group>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <div v-for="(p, i) in persons" :key="p.user_id"
           style="display:flex;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0;cursor:pointer;"
           @click="$router.push('/persons/'+p.user_id)">
        <div style="width:24px;font-weight:bold;color:#999;">{{ i+1 }}</div>
        <div style="width:36px;height:36px;border-radius:50%;background:#f0f2f5;display:flex;align-items:center;justify-content:center;font-size:16px;margin:0 12px;">
          {{ p.is_internal ? '🔵' : '🟢' }}
        </div>
        <div style="flex:1;">
          <div style="font-weight:bold;">{{ p.display_name }}</div>
          <div style="font-size:12px;color:#999;">{{ p.email || '企业微信用户' }}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-weight:bold;font-size:18px;color:#409eff;">{{ p.total_messages }}</div>
          <div style="font-size:12px;color:#999;">条消息</div>
        </div>
      </div>
      <div v-if="persons.length === 0 && !loading" style="text-align:center;color:#999;padding:40px;">
        暂无人员数据
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listPersons } from '@/api/index.js'

const persons = ref([])
const total = ref(0)
const filterInternal = ref(undefined)
const loading = ref(false)

async function loadPersons() {
  loading.value = true
  try {
    const params = {}
    if (filterInternal.value !== undefined) params.is_internal = filterInternal.value
    const res = await listPersons(params)
    persons.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    console.error(e)
  }
  loading.value = false
}

onMounted(loadPersons)
</script>
