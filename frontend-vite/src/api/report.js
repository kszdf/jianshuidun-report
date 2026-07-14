import request from '@/utils/request'

// 经营驾驶舱
export function getDashboard(period) {
  return request({
    url: '/report/dashboard',
    method: 'get',
    params: period ? { period } : {}
  })
}

// 项目利润表
export function getProjectProfit(period) {
  return request({
    url: '/report/project-profit',
    method: 'get',
    params: period ? { period } : {}
  })
}

// 资金日报
export function getCashDaily(reportDate) {
  return request({
    url: '/report/cash-daily',
    method: 'get',
    params: reportDate ? { report_date: reportDate } : {}
  })
}

// 应收账龄
export function getArAging(period) {
  return request({
    url: '/report/ar-aging',
    method: 'get',
    params: period ? { period } : {}
  })
}
