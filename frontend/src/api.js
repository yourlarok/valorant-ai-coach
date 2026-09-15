const BASE = '/api'

export async function listMatches(name) {
  const r = await fetch(`${BASE}/matches?name=${encodeURIComponent(name)}`)
  return r.json()
}
export async function getAnalysis(matchId, name) {
  const r = await fetch(`${BASE}/analysis/${matchId}?name=${encodeURIComponent(name)}`)
  if (!r.ok) throw new Error((await r.json()).detail || '分析失败')
  return r.json()
}
export async function getPlan(name) {
  const r = await fetch(`${BASE}/plan?name=${encodeURIComponent(name)}`)
  return r.json()
}
export async function toggleTask(name, taskName, done) {
  const r = await fetch(`${BASE}/plan/toggle?name=${encodeURIComponent(name)}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_name: taskName, done }),
  })
  return r.json()
}
