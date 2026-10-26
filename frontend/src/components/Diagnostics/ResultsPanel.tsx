import React, { useState, useMemo } from 'react'
import type { AnalysisResponse, DiagnosticFinding, SuggestedFix } from '../../types/api'
import {
  ListFilter,
  Brain,
  GitCommit,
  XCircle,
  AlertTriangle,
  Info,
  LayoutGrid,
  Copy,
  Check,
  ChevronDown,
  Wand2,
  CheckCircle2,
  AlertOctagon,
} from 'lucide-react'

interface ResultsPanelProps {
  response: AnalysisResponse | null
  error: string | null
  isAnalyzing: boolean
  selectedFindingId: string | null
  onSelectFinding: (finding: DiagnosticFinding) => void
  onSelectLine: (line: number) => void
  onApplyFix?: (fix: SuggestedFix) => void
  onCopySuccess?: (msg: string) => void
  sourceCode: string
}

type TabType = 'results' | 'ai_insights' | 'flow'
type FilterType = 'all' | 'errors' | 'warnings' | 'suggestions'

export const ResultsPanel: React.FC<ResultsPanelProps> = ({
  response,
  error,
  isAnalyzing,
  selectedFindingId,
  onSelectFinding,
  onSelectLine,
  onApplyFix,
  onCopySuccess,
  sourceCode,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('results')
  const [activeFilter, setActiveFilter] = useState<FilterType>('all')
  const [copiedSnippetId, setCopiedSnippetId] = useState<string | null>(null)

  const findings = response?.findings || []
  const syntaxError = response?.syntax_error

  // Extract counts
  const errorCount =
    (response?.summary.errors_count || 0) + (syntaxError ? 1 : 0)
  const warningCount = response?.summary.warnings_count || 0
  const suggestionsCount = findings.reduce(
    (acc, f) => acc + (f.suggested_fixes ? f.suggested_fixes.length : 0),
    0
  )
  const totalIssuesCount =
    (response?.summary.total_findings || 0) + (syntaxError ? 1 : 0)

  // Filtered findings
  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      if (activeFilter === 'errors') return f.severity === 'error'
      if (activeFilter === 'warnings') return f.severity === 'warning'
      if (activeFilter === 'suggestions') return f.suggested_fixes && f.suggested_fixes.length > 0
      return true
    })
  }, [findings, activeFilter])

  // Extract snippet from source code if not provided
  const extractSnippet = (f: DiagnosticFinding): string => {
    const lines = sourceCode.split('\n')
    const lineIdx = f.location.line - 1
    if (lineIdx >= 0 && lineIdx < lines.length) {
      return lines[lineIdx].trim()
    }
    return ''
  }

  const handleCopySnippet = async (snippet: string, id: string) => {
    try {
      await navigator.clipboard.writeText(snippet)
      setCopiedSnippetId(id)
      onCopySuccess?.('Code snippet copied to clipboard!')
      setTimeout(() => setCopiedSnippetId(null), 2000)
    } catch {
      // fallback
    }
  }

  return (
    <div className="panel-card results-pane">
      {/* Header Tabs */}
      <div className="panel-header-tabs">
        <div className="tab-btn-group">
          <button
            className={`tab-btn ${activeTab === 'results' ? 'active' : ''}`}
            onClick={() => setActiveTab('results')}
          >
            <ListFilter size={14} />
            <span>Analysis Results</span>
          </button>

          <button
            className={`tab-btn ${activeTab === 'ai_insights' ? 'active' : ''}`}
            onClick={() => setActiveTab('ai_insights')}
          >
            <Brain size={14} color="#a855f7" />
            <span>AI Insights</span>
          </button>

          <button
            className={`tab-btn ${activeTab === 'flow' ? 'active' : ''}`}
            onClick={() => setActiveTab('flow')}
          >
            <GitCommit size={14} color="#38bdf8" />
            <span>Execution Flow (Beta)</span>
          </button>
        </div>
      </div>

      {/* Engine & Language Metadata Bar */}
      {response && (
        <div className="meta-engine-badge">
          <span>
            Target: <strong style={{ color: '#ffffff' }}>{(response.language || 'python').toUpperCase()}</strong> • Engine: <code>{response.analyzer_id || 'python_ast_semantic'}</code> • {response.summary.lines_analyzed} lines analyzed in {response.summary.execution_time_ms}ms
          </span>
        </div>
      )}

      {/* Tab 1: Analysis Results */}
      {activeTab === 'results' && (
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
          {/* Tool Unavailable Alert Banner if Compiler Missing */}
          {response?.status === 'tool_unavailable' && (
            <div className="tool-unavailable-banner">
              <div className="tool-unavailable-title">
                <AlertOctagon size={16} />
                <span>{(response.language || 'Language').toUpperCase()} Analyzer Toolchain Unavailable</span>
              </div>
              <div className="tool-unavailable-text">
                {response.status_message || (response.findings[0] && response.findings[0].explanation) || 'Required compiler tool is missing on this system.'}
              </div>
            </div>
          )}

          {/* Summary Metric Cards Row */}
          <div className="summary-cards-row">
            {/* Errors Card */}
            <div className="summary-metric-card errors">
              <XCircle size={20} color="#f87171" />
              <div>
                <div className="summary-metric-num">{errorCount}</div>
                <div className="summary-metric-label">Errors</div>
              </div>
            </div>

            {/* Warnings Card */}
            <div className="summary-metric-card warnings">
              <AlertTriangle size={20} color="#fbbf24" />
              <div>
                <div className="summary-metric-num">{warningCount}</div>
                <div className="summary-metric-label">Warnings</div>
              </div>
            </div>

            {/* Suggestions Card */}
            <div className="summary-metric-card suggestions">
              <Info size={20} color="#60a5fa" />
              <div>
                <div className="summary-metric-num">{suggestionsCount}</div>
                <div className="summary-metric-label">Suggestions</div>
              </div>
            </div>

            {/* Total Issues Card */}
            <div className="summary-metric-card total">
              <LayoutGrid size={20} color="#94a3b8" />
              <div>
                <div className="summary-metric-num">{totalIssuesCount}</div>
                <div className="summary-metric-label">Total Issues</div>
              </div>
            </div>
          </div>

          {/* Filter Pills Row */}
          <div className="filter-pills-row">
            <button
              className={`filter-pill ${activeFilter === 'all' ? 'active' : ''}`}
              onClick={() => setActiveFilter('all')}
            >
              All Issues ({totalIssuesCount})
            </button>

            <button
              className={`filter-pill ${activeFilter === 'errors' ? 'active' : ''}`}
              onClick={() => setActiveFilter('errors')}
            >
              Errors ({errorCount})
            </button>

            <button
              className={`filter-pill ${activeFilter === 'warnings' ? 'active' : ''}`}
              onClick={() => setActiveFilter('warnings')}
            >
              Warnings ({warningCount})
            </button>

            <button
              className={`filter-pill ${activeFilter === 'suggestions' ? 'active' : ''}`}
              onClick={() => setActiveFilter('suggestions')}
            >
              Suggestions ({suggestionsCount})
            </button>
          </div>

          {/* Findings Scrollable List */}
          <div className="findings-scroll-container">
            {/* Loading State */}
            {isAnalyzing && (
              <div style={{ padding: '40px 16px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                <div className="spinner" style={{ width: '26px', height: '26px', margin: '0 auto 12px' }} />
                <p style={{ fontWeight: 600, color: '#ffffff' }}>Running Semantic AST Analysis...</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Extracting features and querying ML pattern classifier
                </p>
              </div>
            )}

            {/* Network / General Error */}
            {error && (
              <div
                style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid var(--color-error-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px',
                  color: 'var(--color-error-light)',
                  fontSize: '0.825rem',
                }}
              >
                <strong>Error: </strong>
                {error}
              </div>
            )}

            {/* Syntax Error Card */}
            {syntaxError && (
              <div
                className="diagnostic-item-card severity-error"
                onClick={() => onSelectLine(syntaxError.location.line)}
              >
                <div className="diag-card-header">
                  <div className="diag-title-area">
                    <AlertOctagon size={16} color="var(--color-error)" />
                    <span className="diag-title-text">Python Syntax Error</span>
                  </div>
                  <div className="diag-right-meta">
                    <span className="diag-line-tag">Line {syntaxError.location.line}</span>
                    <span className="diag-severity-pill error">Error</span>
                  </div>
                </div>

                <div className="diag-snippet-box">
                  <code>{extractSnippet(syntaxError) || syntaxError.message}</code>
                </div>

                <p className="diag-explanation-p">{syntaxError.message}</p>
              </div>
            )}

            {/* Clean Code Success State */}
            {response && response.status === 'success' && findings.length === 0 && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '40px 20px',
                  textAlign: 'center',
                  gap: '10px',
                }}
              >
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--color-success-bg)',
                    border: '1px solid var(--color-success-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--color-success-light)',
                  }}
                >
                  <CheckCircle2 size={24} />
                </div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#ffffff' }}>
                  Clean Code! No Type Errors Found
                </h4>
                <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', maxWidth: '340px' }}>
                  The AST semantic analyzer and ML classifier verified that all expressions and assignments adhere to Python type rules.
                </p>
              </div>
            )}

            {/* Render Each Finding Card */}
            {filteredFindings.map((finding) => {
              const isSelected = selectedFindingId === finding.id
              const snippet = extractSnippet(finding)
              const expType = finding.expected_type?.raw_type
              const obsType = finding.observed_type?.raw_type

              // Human-friendly title matching reference design
              let displayTitle = finding.message
              if (finding.rule_id === 'TM001_STRING_NUMBER_CONCAT') {
                displayTitle = 'Type Mismatch in Addition'
              } else if (finding.rule_id === 'TM002_UNSUPPORTED_ARITHMETIC') {
                displayTitle = 'Incompatible Types in Operation'
              } else if (finding.rule_id === 'TM003_ARGUMENT_COUNT_MISMATCH') {
                displayTitle = 'Function Argument Count Mismatch'
              } else if (finding.rule_id === 'TM004_ARGUMENT_TYPE_MISMATCH') {
                displayTitle = 'Function Argument Type Mismatch'
              } else if (finding.rule_id === 'TM005_INCOMPATIBLE_RETURN') {
                displayTitle = 'Incompatible Return Type'
              } else if (finding.rule_id === 'TM006_INVALID_ANNOTATED_ASSIGNMENT') {
                displayTitle = 'Invalid Variable Assignment'
              } else if (finding.rule_id === 'TM007_INCOMPATIBLE_REASSIGNMENT') {
                displayTitle = 'Incompatible Type Reassignment'
              }

              return (
                <div
                  key={finding.id}
                  className={`diagnostic-item-card severity-${finding.severity} ${
                    isSelected ? 'is-selected' : ''
                  }`}
                  onClick={() => onSelectFinding(finding)}
                >
                  {/* Card Header */}
                  <div className="diag-card-header">
                    <div className="diag-title-area">
                      {finding.severity === 'error' ? (
                        <XCircle size={15} color="#f87171" />
                      ) : (
                        <AlertTriangle size={15} color="#fbbf24" />
                      )}
                      <span className="diag-title-text">{displayTitle}</span>
                    </div>

                    <div className="diag-right-meta">
                      <span className="diag-line-tag">Line {finding.location.line}</span>
                      <span className={`diag-severity-pill ${finding.severity}`}>
                        {finding.severity === 'error' ? 'Error' : 'Warning'}
                      </span>
                      <ChevronDown size={14} color="var(--text-muted)" />
                    </div>
                  </div>

                  {/* Code Snippet Box */}
                  {snippet && (
                    <div className="diag-snippet-box">
                      <code>{snippet}</code>
                      <button
                        className="btn-copy-icon"
                        title="Copy code snippet"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleCopySnippet(snippet, finding.id)
                        }}
                      >
                        {copiedSnippetId === finding.id ? (
                          <Check size={13} color="var(--color-success-light)" />
                        ) : (
                          <Copy size={13} />
                        )}
                      </button>
                    </div>
                  )}

                  {/* Expected vs Found Types */}
                  {(expType || obsType) && (
                    <div className="diag-types-meta">
                      {expType && (
                        <div className="exp">
                          Expected type:{' '}
                          <span className="exp-val">{expType}</span>
                        </div>
                      )}
                      {obsType && (
                        <div className="fnd">
                          Found type: <span className="fnd-val">{obsType}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Explanation */}
                  {finding.explanation && (
                    <p className="diag-explanation-p">{finding.explanation}</p>
                  )}

                  {/* Suggested Fixes (Diff Viewer + Apply) */}
                  {finding.suggested_fixes && finding.suggested_fixes.length > 0 && (
                    <div
                      style={{
                        marginTop: '10px',
                        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                        paddingTop: '8px',
                      }}
                    >
                      {finding.suggested_fixes.map((fix) => (
                        <div key={fix.id} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                              <Wand2 size={12} color="#38bdf8" />
                              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#38bdf8' }}>
                                Suggested Fix: {fix.title}
                              </span>
                            </div>

                            {onApplyFix && fix.replacements && fix.replacements.length > 0 && (
                              <button
                                className="btn btn-primary btn-sm"
                                style={{ padding: '2px 8px', fontSize: '0.7rem' }}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  onApplyFix(fix)
                                }}
                              >
                                Apply Fix
                              </button>
                            )}
                          </div>

                          {fix.diff_preview && (
                            <div className="diff-preview" style={{ margin: '4px 0 0 0', fontSize: '0.725rem' }}>
                              {fix.diff_preview.split('\n').map((dLine, dIdx) => (
                                <div
                                  key={dIdx}
                                  style={{
                                    color: dLine.startsWith('-')
                                      ? '#f87171'
                                      : dLine.startsWith('+')
                                      ? '#34d399'
                                      : 'inherit',
                                  }}
                                >
                                  {dLine}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Tab 2: AI Insights */}
      {activeTab === 'ai_insights' && (
        <div style={{ padding: '16px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--accent-purple-border)',
              borderRadius: 'var(--radius-md)',
              padding: '14px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Brain size={18} color="var(--accent-purple-light)" />
              <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#ffffff' }}>
                Machine Learning Pattern Classifier
              </h4>
            </div>

            <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', lineHeight: 1.45, marginBottom: '10px' }}>
              TypeMind AI pairs deterministic static AST rules with a trained Random Forest model. The model scores structural syntax tree features to detect type anomalies and corroborates static rules.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
              <div style={{ backgroundColor: 'var(--bg-input)', padding: '8px 10px', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Algorithm</span>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ffffff' }}>Random Forest</div>
              </div>
              <div style={{ backgroundColor: 'var(--bg-input)', padding: '8px 10px', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>AST Features Vectorized</span>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#38bdf8' }}>47 Features</div>
              </div>
            </div>

            {findings.some((f) => f.ml_prediction) ? (
              <div>
                <h5 style={{ fontSize: '0.8rem', color: '#ffffff', marginBottom: '6px' }}>Active Predictions:</h5>
                {findings
                  .filter((f) => f.ml_prediction)
                  .map((f) => (
                    <div
                      key={f.id}
                      style={{
                        backgroundColor: 'var(--bg-input)',
                        padding: '8px 10px',
                        borderRadius: '4px',
                        marginBottom: '6px',
                        fontSize: '0.75rem',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#ffffff' }}>
                        <span>Line {f.location.line}: {f.ml_prediction?.predicted_error_type}</span>
                        <span style={{ color: 'var(--accent-purple-light)', fontWeight: 600 }}>
                          {((f.ml_prediction?.confidence || 0) * 100).toFixed(1)}% Confidence
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Run analysis to view model predictions and active feature contributions.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Execution Flow (Beta) */}
      {activeTab === 'flow' && (
        <div style={{ padding: '16px', overflowY: 'auto' }}>
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '14px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <GitCommit size={18} color="#38bdf8" />
              <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#ffffff' }}>
                Two-Pass AST Semantic Execution Trace
              </h4>
            </div>

            <ol style={{ paddingLeft: '20px', fontSize: '0.775rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              <li>
                <strong style={{ color: '#ffffff' }}>Pass 1 (Declaration Discovery):</strong> Traverses function signatures, parameter annotations, and return type declarations into the hierarchical SymbolTable.
              </li>
              <li>
                <strong style={{ color: '#ffffff' }}>Pass 2 (Expression Evaluation):</strong> Type inference engine statically checks binary operations, function calls, and annotated assignments against scoped symbols.
              </li>
              <li>
                <strong style={{ color: '#ffffff' }}>ML Corroboration:</strong> Featurizer vectorizes 47 AST indicators, producing hybrid provenance when confirmed by rule heuristics.
              </li>
            </ol>
          </div>
        </div>
      )}
    </div>
  )
}
