import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from '../App'
import * as api from '../services/api'
import type { AnalysisResponse, HealthResponse, ModelInfoResponse } from '../types/api'

vi.mock('../services/api', async () => {
  const actual = await vi.importActual<typeof api>('../services/api')
  return {
    ...actual,
    checkHealth: vi.fn(),
    getModelInfo: vi.fn(),
    analyzeCode: vi.fn(),
  }
})

describe('App Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    const mockHealth: HealthResponse = {
      status: 'healthy',
      version: '0.1.0',
      environment: 'development',
    }
    const mockModel: ModelInfoResponse = {
      status: 'loaded',
      model_name: 'TypeMind_PatternClassifier',
      model_architecture: 'RandomForestClassifier',
      features_count: 47,
      classes: ['type_mismatch', 'incompatible_return'],
    }

    vi.mocked(api.checkHealth).mockResolvedValue(mockHealth)
    vi.mocked(api.getModelInfo).mockResolvedValue(mockModel)
  })

  it('renders top navigation branding and tagline', async () => {
    render(<App />)

    expect(screen.getAllByText(/TypeMind/i)[0]).toBeInTheDocument()
    expect(screen.getByText('Understand Code. Detect Errors. Think Smarter.')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText(/Ready \(RandomForestClassifier\)/i)).toBeInTheDocument()
    })
  })

  it('triggers code analysis when Analyze Code button is clicked', async () => {
    const mockAnalysisResponse: AnalysisResponse = {
      status: 'success',
      syntax_error: null,
      findings: [],
      summary: {
        total_findings: 0,
        rule_based_findings: 0,
        ml_predicted_findings: 0,
        errors_count: 0,
        warnings_count: 0,
        syntax_errors_count: 0,
        category_counts: {},
        severity_counts: {},
        execution_time_ms: 1.5,
        lines_analyzed: 4,
      },
      server_version: '0.1.0',
    }

    vi.mocked(api.analyzeCode).mockResolvedValue(mockAnalysisResponse)

    render(<App />)

    const analyzeBtn = screen.getByRole('button', { name: /Analyze Code/i })
    expect(analyzeBtn).toBeInTheDocument()

    fireEvent.click(analyzeBtn)

    await waitFor(() => {
      expect(api.analyzeCode).toHaveBeenCalledTimes(1)
      expect(screen.getByText(/Clean Code! No Type Errors Found/i)).toBeInTheDocument()
    })
  })

  it('loads sample code when sample scenario button is clicked', async () => {
    render(<App />)

    const validProgramBtn = screen.getByRole('button', { name: /Valid Program/i })
    fireEvent.click(validProgramBtn)

    await waitFor(() => {
      const textarea = screen.getByLabelText(/Python source code editor/i) as HTMLTextAreaElement
      expect(textarea.value).toContain('def calculate_order_total')
    })
  })
})
