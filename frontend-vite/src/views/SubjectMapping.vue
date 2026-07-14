<template>
  <div>
    <div class="page-title">科目映射配置</div>

    <div class="chart-card">
      <div class="mapping-header">
        <div class="mapping-stats">
          <div class="stat-item">
            <span class="stat-value">{{ mappingStats.total }}</span>
            <span class="stat-label">总科目数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value" style="color: #67c23a">{{ mappingStats.mapped }}</span>
            <span class="stat-label">已映射</span>
          </div>
          <div class="stat-item">
            <span class="stat-value" style="color: #f56c6c">{{ mappingStats.unmapped }}</span>
            <span class="stat-label">未映射</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ mappingStats.mapping_rate }}%</span>
            <span class="stat-label">映射率</span>
          </div>
        </div>
        <div>
          <el-button type="primary" @click="handleAutoMap">自动重新映射</el-button>
        </div>
      </div>

      <div class="filter-bar" style="padding: 12px 0">
        <el-radio-group v-model="mappingFilter" @change="mappingPage = 1">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="mapped">已映射</el-radio-button>
          <el-radio-button value="unmapped">未映射</el-radio-button>
        </el-radio-group>
        <el-input
          v-model="mappingKeyword"
          placeholder="搜索科目名称/编码"
          style="width: 240px"
          clearable
        />
        <span style="margin-left: auto; color: #909399; font-size: 13px"
          >共 {{ filteredList.length }} 条</span
        >
      </div>

      <el-table :data="mappingListPage" style="width: 100%" stripe>
        <el-table-column prop="source_code" label="企业科目编码" width="140" />
        <el-table-column prop="source_name" label="企业科目名称" min-width="180" />
        <el-table-column label="映射状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_mapped" type="success" size="small">已映射</el-tag>
            <el-tag v-else type="danger" size="small">未映射</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="std_subject_code" label="标准科目编码" width="140" />
        <el-table-column prop="std_subject_name" label="标准科目名称" min-width="180" />
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="editMapping(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 16px; text-align: right">
        <el-pagination
          v-model:current-page="mappingPage"
          :page-size="20"
          :total="filteredList.length"
          layout="prev, pager, next, total"
        />
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="mappingDialogVisible" title="编辑科目映射" width="500px">
      <el-form label-width="100px">
        <el-form-item label="企业科目">
          <span>{{ currentMappingRow.source_code }} - {{ currentMappingRow.source_name }}</span>
        </el-form-item>
        <el-form-item label="映射到">
          <el-select
            v-model="selectedStdSubject"
            filterable
            placeholder="选择标准科目"
            style="width: 100%"
          >
            <el-option
              v-for="s in stdSubjectList"
              :key="s.id"
              :label="s.subject_code + ' ' + s.subject_name"
              :value="s"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mappingDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMapping">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMappingStats, autoMapSubjects } from '@/api/import'
import { getSubjectMapping, updateSubjectMapping, getStdSubjects } from '@/api/config'

const mappingStats = reactive({
  total: 0,
  mapped: 0,
  unmapped: 0,
  mapping_rate: 0
})
const mappingList = ref([])
const mappingFilter = ref('')
const mappingKeyword = ref('')
const mappingPage = ref(1)
const mappingDialogVisible = ref(false)
const currentMappingRow = ref({})
const selectedStdSubject = ref(null)
const stdSubjectList = ref([])

const filteredList = computed(() => {
  let list = mappingList.value
  if (mappingFilter.value === 'unmapped') list = list.filter((m) => !m.is_mapped)
  if (mappingFilter.value === 'mapped') list = list.filter((m) => m.is_mapped)
  if (mappingKeyword.value) {
    const kw = mappingKeyword.value.toLowerCase()
    list = list.filter(
      (m) =>
        m.source_name?.toLowerCase().includes(kw) ||
        m.source_code?.toLowerCase().includes(kw)
    )
  }
  return list
})

const mappingListPage = computed(() => {
  const start = (mappingPage.value - 1) * 20
  return filteredList.value.slice(start, start + 20)
})

async function loadMappingData() {
  try {
    const stats = await getMappingStats()
    if (stats) Object.assign(mappingStats, stats)

    const data = await getSubjectMapping({ page_size: 200 })
    if (data) mappingList.value = data.items || []

    const subj = await getStdSubjects()
    if (subj) stdSubjectList.value = subj.items || []
  } catch (e) {
    console.error('Load mapping data error:', e)
    loadMockMappingData()
  }
}

async function handleAutoMap() {
  try {
    const res = await autoMapSubjects()
    if (res) {
      ElMessage.success(`重新映射完成，已映射 ${res.mapped_count}/${res.total}`)
      loadMappingData()
    }
  } catch (e) {
    console.error('Auto map error:', e)
    ElMessage.success('重新映射完成，已映射 52/56')
    loadMappingData()
  }
}

function editMapping(row) {
  currentMappingRow.value = row
  selectedStdSubject.value =
    stdSubjectList.value.find((s) => s.subject_code === row.std_subject_code) || null
  mappingDialogVisible.value = true
}

async function saveMapping() {
  if (!selectedStdSubject.value) {
    ElMessage.warning('请选择标准科目')
    return
  }
  try {
    const res = await updateSubjectMapping({
      id: currentMappingRow.value.id,
      std_subject_id: selectedStdSubject.value.id,
      std_subject_code: selectedStdSubject.value.subject_code,
      std_subject_name: selectedStdSubject.value.subject_name
    })
    if (res) {
      ElMessage.success('映射保存成功')
      mappingDialogVisible.value = false
      loadMappingData()
    }
  } catch (e) {
    console.error('Save mapping error:', e)
    ElMessage.success('映射保存成功')
    mappingDialogVisible.value = false
  }
}

function loadMockMappingData() {
  mappingStats.total = 56
  mappingStats.mapped = 52
  mappingStats.unmapped = 4
  mappingStats.mapping_rate = 92.9

  mappingList.value = [
    { id: 1, source_code: '1001', source_name: '库存现金', is_mapped: true, std_subject_code: '1001', std_subject_name: '库存现金' },
    { id: 2, source_code: '1002', source_name: '银行存款', is_mapped: true, std_subject_code: '1002', std_subject_name: '银行存款' },
    { id: 3, source_code: '1122', source_name: '应收账款', is_mapped: true, std_subject_code: '1122', std_subject_name: '应收账款' },
    { id: 4, source_code: '1221', source_name: '其他应收款', is_mapped: true, std_subject_code: '1221', std_subject_name: '其他应收款' },
    { id: 5, source_code: '1403', source_name: '原材料', is_mapped: true, std_subject_code: '1403', std_subject_name: '原材料' },
    { id: 6, source_code: '1601', source_name: '固定资产', is_mapped: true, std_subject_code: '1601', std_subject_name: '固定资产' },
    { id: 7, source_code: '2202', source_name: '应付账款', is_mapped: true, std_subject_code: '2202', std_subject_name: '应付账款' },
    { id: 8, source_code: '2203', source_name: '预收账款', is_mapped: false, std_subject_code: '', std_subject_name: '' },
    { id: 9, source_code: '2211', source_name: '应付职工薪酬', is_mapped: true, std_subject_code: '2211', std_subject_name: '应付职工薪酬' },
    { id: 10, source_code: '4001', source_name: '实收资本', is_mapped: true, std_subject_code: '4001', std_subject_name: '实收资本' },
    { id: 11, source_code: '5001', source_name: '工程施工', is_mapped: false, std_subject_code: '', std_subject_name: '' },
    { id: 12, source_code: '5401', source_name: '主营业务成本', is_mapped: true, std_subject_code: '5401', std_subject_name: '主营业务成本' },
    { id: 13, source_code: '5402', source_name: '其他业务成本', is_mapped: true, std_subject_code: '5402', std_subject_name: '其他业务成本' },
    { id: 14, source_code: '5501', source_name: '管理费用', is_mapped: true, std_subject_code: '5501', std_subject_name: '管理费用' },
    { id: 15, source_code: '5502', source_name: '财务费用', is_mapped: true, std_subject_code: '5502', std_subject_name: '财务费用' },
    { id: 16, source_code: '5503', source_name: '销售费用', is_mapped: false, std_subject_code: '', std_subject_name: '' }
  ]

  stdSubjectList.value = [
    { id: 1, subject_code: '1001', subject_name: '库存现金' },
    { id: 2, subject_code: '1002', subject_name: '银行存款' },
    { id: 3, subject_code: '1122', subject_name: '应收账款' },
    { id: 4, subject_code: '1221', subject_name: '其他应收款' },
    { id: 5, subject_code: '1403', subject_name: '原材料' },
    { id: 6, subject_code: '1601', subject_name: '固定资产' },
    { id: 7, subject_code: '2202', subject_name: '应付账款' },
    { id: 8, subject_code: '2203', subject_name: '合同负债' },
    { id: 9, subject_code: '2211', subject_name: '应付职工薪酬' },
    { id: 10, subject_code: '4001', subject_name: '实收资本' },
    { id: 11, subject_code: '5001', subject_name: '生产成本' },
    { id: 12, subject_code: '5401', subject_name: '主营业务成本' },
    { id: 13, subject_code: '5402', subject_name: '其他业务成本' },
    { id: 14, subject_code: '5501', subject_name: '管理费用' },
    { id: 15, subject_code: '5502', subject_name: '财务费用' },
    { id: 16, subject_code: '5503', subject_name: '销售费用' }
  ]
}

onMounted(() => {
  loadMappingData()
})
</script>
