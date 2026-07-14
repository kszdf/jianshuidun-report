import request from '@/utils/request'

// 科目映射列表
export function getSubjectMapping(params) {
  return request({
    url: '/config/subject-mapping',
    method: 'get',
    params
  })
}

// 更新科目映射
export function updateSubjectMapping(data) {
  return request({
    url: '/config/subject-mapping/update',
    method: 'post',
    data
  })
}

// 标准科目列表
export function getStdSubjects() {
  return request({
    url: '/config/std-subjects',
    method: 'get'
  })
}

// 项目列表
export function getProjects(params) {
  return request({
    url: '/config/projects',
    method: 'get',
    params
  })
}

// 银行账户列表
export function getBankAccounts() {
  return request({
    url: '/config/bank-accounts',
    method: 'get'
  })
}
