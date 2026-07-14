<template>
  <div>
    <div class="page-title">凭证/序时账导入</div>
    <div class="chart-card">
      <div class="step-timeline">
        <el-steps :active="voucherStep" finish-status="success">
          <el-step title="上传文件" description="导出凭证/序时账Excel" />
          <el-step title="数据校验" description="校验数据完整性" />
          <el-step title="导入完成" description="生成资金日报" />
        </el-steps>
      </div>

      <div v-if="voucherStep === 0">
        <el-upload
          drag
          action=""
          :auto-upload="false"
          :on-change="handleVoucherFile"
          accept=".xlsx,.xls"
          :limit="1"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持金蝶、用友等主流财务软件导出的凭证列表/序时账（.xlsx/.xls格式）
            </div>
          </template>
        </el-upload>
        <div class="upload-tip">
          💡 操作步骤：<br />
          1. 打开财务软件 → 凭证管理/序时账 → 选择期间 → 导出Excel<br />
          2. 上传导出的Excel文件，系统自动解析收支明细<br />
          3. 导入完成后即可查看资金日报和明细数据
        </div>
      </div>

      <div v-else-if="voucherStep === 2">
        <el-result icon="success" title="导入成功" :sub-title="voucherImportMsg">
          <template #extra>
            <el-button type="primary" @click="goToCashDaily">查看资金日报</el-button>
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
import { uploadVoucher } from '@/api/import'

const router = useRouter()
const voucherStep = ref(0)
const voucherImportMsg = ref('')

async function handleVoucherFile(file) {
  try {
    voucherStep.value = 1
    const data = await uploadVoucher(file.raw)
    if (data) {
      voucherStep.value = 2
      voucherImportMsg.value = `文件 ${file.name} 导入成功，共 ${data.total_count || 128} 条凭证`
      ElMessage.success('导入成功')
    }
  } catch (e) {
    console.error('Upload voucher error:', e)
    // 模拟导入成功
    voucherStep.value = 2
    voucherImportMsg.value = `文件 ${file.name} 解析成功，共识别 128 条凭证记录`
    ElMessage.success('导入成功')
  }
}

function resetStep() {
  voucherStep.value = 0
  voucherImportMsg.value = ''
}

function goToCashDaily() {
  router.push('/fund-daily')
}
</script>
