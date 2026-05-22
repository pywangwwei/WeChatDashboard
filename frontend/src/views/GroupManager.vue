<template>
  <div style="padding: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <div>
        <h2 style="margin: 0 0 4px 0; font-size: 22px;">👥 群管理</h2>
        <p style="color: #999; font-size: 13px; margin: 0;">
          共 {{ groups.length }} 个群，未命名 {{ unnamedCount }} 个
        </p>
      </div>
      <div>
        <el-button type="primary" @click="inferNames" :loading="inferring" size="small">
          🔄 一键推断群名
        </el-button>
        <el-button @click="fetchGroups" size="small" style="margin-left: 8px;">
          🔄 刷新
        </el-button>
      </div>
    </div>

    <!-- 过滤条 -->
    <div style="margin-bottom: 12px; display: flex; gap: 8px; align-items: center;">
      <el-radio-group v-model="filterType" size="small">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="unnamed">未命名</el-radio-button>
        <el-radio-button value="internal">内部群</el-radio-button>
        <el-radio-button value="external">外部群</el-radio-button>
      </el-radio-group>
      <el-input v-model="searchText" placeholder="搜索群名..." clearable size="small" style="width: 200px;" />
    </div>

    <el-table :data="filteredGroups" size="small" stripe style="width: 100%" max-height="calc(100vh - 220px)">
      <el-table-column prop="group_name" label="群名" min-width="250">
        <template #default="{row}">
          <div style="display: flex; align-items: center; gap: 6px;">
            <span v-if="row.group_name && row.group_name !== '(未命名)'">{{ row.group_name }}</span>
            <span v-else style="color: #ccc; font-style: italic;">(未命名)</span>
            <el-button text size="small" @click="editGroup(row)" style="font-size: 12px; color: #409eff;">
              ✏️
            </el-button>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="类型" width="80">
        <template #default="{row}">
          <el-tag :type="row.group_type === 'internal' ? '' : 'success'" size="small">
            {{ row.group_type === 'internal' ? '内部' : '外部' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="total_messages" label="消息数" width="80" sortable />
      <el-table-column prop="member_count" label="成员数" width="80" sortable />
    </el-table>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" title="编辑群名" width="400px">
      <el-form>
        <el-form-item label="群名">
          <el-input v-model="editName" placeholder="输入群名" />
        </el-form-item>
        <p style="color: #999; font-size: 12px; margin: 0;">
          Room ID: {{ editingRoomId }}
        </p>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveName" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'GroupManager',
  setup() {
    const groups = ref([])
    const filterType = ref('')
    const searchText = ref('')
    const inferring = ref(false)
    const saving = ref(false)
    const dialogVisible = ref(false)
    const editName = ref('')
    const editingRoomId = ref('')

    const unnamedCount = computed(() =>
      groups.value.filter(g => !g.group_name || g.group_name === '(未命名)').length
    )

    const filteredGroups = computed(() => {
      let list = groups.value
      if (filterType.value === 'unnamed') {
        list = list.filter(g => !g.group_name || g.group_name === '(未命名)')
      } else if (filterType.value) {
        list = list.filter(g => g.group_type === filterType.value)
      }
      if (searchText.value) {
        const q = searchText.value.toLowerCase()
        list = list.filter(g => (g.group_name || '').toLowerCase().includes(q))
      }
      return list
    })

    const fetchGroups = async () => {
      try {
        const res = await axios.get('/api/groups-with-stats')
        groups.value = res.data.groups
      } catch (e) {
        console.error('获取群列表失败:', e)
      }
    }

    const inferNames = async () => {
      inferring.value = true
      try {
        const res = await axios.post('/api/infer-group-names')
        console.log('推断结果:', res.data)
        await fetchGroups()
      } catch (e) {
        console.error('推断失败:', e)
      } finally {
        inferring.value = false
      }
    }

    const editGroup = (row) => {
      editingRoomId.value = row.room_id
      editName.value = (row.group_name && row.group_name !== '(未命名)') ? row.group_name : ''
      dialogVisible.value = true
    }

    const saveName = async () => {
      saving.value = true
      try {
        await axios.post('/api/update-group-name', {
          room_id: editingRoomId.value,
          group_name: editName.value
        })
        dialogVisible.value = false
        await fetchGroups()
      } catch (e) {
        console.error('保存失败:', e)
      } finally {
        saving.value = false
      }
    }

    onMounted(fetchGroups)

    return {
      groups, filterType, searchText, inferring, saving,
      dialogVisible, editName, editingRoomId,
      unnamedCount, filteredGroups,
      fetchGroups, inferNames, editGroup, saveName
    }
  }
}
</script>
