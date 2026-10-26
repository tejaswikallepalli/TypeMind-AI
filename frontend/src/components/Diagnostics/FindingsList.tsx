import React, { useState, useMemo } from 'react'
import type { AnalysisResponse, DiagnosticFinding, SuggestedFix } from '../../types/api'
import { FindingItem } from './FindingItem'
import { SyntaxErrorCard } from './SyntaxErrorCard'
import { EmptyState } from './EmptyState'
import { SummaryCards } from './SummaryCards'
import { Sparkles } from 'lucide-react'

interface FindingsListProps {
  response: AnalysisResponse | null
  error: string | null
  isAnalyzing: boolean
  selectedFindingId: string | null
  onSelectFinding: (finding: DiagnosticFinding) => void
  onSelectLine: (line: number) => void
  onApplyFix?: (fix: SuggestedFix) => void
  onCopySuccess?: (msg: string) => void
  onRetry?: () => void
}

type SeverityFilter = 'all' | 'error' | 'warning' | 'ml'

export const FindingsList: React.FC<FindingsListProps> = ({
  response,
  error,
  isAnalyzing,
  selectedFindingId,
  onSelectFinding,
  onSelectLine,
  onApplyFix,
  onCopySuccess,
  onRetry,
}) => {
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  const findings = response?.findings || []
  const syntaxError = response?.syntax_error

  // Extract unique categories present in the findings for the dropdown
  const uniqueCategories = useMemo(() => {
    const set = new Set<string>()
    findings.forEach((f) => set.add(f.category))
    return Array.from(set)
  }, [findings])

  // Filtered findings
  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      if (severityFilter === 'error' && f.severity !== 'error') return false
      if (severityFilter === 'warning' && f.severity !== 'warning') return false
      if (severityFilter === 'ml' && f.origin !== 'ml_prediction' && f.origin !== 'hybrid') return false
      if (categoryFilter !== 'all' && f.category !== categoryFilter) return false
      return true
    })
  }, [findings, severityFilter, categoryFilter])

  // Count metrics for filter tabs
  const errorCount = findings.filter((f) => f.severity === 'error').length + (syntaxError ? 1 : 0)
  const warningCount = findings.filter((f) => f.severity === 'warning').length
  const mlCount = findings.filter((f) => f.origin === 'ml_prediction' || f.origin === 'hybrid').length

  return (
    <div className="pane-card">
      <div className="pane-header">
        <div className="pane-title">
          <Sparkles size={16} color="var(--accent-violet)" />
          <span>Diagnostic Intelligence</span>
          {response && (
            <span
              style={{
                fontSize: '0.75rem',
                backgroundColor: 'var(--bg-elevated)',
                padding: '2px 8px',
                borderRadius: '12px',
                color: 'var(--text-secondary)',
              }}
            >
              {findings.length + (syntaxError ? 1 : 0)} {findings.length === 1 && !syntaxError ? 'finding' : 'findings'}
            </span>
          )}
        </div>

        {/* Filter Controls */}
        {response && findings.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                className={`btn btn-sm ${severityFilter === 'all' ? 'btn-secondary' : 'btn-ghost'}`}
                onClick={() => setSeverityFilter('all')}
              >
                All ({findings.length})
              </button>
              <button
                className={`btn btn-sm ${severityFilter === 'error' ? 'btn-secondary' : 'btn-ghost'}`}
                onClick={() => setSeverityFilter('error')}
                style={{ color: errorCount > 0 ? 'var(--color-error-light)' : 'inherit' }}
              >
                Errors ({errorCount})
              </button>
              <button
                className={`btn btn-sm ${severityFilter === 'warning' ? 'btn-secondary' : 'btn-ghost'}`}
                onClick={() => setSeverityFilter('warning')}
                style={{ color: warningCount > 0 ? 'var(--color-warning-light)' : 'inherit' }}
              >
                Warnings ({warningCount})
              </button>
              <button
                className={`btn btn-sm ${severityFilter === 'ml' ? 'btn-secondary' : 'btn-ghost'}`}
                onClick={() => setSeverityFilter('ml')}
                style={{ color: mlCount > 0 ? 'var(--accent-violet-light)' : 'inherit' }}
              >
                ML ({mlCount})
              </button>
            </div>

            {uniqueCategories.length > 1 && (
              <select
                className="select-input"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                style={{ fontSize: '0.75rem', padding: '4px 8px' }}
                aria-label="Filter findings by category"
              >
                <option value="all">All Categories</option>
                {uniqueCategories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            )}
          </div>
        )}
      </div>

      <div className="findings-container">
        {/* Metric Summary Cards */}
        {response && <SummaryCards summary={response.summary} status={response.status} />}

        {/* Network Error State */}
        {error && <EmptyState type="network_error" errorMessage={error} onRetry={onRetry} />}

        {/* Initial Empty State */}
        {!response && !error && !isAnalyzing && <EmptyState type="initial" />}

        {/* Analyzing Loading Skeleton */}
        {isAnalyzing && (
          <div style={{ padding: '48px 16px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <div className="spinner" style={{ width: '28px', height: '28px', margin: '0 auto 16px' }} />
            <p style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Parsing Python AST & Running Type Inference...</p>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Vectorizing features and querying machine learning classifier
            </p>
          </div>
        )}

        {/* Syntax Error Card */}
        {syntaxError && <SyntaxErrorCard syntaxError={syntaxError} onSelectLine={onSelectLine} />}

        {/* Clean Code Success */}
        {response && response.status === 'success' && findings.length === 0 && (
          <EmptyState type="clean" />
        )}

        {/* Filtered Empty State */}
        {response && findings.length > 0 && filteredFindings.length === 0 && (
          <EmptyState type="filtered_empty" />
        )}

        {/* Findings List */}
        {filteredFindings.map((finding) => (
          <FindingItem
            key={finding.id}
            finding={finding}
            isSelected={selectedFindingId === finding.id}
            onSelect={() => onSelectFinding(finding)}
            onApplyFix={onApplyFix}
            onCopySuccess={onCopySuccess}
          />
        ))}
      </div>
    </div>
  )
}
