<template>
  <div class="tax-calc-page">
    <div class="page-title">挂靠税费精算计算器</div>
    <div class="page-subtitle">建筑行业挂靠业务税费一键精算，支持先扣后返模式</div>

    <!-- 预设场景 -->
    <div class="preset-scenes">
      <el-button
        v-for="scene in presetScenes"
        :key="scene.name"
        size="small"
        :type="activeScene === scene.name ? 'primary' : 'default'"
        @click="applyScene(scene)"
      >
        {{ scene.name }}
      </el-button>
    </div>

    <div class="calc-container">
      <!-- 左侧：输入区 -->
      <div class="input-section">
        <div class="section-title">
          <el-icon><Calculator /></el-icon>
          <span>输入参数</span>
        </div>

        <!-- 模式切换 -->
        <el-tabs v-model="calcMode" class="mode-tabs">
          <el-tab-pane label="标准模式" name="standard" />
          <el-tab-pane label="先扣后返" name="pre_deduct" />
        </el-tabs>

        <el-form label-width="120px" size="default">
          <el-form-item label="合同金额(含税)">
            <el-input-number
              v-model="form.contract_amount"
              :min="0"
              :step="10000"
              :controls="false"
              style="width: 100%"
              @change="calcResult"
            />
            <span class="unit">元</span>
          </el-form-item>

          <el-form-item label="适用税率">
            <el-input-number
              v-model="form.tax_rate"
              :min="0"
              :max="20"
              :step="0.5"
              :controls="false"
              style="width: 100%"
              @change="calcResult"
            />
            <span class="unit">%</span>
          </el-form-item>

          <el-form-item label="挂靠费比例">
            <el-input-number
              v-model="form.management_fee_ratio"
              :min="0"
              :max="20"
              :step="0.5"
              :controls="false"
              style="width: 100%"
              @change="calcResult"
            />
            <span class="unit">%</span>
          </el-form-item>

          <el-form-item label="增值税税负率">
            <el-input-number
              v-model="form.vat_burden_rate"
              :min="0"
              :max="10"
              :step="0.1"
              :controls="false"
              style="width: 100%"
              @change="calcResult"
            />
            <span class="unit">%</span>
          </el-form-item>

          <el-form-item label="所得税税负率">
            <el-input-number
              v-model="form.income_tax_burden_rate"
              :min="0"
              :max="10"
              :step="0.1"
              :controls="false"
              style="width: 100%"
              @change="calcResult"
            />
            <span class="unit">%</span>
          </el-form-item>

          <!-- 先扣后返模式的额外输入 -->
          <template v-if="calcMode === 'pre_deduct'">
            <el-divider>提供的发票</el-divider>
            <el-form-item label="已提供进项税">
              <el-input-number
                v-model="form.provided_input_tax"
                :min="0"
                :step="1000"
                :controls="false"
                style="width: 100%"
                @change="calcResult"
              />
              <span class="unit">元</span>
            </el-form-item>
            <el-form-item label="已提供成本票(不含税)">
              <el-input-number
                v-model="form.provided_cost_invoice"
                :min="0"
                :step="10000"
                :controls="false"
                style="width: 100%"
                @change="calcResult"
              />
              <span class="unit">元</span>
            </el-form-item>
          </template>
        </el-form>
      </div>

      <!-- 右侧：结果区 -->
      <div class="result-section">
        <div class="section-title">
          <el-icon><TrendCharts /></el-icon>
          <span>计算结果</span>
        </div>

        <!-- 核心指标卡 -->
        <div class="result-cards">
          <div class="result-card main-card">
            <div class="card-label">{{ calcMode === 'standard' ? '实际到手' : '实付金额' }}</div>
            <div class="card-value">
              {{ formatMoney(calcMode === 'standard' ? result?.summary?.net_received : result?.pre_deduct_return?.result?.actual_payment) }}
            </div>
            <div class="card-sub">
              综合费率 {{ calcMode === 'standard' ? result?.summary?.comprehensive_tax_rate : preDeductComprehensiveRate }}%
            </div>
          </div>
          <div class="result-card">
            <div class="card-label">价税合计</div>
            <div class="card-value small">{{ formatMoney(form.contract_amount) }}</div>
          </div>
          <div class="result-card">
            <div class="card-label">不含税金额</div>
            <div class="card-value small">{{ formatMoney(result?.basic?.amount_no_tax) }}</div>
          </div>
        </div>

        <!-- 标准模式结果 -->
        <template v-if="calcMode === 'standard'">
          <div class="result-block">
            <div class="block-title">各项税费明细</div>
            <div class="tax-item-list">
              <div
                v-for="item in result?.tax_items"
                :key="item.name"
                class="tax-item"
              >
                <span class="tax-name">{{ item.name }}</span>
                <span class="tax-amount">{{ formatMoney(item.amount) }}</span>
              </div>
              <div class="tax-item total-row">
                <span class="tax-name">税费合计</span>
                <span class="tax-amount">{{ formatMoney(result?.summary?.total_tax) }}</span>
              </div>
              <div class="tax-item total-row highlight">
                <span class="tax-name">合计扣款</span>
                <span class="tax-amount">{{ formatMoney(result?.summary?.total_deduction) }}</span>
              </div>
            </div>
          </div>

          <div class="result-block">
            <div class="block-title">发票需求</div>
            <div class="tax-item-list">
              <div class="tax-item">
                <span class="tax-name">需要进项税</span>
                <span class="tax-amount">{{ formatMoney(result?.invoice_need?.input_tax_needed) }}</span>
              </div>
              <div class="tax-item">
                <span class="tax-name">需成本票(不含税)</span>
                <span class="tax-amount">{{ formatMoney(result?.invoice_need?.cost_invoice_needed_no_tax) }}</span>
              </div>
              <div class="tax-item">
                <span class="tax-name">需成本票(含税)</span>
                <span class="tax-amount">{{ formatMoney(result?.invoice_need?.cost_invoice_needed_with_tax) }}</span>
              </div>
              <div class="tax-item">
                <span class="tax-name">账面利润</span>
                <span class="tax-amount">{{ formatMoney(result?.invoice_need?.book_profit) }}</span>
              </div>
              <div class="tax-item">
                <span class="tax-name">分红个税</span>
                <span class="tax-amount">{{ formatMoney(result?.invoice_need?.dividend_tax) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- 先扣后返模式结果 -->
        <template v-else>
          <div class="result-block">
            <div class="block-title">先扣部分</div>
            <div class="tax-item-list">
              <div class="tax-item">
                <span class="tax-name">增值税(全额)</span>
                <span class="tax-amount">{{ formatMoney(result?.pre_deduct_return?.pre_deduct?.vat) }}</span>
              </div>
              <div class="tax-item">
                <span class="tax-name">附加税</span>
                <span class="tax-amount">{{ formatMoney(result?.pre_deduct_return?.pre_deduct?.surtax) }}</span>
              </div>
              <div class="tax-item">
                <span class="tax-name">所得税(按25%利润)</span>
                <span class="tax-amount">{{ formatMoney(result?.pre_deduct_return?.pre_deduct?.income_tax) }}</span>
              </div>
              <div class="tax-item">
                <span class="tax-name">印花税</span>
                <span class="tax-amount">{{ formatMoney(result?.pre_deduct_return?.pre_deduct?.stamp_tax) }}</span>
              </div>
              <div class="tax-item">
                <span class="tax-name">管理费</span>
                <span class="tax-amount">{{ formatMoney(result?.pre_deduct_return?.pre_deduct?.management_fee) }}</span>
              </div>
              <div class="tax-item total-row highlight">
                <span class="tax-name">先扣总额</span>
                <span class="tax-amount">{{ formatMoney(result?.pre_deduct_return?.pre_deduct?.total) }}</span>
              </div>
            </div>
          </div>

          <div class="result-block">
            <div class="block-title">后返部分</div>
            <div class="tax-item-list">
              <div class="tax-item return-item">
                <span class="tax-name">进项税返还</span>
                <span class="tax-amount">+{{ formatMoney(result?.pre_deduct_return?.returns?.input_tax_return) }}</span>
              </div>
              <div class="tax-item return-item">
                <span class="tax-name">附加税返还</span>
                <span class="tax-amount">+{{ formatMoney(result?.pre_deduct_return?.returns?.surtax_return) }}</span>
              </div>
              <div class="tax-item return-item">
                <span class="tax-name">所得税返还</span>
                <span class="tax-amount">+{{ formatMoney(result?.pre_deduct_return?.returns?.income_tax_return) }}</span>
              </div>
              <div class="tax-item total-row return-item">
                <span class="tax-name">总返还</span>
                <span class="tax-amount">+{{ formatMoney(result?.pre_deduct_return?.returns?.total_return) }}</span>
              </div>
            </div>
          </div>

          <div class="result-block">
            <div class="block-title">发票缺口</div>
            <div class="tax-item-list">
              <div class="tax-item">
                <span class="tax-name">进项税缺口</span>
                <span class="tax-amount" :class="{ 'warning-text': result?.pre_deduct_return?.gap?.input_tax_shortfall > 0 }">
                  {{ formatMoney(result?.pre_deduct_return?.gap?.input_tax_shortfall) }}
                </span>
              </div>
              <div class="tax-item">
                <span class="tax-name">成本票缺口(按75%)</span>
                <span class="tax-amount" :class="{ 'warning-text': result?.pre_deduct_return?.gap?.cost_invoice_shortfall > 0 }">
                  {{ formatMoney(result?.pre_deduct_return?.gap?.cost_invoice_shortfall) }}
                </span>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Calculator, TrendCharts } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const calcMode = ref('standard')
const activeScene = ref('')

// 预设场景
const presetScenes = [
  {
    name: '房建项目1000万',
    form: {
      contract_amount: 10000000,
      tax_rate: 9,
      management_fee_ratio: 2,
      vat_burden_rate: 2.5,
      income_tax_burden_rate: 1.5,
      provided_input_tax: 500000,
      provided_cost_invoice: 7000000,
    }
  },
  {
    name: '市政项目500万',
    form: {
      contract_amount: 5000000,
      tax_rate: 9,
      management_fee_ratio: 1.5,
      vat_burden_rate: 2.0,
      income_tax_burden_rate: 1.2,
      provided_input_tax: 200000,
      provided_cost_invoice: 3500000,
    }
  },
  {
    name: '装修项目200万',
    form: {
      contract_amount: 2000000,
      tax_rate: 9,
      management_fee_ratio: 3,
      vat_burden_rate: 3.0,
      income_tax_burden_rate: 2.0,
      provided_input_tax: 60000,
      provided_cost_invoice: 1200000,
    }
  },
]

const form = reactive({
  contract_amount: 1000000,
  tax_rate: 9,
  management_fee_ratio: 2,
  vat_burden_rate: 2.5,
  income_tax_burden_rate: 1.5,
  provided_input_tax: 0,
  provided_cost_invoice: 0,
})

const result = ref(null)

// 先扣后返的综合费率
const preDeductComprehensiveRate = computed(() => {
  if (!result.value?.pre_deduct_return) return 0
  const total = form.contract_amount - result.value.pre_deduct_return.result.actual_payment
  return ((total / form.contract_amount) * 100).toFixed(2)
})

function applyScene(scene) {
  activeScene.value = scene.name
  Object.assign(form, scene.form)
  calcResult()
}

// 前端直接计算（无需调后端，响应更快）
function calcResult() {
  // 标准模式计算
  const contractAmount = form.contract_amount
  const taxRate = form.tax_rate / 100
  const mgmtFeeRatio = form.management_fee_ratio / 100
  const vatBurden = form.vat_burden_rate / 100
  const incomeTaxBurden = form.income_tax_burden_rate / 100

  const amountNoTax = contractAmount / (1 + taxRate)
  const outputTax = amountNoTax * taxRate
  const vatPayable = amountNoTax * vatBurden
  const surtaxPayable = vatPayable * 0.12
  const incomeTaxPayable = amountNoTax * incomeTaxBurden
  const managementFee = contractAmount * mgmtFeeRatio
  const stampTax = amountNoTax * 0.0003 * 2
  const totalTax = vatPayable + surtaxPayable + incomeTaxPayable + stampTax
  const totalDeduction = totalTax + managementFee
  const netReceived = contractAmount - totalDeduction
  const comprehensiveRate = (totalDeduction / contractAmount) * 100

  const inputTaxNeeded = outputTax - vatPayable
  const bookProfit = incomeTaxPayable / 0.25
  const costInvoiceNeededNoTax = amountNoTax - stampTax - surtaxPayable - bookProfit
  const costInvoiceNeededWithTax = costInvoiceNeededNoTax + inputTaxNeeded
  const dividendTax = (bookProfit - incomeTaxPayable) * 0.2

  const standardResult = {
    input: {
      contract_amount: contractAmount,
      tax_rate: form.tax_rate,
      management_fee_ratio: form.management_fee_ratio,
      vat_burden_rate: form.vat_burden_rate,
      income_tax_burden_rate: form.income_tax_burden_rate,
    },
    basic: {
      amount_no_tax: round2(amountNoTax),
      output_tax: round2(outputTax),
    },
    tax_items: [
      { name: '增值税', amount: round2(vatPayable), category: '流转税' },
      { name: '附加税(城建+教附)', amount: round2(surtaxPayable), category: '附加税' },
      { name: '企业所得税', amount: round2(incomeTaxPayable), category: '所得税' },
      { name: '印花税', amount: round2(stampTax), category: '其他税' },
      { name: '挂靠管理费', amount: round2(managementFee), category: '管理费' },
    ],
    summary: {
      total_tax: round2(totalTax),
      total_deduction: round2(totalDeduction),
      net_received: round2(netReceived),
      comprehensive_tax_rate: round2(comprehensiveRate),
    },
    invoice_need: {
      input_tax_needed: round2(inputTaxNeeded),
      cost_invoice_needed_no_tax: round2(costInvoiceNeededNoTax),
      cost_invoice_needed_with_tax: round2(costInvoiceNeededWithTax),
      book_profit: round2(bookProfit),
      dividend_tax: round2(dividendTax),
    },
  }

  // 先扣后返模式
  if (calcMode.value === 'pre_deduct') {
    const providedInputTax = form.provided_input_tax
    const providedCostInvoice = form.provided_cost_invoice

    // 先扣
    const vatPreDeduct = outputTax
    const surtaxPreDeduct = vatPreDeduct * 0.12
    const incomeTaxPreDeduct = amountNoTax * 0.25 * 0.25
    const totalPreDeduct = vatPreDeduct + surtaxPreDeduct + incomeTaxPreDeduct + stampTax + managementFee

    // 后返
    const inputTaxReturn = Math.min(providedInputTax, vatPreDeduct)
    const surtaxReturn = inputTaxReturn * 0.12
    const incomeTaxReturn = Math.min(providedCostInvoice * 0.25, incomeTaxPreDeduct)
    const totalReturn = inputTaxReturn + surtaxReturn + incomeTaxReturn

    const actualPayment = contractAmount - totalPreDeduct + totalReturn

    const targetVat = amountNoTax * vatBurden
    const targetIncomeTax = amountNoTax * incomeTaxBurden

    result.value = {
      ...standardResult,
      pre_deduct_return: {
        pre_deduct: {
          vat: round2(vatPreDeduct),
          surtax: round2(surtaxPreDeduct),
          income_tax: round2(incomeTaxPreDeduct),
          stamp_tax: round2(stampTax),
          management_fee: round2(managementFee),
          total: round2(totalPreDeduct),
        },
        returns: {
          input_tax_return: round2(inputTaxReturn),
          surtax_return: round2(surtaxReturn),
          income_tax_return: round2(incomeTaxReturn),
          total_return: round2(totalReturn),
        },
        provided: {
          input_tax: round2(providedInputTax),
          cost_invoice_no_tax: round2(providedCostInvoice),
        },
        result: {
          actual_payment: round2(actualPayment),
          actual_vat: round2(vatPreDeduct - inputTaxReturn),
          actual_income_tax: round2(incomeTaxPreDeduct - incomeTaxReturn),
        },
        gap: {
          input_tax_shortfall: round2(Math.max(outputTax - providedInputTax, 0)),
          cost_invoice_shortfall: round2(Math.max(amountNoTax * 0.75 - providedCostInvoice, 0)),
        },
        target_burden: {
          target_vat: round2(targetVat),
          target_income_tax: round2(targetIncomeTax),
        },
        conclusion: `先扣${round2(totalPreDeduct)}元，返还${round2(totalReturn)}元，实付${round2(actualPayment)}元`,
      }
    }
  } else {
    result.value = standardResult
  }
}

function round2(val) {
  return Math.round(val * 100) / 100
}

function formatMoney(val) {
  if (val === undefined || val === null) return '0.00'
  const num = parseFloat(val)
  if (Math.abs(num) >= 100000000) return (num / 100000000).toFixed(2) + '亿'
  if (Math.abs(num) >= 10000) return (num / 10000).toFixed(2) + '万'
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

onMounted(() => {
  calcResult()
})
</script>

<style scoped>
.tax-calc-page {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #0a1f44;
  margin-bottom: 8px;
}

.page-subtitle {
  color: #909399;
  margin-bottom: 20px;
}

.preset-scenes {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.calc-container {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.input-section,
.result-section {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #0a1f44;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.section-title .el-icon {
  color: #c9a24a;
}

.mode-tabs {
  margin-bottom: 20px;
}

.unit {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}

.result-cards {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.result-card {
  flex: 1;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.result-card.main-card {
  background: linear-gradient(135deg, #0a1f44 0%, #1a3a6b 100%);
  color: #fff;
}

.result-card.main-card .card-label {
  color: rgba(255, 255, 255, 0.8);
}

.result-card.main-card .card-sub {
  color: #c9a24a;
}

.card-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.card-value {
  font-size: 22px;
  font-weight: bold;
  color: #0a1f44;
}

.card-value.small {
  font-size: 16px;
}

.card-sub {
  font-size: 12px;
  color: #c9a24a;
  margin-top: 6px;
}

.result-block {
  margin-bottom: 20px;
}

.block-title {
  font-size: 14px;
  font-weight: 600;
  color: #0a1f44;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #c9a24a;
}

.tax-item-list {
  background: #fafafa;
  border-radius: 6px;
  overflow: hidden;
}

.tax-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.tax-item:last-child {
  border-bottom: none;
}

.tax-item.total-row {
  background: #f0f2f5;
  font-weight: 600;
}

.tax-item.total-row.highlight {
  background: linear-gradient(90deg, #f0f2f5, #e8ecf1);
  color: #0a1f44;
}

.tax-item.return-item .tax-amount {
  color: #67c23a;
}

.tax-name {
  color: #606266;
}

.tax-amount {
  font-weight: 500;
  color: #303133;
}

.tax-amount.warning-text {
  color: #f56c6c;
}
</style>
