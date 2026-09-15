const BASE = '/api'

export async function getIdentity() {
  const r = await fetch(`${BASE}/identity`)
  if (!r.ok) throw new Error((await r.json()).detail || '获取身份信息失败')
  return r.json()
}
export async function bindIdentity(name) {
  const r = await fetch(`${BASE}/identity`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!r.ok) throw new Error((await r.json()).detail || '绑定身份失败')
  return r.json()
}
export async function getNotifications(unreadOnly = false) {
  const r = await fetch(`${BASE}/notifications?unread_only=${unreadOnly}`)
  if (!r.ok) throw new Error((await r.json()).detail || '获取通知失败')
  return r.json()
}
export async function markNotificationRead(id) {
  const r = await fetch(`${BASE}/notifications/${id}/read`, { method: 'POST' })
  if (!r.ok) throw new Error((await r.json()).detail || '标记已读失败')
  return r.json()
}
export async function markAllNotificationsRead() {
  const r = await fetch(`${BASE}/notifications/read-all`, { method: 'POST' })
  if (!r.ok) throw new Error((await r.json()).detail || '全部已读失败')
  return r.json()
}
export async function getAutomation() {
  const r = await fetch(`${BASE}/settings/automation`)
  if (!r.ok) throw new Error((await r.json()).detail || '获取自动化设置失败')
  return r.json()
}
export async function simulateNewMatch(name) {
  const r = await fetch(`${BASE}/dev/simulate-new-match?name=${encodeURIComponent(name)}`, {
    method: 'POST',
  })
  if (!r.ok) throw new Error((await r.json()).detail || '模拟新对局失败')
  return r.json()
}
export async function putAutomation(body) {
  const r = await fetch(`${BASE}/settings/automation`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error((await r.json()).detail || '保存自动化设置失败')
  return r.json()
}
export async function listMatches(name, count) {
  let url = `${BASE}/matches?name=${encodeURIComponent(name)}`
  if (count) url += `&count=${count}`
  const r = await fetch(url)
  if (!r.ok) throw new Error((await r.json()).detail || '获取对局列表失败')
  return r.json()
}
export async function getAnalysis(matchId, name) {
  const r = await fetch(`${BASE}/analysis/${matchId}?name=${encodeURIComponent(name)}`)
  if (!r.ok) throw new Error((await r.json()).detail || '分析失败')
  return r.json()
}
export async function getWeekly(name) {
  const r = await fetch(`${BASE}/analysis/weekly?name=${encodeURIComponent(name)}`)
  if (!r.ok) throw new Error((await r.json()).detail || '获取周度分析失败')
  return r.json()
}
export async function getPlan(name) {
  const r = await fetch(`${BASE}/plan?name=${encodeURIComponent(name)}`)
  if (!r.ok) throw new Error((await r.json()).detail || '获取训练计划失败')
  return r.json()
}
export async function getSettings() {
  const r = await fetch(`${BASE}/settings/llm`)
  if (!r.ok) throw new Error((await r.json()).detail || '获取 LLM 配置失败')
  return r.json()
}
export async function saveSettings(body) {
  const r = await fetch(`${BASE}/settings/llm`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error((await r.json()).detail || '保存 LLM 配置失败')
  return r.json()
}
export async function toggleTask(name, taskName, done) {
  const r = await fetch(`${BASE}/plan/toggle?name=${encodeURIComponent(name)}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_name: taskName, done }),
  })
  if (!r.ok) throw new Error((await r.json()).detail || '打卡保存失败')
  const data = await r.json()
  if (!data?.ok) throw new Error('打卡保存失败')
  return data
}
