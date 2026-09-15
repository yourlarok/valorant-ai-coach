const BASE = '/api'

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
export async function getPlan(name) {
  const r = await fetch(`${BASE}/plan?name=${encodeURIComponent(name)}`)
  if (!r.ok) throw new Error((await r.json()).detail || '获取训练计划失败')
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
