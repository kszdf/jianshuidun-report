import request from '@/utils/request'

// 映射统计
export function getMappingStats() {
  return request({
    url: '/import/mapping-stats',
    method: 'get'
  })
}

// 自动映射
export function autoMapSubjects() {
  return request({
    url: '/import/auto-map',
    method: 'post'
  })
}

// 上传科目余额表
export function uploadBalance(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/import/balance',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 上传凭证/序时账
export function uploadVoucher(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/import/voucher',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
