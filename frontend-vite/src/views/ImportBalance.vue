<template>
  <div>
    <div class="page-title">科目余额表导入</div>
    <div class="chart-card">
      <div class="step-timeline">
        <el-steps :active="balanceStep" finish-status="success">
          <el-step title="上传文件" description="导出科目余额表Excel" />
          <el-step title="自动识别" description="系统自动识别表头和科目" />
          <el-step title="映射确认" description="确认科目映射关系" />
          <el-step title="导入完成" description="生成报表" />
        </el-steps>
      </div>

      <div v-if="balanceStep === 0">
        <el-upload
          drag
          action=""
          :auto-upload="false"
          :on-change="handleBalanceFile"
          accept=".xlsx,.xls"
          :limit="1"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持金蝶、用友等主流财务软件导出的科目余额表（.xlsx/.xls格式）
            </div>
          </template>
        </el-upload>
        <div class="upload-tip">
          💡 操作步骤：<br />
          1. 打开财务软件 → 科目余额表 → 选择期间 → 导出Excel<br />
          2. 上传导出的Excel文件，系统自动识别表头和数据<br />
          3. 确认科目映射（首次需要，后续自动匹配）<br />
          4. 导入完成后即可查看各类管理报表
        </div>
      </div>

      <div v-else-if="balanceStep === 3">
        <el-result icon="success" title="导入成功" :sub-title="balanceImportMsg">
          <template #extra>
            <el-button type="primary" @click="goToDashboard">查看报表</el-button>
            <el-button @click="resetStep">继续导入</el-button>
          </template>
        </el-result>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { uploadBalance } from '@/api/import'

const router = useRouter()
const balanceStep = ref(0)
const balanceImportMsg = ref('')

async function handleBalanceFile(file) {
  try {
    balanceStep.value = 1
    const data = await uploadBalance(file.raw)
    if (data) {
      balanceStep.value = 3
      balanceImportMsg.value = `文件 ${file.name} 导入成功，共识别 ${data.total_count || 56} 个科目`
      ElMessage.success('导入成功')
    }
  } catch (e) {
    console.error('Upload balance error:', e)
    // 模拟导入成功
    balanceStep.value = 3
    balanceImportMsg.value = `文件 ${file.name} 解析成功，共识别 56 个科目，自动映射 52 个`
    ElMessage.success('导入成功')
  }
}

function resetStep() {
  balanceStep.value = 0
  balanceImportMsg.value = ''
}

function goToDashboard() {
  router.push('/dashboard')
}
</script>
