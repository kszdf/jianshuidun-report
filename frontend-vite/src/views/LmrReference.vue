<template>
  <div class="lmr-page">
    <div class="page-header">
      <div>
        <div class="page-title">人材机占比参考库</div>
        <div class="page-subtitle">7类工程人材机行业参考值，快速对比你的项目是否合理</div>
      </div>
    </div>

    <!-- 工程类型选择 -->
    <div class="type-selector">
      <div
        v-for="item in projectTypes"
        :key="item.type"
        class="type-card"
        :class="{ active: selectedType === item.type }"
        @click="selectedType = item.type"
      >
        <div class="type-icon">{{ item.icon }}</div>
        <div class="type-name">{{ item.name }}</div>
      </div>
    </div>

    <div class="content-row">
      <!-- 左侧：行业参考值 -->
      <div class="panel reference-panel">
        <div class="panel-title">
          <span class="title-icon">📊</span>
          行业参考值
        </div>
        <div class="reference-chart">
          <div class="chart-bar" v-for="item in currentReference" :key="item.name">
            <div class="bar-label">{{ item.name }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: item.value + '%', background: item.color }">
                <span class="bar-value">{{ item.value }}%</span>
              </div>
            </div>
          </div>
        </div>
        <div class="reference-note">
          <p>💡 以上为行业经验参考值，具体项目因施工工艺、管理水平、地区差异会有所浮动</p>
          <p>⚠️ 人工费占比异常偏高或偏低都可能意味着成本结构有问题，建议重点核查</p>
        </div>
      </div>

      <!-- 右侧：项目对比 -->
      <div class="panel compare-panel">
        <div class="panel-title">
          <span class="title-icon">🔍</span>
          项目实际对比
        </div>

        <div class="project-selector">
          <el-select v-model="selectedProject" placeholder="选择项目" size="small" style="width: 100%">
            <el-option
              v-for="p in projectList"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </div>

        <div v-if="projectData" class="compare-table">
          <table>
            <thead>
              <tr>
                <th>类别</th>
                <th>实际占比</th>
                <th>参考值</th>
                <th>差异</th>
                <th>风险</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in compareData" :key="item.name">
                <td>{{ item.name }}</td>
                <td class="actual">{{ item.actual }}%</td>
                <td class="reference">{{ item.reference }}%</td>
                <td :class="item.diffClass">{{ item.diff > 0 ? '+' : '' }}{{ item.diff }}%</td>
                <td>
                  <el-tag :type="item.riskLevel" size="small">{{ item.riskText }}</el-tag>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="analysis-box" v-if="projectData">
          <div class="analysis-title">分析建议</div>
          <div class="analysis-content">
            <p v-for="(tip, idx) in analysisTips" :key="idx">• {{ tip }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 全部类型对照表 -->
    <div class="panel all-types-panel">
      <div class="panel-title">
        <span class="title-icon">📋</span>
        7类工程人材机占比对照表
      </div>
      <table class="all-types-table">
        <thead>
          <tr>
            <th>工程类型</th>
            <th>人工费占比</th>
            <th>材料费占比</th>
            <th>机械费占比</th>
            <th>特点说明</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in allTypesTable" :key="item.type" :class="{ highlight: selectedType === item.type }">
            <td class="type-name-cell">
              <span class="type-icon-small">{{ item.icon }}</span>
              {{ item.name }}
            </td>
            <td>{{ item.labor }}%</td>
            <td>{{ item.material }}%</td>
            <td>{{ item.machine }}%</td>
            <td class="desc-cell">{{ item.desc }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const projectTypes = [
  { type: 'building', name: '房建工程', icon: '🏢' },
  { type: 'municipal', name: '市政工程', icon: '🛣️' },
  { type: 'decoration', name: '装修工程', icon: '🎨' },
  { type: 'labor', name: '劳务工程', icon: '👷' },
  { type: 'installation', name: '安装工程', icon: '🔧' },
  { type: 'water', name: '水利工程', icon: '💧' },
  { type: 'garden', name: '园林工程', icon: '🌳' },
]

const referenceData = {
  building: [
    { name: '人工费', value: 30, color: '#409eff' },
    { name: '材料费', value: 60, color: '#67c23a' },
    { name: '机械费', value: 10, color: '#e6a23c' },
  ],
  municipal: [
    { name: '人工费', value: 20, color: '#409eff' },
    { name: '材料费', value: 55, color: '#67c23a' },
    { name: '机械费', value: 25, color: '#e6a23c' },
  ],
  decoration: [
    { name: '人工费', value: 40, color: '#409eff' },
    { name: '材料费', value: 55, color: '#67c23a' },
    { name: '机械费', value: 5, color: '#e6a23c' },
  ],
  labor: [
    { name: '人工费', value: 95, color: '#409eff' },
    { name: '材料费', value: 3, color: '#67c23a' },
    { name: '机械费', value: 2, color: '#e6a23c' },
  ],
  installation: [
    { name: '人工费', value: 50, color: '#409eff' },
    { name: '材料费', value: 40, color: '#67c23a' },
    { name: '机械费', value: 10, color: '#e6a23c' },
  ],
  water: [
    { name: '人工费', value: 10, color: '#409eff' },
    { name: '材料费', value: 40, color: '#67c23a' },
    { name: '机械费', value: 50, color: '#e6a23c' },
  ],
  garden: [
    { name: '人工费', value: 40, color: '#409eff' },
    { name: '材料费', value: 50, color: '#67c23a' },
    { name: '机械费', value: 10, color: '#e6a23c' },
  ],
}

const allTypesTable = [
  { type: 'building', name: '房建工程', icon: '🏢', labor: 30, material: 60, machine: 10, desc: '钢筋混凝土结构为主，材料占比最高' },
  { type: 'municipal', name: '市政工程', icon: '🛣️', labor: 20, material: 55, machine: 25, desc: '道路桥梁管网，大型机械设备使用多' },
  { type: 'decoration', name: '装修工程', icon: '🎨', labor: 40, material: 55, machine: 5, desc: '精装修工程人工占比高，以手工操作为主' },
  { type: 'labor', name: '劳务工程', icon: '👷', labor: 95, material: 3, machine: 2, desc: '纯劳务分包，几乎全部是人工成本' },
  { type: 'installation', name: '安装工程', icon: '🔧', labor: 50, material: 40, machine: 10, desc: '水电暖通安装，技术人工占比高' },
  { type: 'water', name: '水利工程', icon: '💧', labor: 10, material: 40, machine: 50, desc: '大型水利设施，重型机械使用费最高' },
  { type: 'garden', name: '园林工程', icon: '🌳', labor: 40, material: 50, machine: 10, desc: '绿化景观工程，苗木材料费+人工各半' },
]

const projectList = [
  { id: 1, name: '苏州工业园区科技园区办公楼项目' },
  { id: 2, name: '吴中区市政道路改造项目' },
  { id: 3, name: '高新区产业园精装修工程' },
]

const selectedType = ref('building')
const selectedProject = ref(1)

const currentReference = computed(() => referenceData[selectedType.value] || [])

const currentRefValues = computed(() => {
  const ref = referenceData[selectedType.value]
  if (!ref) return { labor: 30, material: 60, machine: 10 }
  return {
    labor: ref.find(i => i.name === '人工费')?.value || 30,
    material: ref.find(i => i.name === '材料费')?.value || 60,
    machine: ref.find(i => i.name === '机械费')?.value || 10,
  }
})

// 模拟项目实际数据
const projectActualData = {
  1: { type: 'building', labor: 32, material: 58, machine: 10 },
  2: { type: 'municipal', labor: 18, material: 57, machine: 25 },
  3: { type: 'decoration', labor: 45, material: 52, machine: 3 },
}

const projectData = computed(() => {
  return projectActualData[selectedProject.value] || null
})

const compareData = computed(() => {
  if (!projectData.value) return []
  const ref = currentRefValues.value
  const actual = projectData.value

  const items = [
    { name: '人工费', actual: actual.labor, reference: ref.labor },
    { name: '材料费', actual: actual.material, reference: ref.material },
    { name: '机械费', actual: actual.machine, reference: ref.machine },
  ]

  return items.map(item => {
    const diff = item.actual - item.reference
    const absDiff = Math.abs(diff)
    let riskLevel = 'success'
    let riskText = '正常'
    let diffClass = 'diff-normal'

    if (absDiff > 10) {
      riskLevel = 'danger'
      riskText = '异常'
      diffClass = 'diff-danger'
    } else if (absDiff > 5) {
      riskLevel = 'warning'
      riskText = '偏高'
      diffClass = 'diff-warning'
    }

    return {
      ...item,
      diff: diff.toFixed(1),
      riskLevel,
      riskText,
      diffClass,
    }
  })
})

const analysisTips = computed(() => {
  const tips = []
  if (!projectData.value) return tips

  const laborDiff = projectData.value.labor - currentRefValues.value.labor
  const materialDiff = projectData.value.material - currentRefValues.value.material
  const machineDiff = projectData.value.machine - currentRefValues.value.machine

  if (laborDiff > 5) {
    tips.push('人工费占比偏高，建议核查是否存在窝工现象或班组定额偏高')
  } else if (laborDiff < -5) {
    tips.push('人工费占比偏低，需确认是否存在工资未入账或劳务票缺失')
  }

  if (materialDiff > 5) {
    tips.push('材料费占比偏高，建议核查材料损耗率和采购价格')
  } else if (materialDiff < -5) {
    tips.push('材料费占比偏低，需关注材料发票是否足额取得')
  }

  if (Math.abs(machineDiff) > 5) {
    tips.push('机械费占比偏离较大，建议核实机械台班记录')
  }

  if (tips.length === 0) {
    tips.push('该项目人材机结构基本合理，与行业参考值相符')
  }

  return tips
})
</script>

<style scoped>
.lmr-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #0a1f44;
  margin-bottom: 8px;
}

.page-subtitle {
  color: #909399;
  font-size: 14px;
}

.type-selector {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.type-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px 12px;
  text-align: center;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.type-card:hover {
  border-color: #c9a24a;
  transform: translateY(-2px);
}

.type-card.active {
  border-color: #0a1f44;
  background: linear-gradient(135deg, #0a1f44, #1a3a6b);
  color: #fff;
}

.type-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.type-name {
  font-size: 14px;
  font-weight: 500;
}

.content-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.reference-panel {
  flex: 1;
}

.compare-panel {
  flex: 1.2;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #0a1f44;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 18px;
}

.reference-chart {
  margin-bottom: 20px;
}

.chart-bar {
  margin-bottom: 16px;
}

.bar-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 6px;
}

.bar-track {
  height: 32px;
  background: #f5f7fa;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.bar-fill {
  height: 100%;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 10px;
  transition: width 0.5s ease;
}

.bar-value {
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}

.reference-note {
  background: #fdf6ec;
  border-radius: 6px;
  padding: 12px 16px;
  font-size: 13px;
  color: #909399;
  line-height: 1.8;
}

.reference-note p {
  margin: 0;
}

.project-selector {
  margin-bottom: 20px;
}

.compare-table {
  margin-bottom: 20px;
}

.compare-table table {
  width: 100%;
  border-collapse: collapse;
}

.compare-table th,
.compare-table td {
  padding: 10px 12px;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.compare-table th {
  background: #fafafa;
  color: #909399;
  font-weight: 500;
}

.compare-table td.actual {
  color: #0a1f44;
  font-weight: 600;
}

.compare-table td.reference {
  color: #909399;
}

.diff-warning {
  color: #e6a23c;
  font-weight: 500;
}

.diff-danger {
  color: #f56c6c;
  font-weight: 600;
}

.diff-normal {
  color: #67c23a;
}

.analysis-box {
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f7df 100%);
  border-radius: 6px;
  padding: 16px;
}

.analysis-title {
  font-size: 14px;
  font-weight: 600;
  color: #67c23a;
  margin-bottom: 10px;
}

.analysis-content p {
  margin: 6px 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.all-types-panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.all-types-table {
  width: 100%;
  border-collapse: collapse;
}

.all-types-table th,
.all-types-table td {
  padding: 14px 16px;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.all-types-table th {
  background: #fafafa;
  color: #909399;
  font-weight: 500;
}

.all-types-table tr.highlight {
  background: #fdf6ec;
}

.type-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  font-weight: 500;
  color: #0a1f44;
}

.type-icon-small {
  font-size: 18px;
}

.desc-cell {
  text-align: left !important;
  color: #606266;
  font-size: 13px;
}
</style>
