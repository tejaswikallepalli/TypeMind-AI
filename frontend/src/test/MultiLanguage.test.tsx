import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { App } from '../App'
import * as api from '../services/api'
import type { AnalysisResponse, LanguagesResponse } from '../types/api'

vi.mock('../services/api', async () => {
  const actual = await vi.importActual('../services/api')
  return {
    ...actual,
    analyzeCode: vi.fn(),
    checkHealth: vi.fn().mockResolvedValue({ status: 'healthy', version: '0.1.0', environment: 'development' }),
    getModelInfo: vi.fn().mockResolvedValue({ status: 'loaded', features_count: 47, classes: ['TM001'] }),
    fetchLanguages: vi.fn().mockResolvedValue({
      languages: [
        { id: 'python', name: 'Python', extensions: ['.py'], support_level: 'supported', tool_name: 'Built-in AST + ML', tool_available: true, ml_supported: true, description: 'Python AST' },
        { id: 'typescript', name: 'TypeScript', extensions: ['.ts', '.tsx'], support_level: 'supported', tool_name: 'tsc --noEmit', tool_available: true, ml_supported: false, description: 'TypeScript Compiler' },
        { id: 'java', name: 'Java', extensions: ['.java'], support_level: 'tool_unavailable', tool_name: 'javac', tool_available: false, ml_supported: false, description: 'Java Compiler' },
        { id: 'c', name: 'C', extensions: ['.c'], support_level: 'tool_unavailable', tool_name: 'gcc', tool_available: false, ml_supported: false, description: 'C Compiler' },
      ],
      total: 4,
      default_language: 'python',
    } satisfies LanguagesResponse),
  }
})

describe('Multi-Language Analysis Workspace', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders the language selector dropdown with configured languages and status indicators', async () => {
    render(<App />)

    const select = screen.getByRole('combobox', { name: /Select Programming Language/i }) as HTMLSelectElement
    expect(select).toBeInTheDocument()
    expect(select.value).toBe('python')

    // Verify option entries
    const options = Array.from(select.options).map((o) => o.text)
    expect(options.some((o) => o.includes('Python'))).toBe(true)
    expect(options.some((o) => o.includes('TypeScript'))).toBe(true)
    expect(options.some((o) => o.includes('Java'))).toBe(true)
  })

  it('switches language and filters sample programs for that language', async () => {
    render(<App />)

    const select = screen.getByRole('combobox', { name: /Select Programming Language/i })
    fireEvent.change(select, { target: { value: 'typescript' } })

    // Verify language changed in dropdown
    expect((select as HTMLSelectElement).value).toBe('typescript')

    // Verify TypeScript samples appear in sample bar
    await waitFor(() => {
      expect(screen.getByText(/Sample Programs \(TypeScript\)/i)).toBeInTheDocument()
      expect(screen.getByText(/Type Mismatch \(TS2322\)/i)).toBeInTheDocument()
    })
  })

  it('sends language parameter in analyzeCode request when analyzing code', async () => {
    const mockResponse: AnalysisResponse = {
      status: 'success',
      language: 'typescript',
      analyzer_id: 'typescript_tsc_compiler',
      support_level: 'supported',
      findings: [
        {
          id: 'ts-err-1',
          message: '[TS2322] Type string is not assignable to type number',
          category: 'type_mismatch',
          severity: 'error',
          location: { file_path: 'test.ts', line: 2, column: 5 },
          origin: 'rule_based',
          is_confirmed: true,
          suggested_fixes: [],
        },
      ],
      summary: {
        total_findings: 1,
        rule_based_findings: 1,
        ml_predicted_findings: 0,
        errors_count: 1,
        warnings_count: 0,
        syntax_errors_count: 0,
        category_counts: { type_mismatch: 1 },
        severity_counts: { error: 1 },
        execution_time_ms: 22.4,
        lines_analyzed: 5,
      },
      server_version: '0.1.0',
    }

    vi.mocked(api.analyzeCode).mockResolvedValueOnce(mockResponse)

    render(<App />)

    // Switch to TypeScript
    const select = screen.getByRole('combobox', { name: /Select Programming Language/i })
    fireEvent.change(select, { target: { value: 'typescript' } })

    // Click Analyze
    const analyzeBtn = screen.getByRole('button', { name: /Analyze Code/i })
    fireEvent.click(analyzeBtn)

    await waitFor(() => {
      expect(api.analyzeCode).toHaveBeenCalledWith(
        expect.objectContaining({
          language: 'typescript',
          enable_ml_analysis: false, // ML disabled for non-python
        })
      )
      expect(screen.getByText(/Type string is not assignable to type number/i)).toBeInTheDocument()
    })
  })

  it('renders toolchain unavailable banner when backend reports tool_unavailable', async () => {
    const mockUnavailableResponse: AnalysisResponse = {
      status: 'tool_unavailable',
      language: 'java',
      analyzer_id: 'java_javac_compiler',
      support_level: 'tool_unavailable',
      status_message: "Java Compiler 'javac' is not installed on this system.",
      findings: [
        {
          id: 'tool-missing-java',
          message: "Java analyzer tool 'javac' is not available",
          category: 'syntax_error',
          severity: 'warning',
          location: { line: 1, column: 1 },
          origin: 'rule_based',
          is_confirmed: true,
          explanation: 'Install OpenJDK 17+ from Adoptium',
          suggested_fixes: [],
        },
      ],
      summary: {
        total_findings: 1,
        rule_based_findings: 1,
        ml_predicted_findings: 0,
        errors_count: 0,
        warnings_count: 1,
        syntax_errors_count: 0,
        category_counts: {},
        severity_counts: {},
        execution_time_ms: 0.1,
        lines_analyzed: 10,
      },
      server_version: '0.1.0',
    }

    vi.mocked(api.analyzeCode).mockResolvedValueOnce(mockUnavailableResponse)

    render(<App />)

    // Switch to Java
    const select = screen.getByRole('combobox', { name: /Select Programming Language/i })
    fireEvent.change(select, { target: { value: 'java' } })

    const analyzeBtn = screen.getByRole('button', { name: /Analyze Code/i })
    fireEvent.click(analyzeBtn)

    await waitFor(() => {
      expect(screen.getByText(/JAVA Analyzer Toolchain Unavailable/i)).toBeInTheDocument()
      expect(screen.getByText(/Java Compiler 'javac' is not installed/i)).toBeInTheDocument()
    })
  })
})
