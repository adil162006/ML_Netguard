const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
async function get(path) {
  const response = await fetch(`${BASE}${path}`)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`)
  return body
}
export const getHealth = () => get('/health')
export const getModelInfo = () => get('/api/model-info')
export const getMetrics = () => get('/api/metrics')
export async function predictTraffic(record) {
  const response = await fetch(`${BASE}/api/predict`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(record) })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `Prediction failed (${response.status})`)
  return body
}
