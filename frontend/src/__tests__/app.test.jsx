import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../api/client', () => ({ getHealth: vi.fn(), getModelInfo: vi.fn(), getMetrics: vi.fn(), predictTraffic: vi.fn() }))
import { getHealth, getModelInfo, getMetrics, predictTraffic } from '../api/client'
import App from '../App'

globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
beforeAll(async () => {
  await Promise.all([
    import('../pages/Dashboard.jsx'), import('../pages/TrafficAnalysis.jsx'),
    import('../pages/ModelPerformance.jsx'), import('../pages/About.jsx'),
  ])
})

const metrics = { selected_model: 'Decision Tree', selection_criteria: 'Test selection', models: {
  'Logistic Regression': { accuracy: .79, precision: .98, recall: .71, f1: .82, training_seconds: 1, prediction_seconds: .2, confusion_matrix: [[10, 2], [3, 8]] },
  'K-Nearest Neighbors': { accuracy: .89, precision: .97, recall: .87, f1: .92, training_seconds: 2, prediction_seconds: 5, confusion_matrix: [[9, 3], [2, 9]] },
  'Decision Tree': { accuracy: .90, precision: .97, recall: .88, f1: .92, training_seconds: 1, prediction_seconds: .1, confusion_matrix: [[11, 1], [2, 9]] },
} }
const modelInfo = { selected_model: 'Decision Tree', feature_count: 10, feature_names: ['dur','proto','service','sbytes','dbytes','spkts','dpkts','sttl','dttl','ct_srv_src'], dataset: { training_records: 100, testing_records: 24, testing_class_counts: { '0': 12, '1': 12 } } }
function mount(path = '/') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><App/></MemoryRouter></QueryClientProvider>)
}
afterEach(() => { cleanup(); vi.clearAllMocks() })

describe('NetGuard dashboard', () => {
  it('renders backend-backed overview metrics and navigates between pages', async () => {
    getHealth.mockResolvedValue({ status: 'ok', model_loaded: true })
    getModelInfo.mockResolvedValue(modelInfo)
    getMetrics.mockResolvedValue(metrics)
    mount()
    expect(await screen.findByText('Network defense overview', {}, { timeout: 5000 })).toBeTruthy()
    expect(await screen.findByText('90.0%', {}, { timeout: 5000 })).toBeTruthy()
    fireEvent.click(screen.getByRole('link', { name: /Model Performance/ }))
    expect(await screen.findByText('Model performance', {}, { timeout: 5000 })).toBeTruthy()
    expect(await screen.findByText('Algorithm comparison')).toBeTruthy()
  })

  it('submits validated traffic features and shows the prediction response', async () => {
    getHealth.mockResolvedValue({ status: 'ok', model_loaded: true })
    predictTraffic.mockResolvedValue({ label: 1, class_name: 'Attack', model: 'Decision Tree', probabilities: { '0': .2, '1': .8 }, explanation: 'Model prediction only.' })
    const { container } = mount('/analysis')
    expect(await screen.findByText('Classify a traffic record')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /Predict traffic/ }))
    expect(predictTraffic).not.toHaveBeenCalled()
    const entries = { dur: '0.12', proto: 'tcp', service: 'http', sbytes: '1000', dbytes: '500', spkts: '10', dpkts: '8', sttl: '64', dttl: '252', ct_srv_src: '2' }
    for (const [name, value] of Object.entries(entries)) fireEvent.change(document.querySelector(`[name="${name}"]`), { target: { value } })
    fireEvent.click(screen.getByRole('button', { name: /Predict traffic/ }))
    await waitFor(() => expect(container.querySelector('.result-label')?.textContent).toBe('Attack'))
    await waitFor(() => expect(predictTraffic).toHaveBeenCalled())
    expect(predictTraffic.mock.calls[0][0]).toEqual({ dur: .12, proto: 'tcp', service: 'http', sbytes: 1000, dbytes: 500, spkts: 10, dpkts: 8, sttl: 64, dttl: 252, ct_srv_src: 2 })
  })

  it('shows API errors instead of invented model metrics', async () => {
    getHealth.mockRejectedValue(new Error('API unavailable'))
    getModelInfo.mockRejectedValue(new Error('API unavailable'))
    getMetrics.mockRejectedValue(new Error('API unavailable'))
    mount()
    expect(await screen.findByText(/API unavailable/)).toBeTruthy()
    expect(screen.queryByText('90.0%')).toBeNull()
  })
})
