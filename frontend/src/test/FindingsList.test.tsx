import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FindingsList } from '../components/Diagnostics/FindingsList'
import type { AnalysisResponse } from '../types/api'

describe('FindingsList Component', () => {
  it('renders initial empty state when no response has been returned', () => {
    render(
      <FindingsList
        response={null}
        error={null}
        isAnalyzing={false}
        selectedFindingId={null}
        onSelectFinding={vi.fn()}
        onSelectLine={vi.fn()}
      />
    )

    expect(screen.getByText(/Ready for Semantic Analysis/i)).toBeInTheDocument()
  })

  it('renders clean code success state when findings are empty', () => {
    const cleanResponse: AnalysisResponse = {
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
        execution_time_ms: 1.2,
        lines_analyzed: 5,
      },
      server_version: '0.1.0',
    }

    render(
      <FindingsList
        response={cleanResponse}
        error={null}
        isAnalyzing={false}
        selectedFindingId={null}
        onSelectFinding={vi.fn()}
        onSelectLine={vi.fn()}
      />
    )

    expect(screen.getByText(/Clean Code! No Type Errors Found/i)).toBeInTheDocument()
  })

  it('renders finding with expected/observed types, explanation, and fix diff', () => {
    const errorResponse: AnalysisResponse = {
      status: 'success',
      syntax_error: null,
      findings: [
        {
          id: 'test-finding-1',
          message: "Cannot concatenate 'str' and 'int'",
          category: 'type_mismatch',
          severity: 'error',
          location: { line: 2, column: 15, end_line: 2, end_column: 22 },
          origin: 'hybrid',
          is_confirmed: true,
          expected_type: { raw_type: 'str' },
          observed_type: { raw_type: 'int' },
          rule_id: 'TM001_STRING_NUMBER_CONCAT',
          explanation: 'Strings cannot be concatenated with numbers directly in Python.',
          suggested_fixes: [
            {
              id: 'fix-1',
              title: 'Convert operand with str()',
              description: 'Wrap expression in str()',
              replacements: [
                {
                  location: { line: 2, column: 15, end_line: 2, end_column: 22 },
                  new_text: 'str(42)',
                },
              ],
              diff_preview: '- 42\n+ str(42)',
            },
          ],
        },
      ],
      summary: {
        total_findings: 1,
        rule_based_findings: 1,
        ml_predicted_findings: 1,
        errors_count: 1,
        warnings_count: 0,
        syntax_errors_count: 0,
        category_counts: { type_mismatch: 1 },
        severity_counts: { error: 1 },
        execution_time_ms: 2.5,
        lines_analyzed: 4,
      },
      server_version: '0.1.0',
    }

    const onSelectFinding = vi.fn()

    render(
      <FindingsList
        response={errorResponse}
        error={null}
        isAnalyzing={false}
        selectedFindingId="test-finding-1"
        onSelectFinding={onSelectFinding}
        onSelectLine={vi.fn()}
      />
    )

    // Verify finding message and badges
    expect(screen.getByText("Cannot concatenate 'str' and 'int'")).toBeInTheDocument()
    expect(screen.getByText('TM001_STRING_NUMBER_CONCAT')).toBeInTheDocument()
    expect(screen.getByText('str')).toBeInTheDocument()
    expect(screen.getByText('int')).toBeInTheDocument()
    expect(screen.getByText(/Strings cannot be concatenated with numbers/i)).toBeInTheDocument()
    expect(screen.getByText(/Convert operand with str\(\)/i)).toBeInTheDocument()
    expect(screen.getByText('- 42')).toBeInTheDocument()
    expect(screen.getByText('+ str(42)')).toBeInTheDocument()
  })

  it('renders dedicated syntax error card when syntax error occurs', () => {
    const syntaxResponse: AnalysisResponse = {
      status: 'syntax_error',
      syntax_error: {
        id: 'syntax-1',
        message: 'expected colon after function parameter list',
        category: 'syntax_error',
        severity: 'error',
        location: { line: 1, column: 22 },
        origin: 'rule_based',
        is_confirmed: true,
        rule_id: 'TM000_SYNTAX_ERROR',
        suggested_fixes: [],
      },
      findings: [],
      summary: {
        total_findings: 0,
        rule_based_findings: 0,
        ml_predicted_findings: 0,
        errors_count: 0,
        warnings_count: 0,
        syntax_errors_count: 1,
        category_counts: {},
        severity_counts: {},
        execution_time_ms: 0.8,
        lines_analyzed: 1,
      },
      server_version: '0.1.0',
    }

    render(
      <FindingsList
        response={syntaxResponse}
        error={null}
        isAnalyzing={false}
        selectedFindingId={null}
        onSelectFinding={vi.fn()}
        onSelectLine={vi.fn()}
      />
    )

    expect(screen.getByText(/Python Syntax Error/i)).toBeInTheDocument()
    expect(screen.getByText(/expected colon after function parameter list/i)).toBeInTheDocument()
    expect(screen.getByText('TM000_SYNTAX_ERROR')).toBeInTheDocument()
  })
})
