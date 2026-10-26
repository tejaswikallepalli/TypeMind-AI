import React from 'react'
import type { AnalysisSummary } from '../../types/api'
import { AlertCircle, AlertTriangle, CheckCircle, Clock, Cpu } from 'lucide-react'

interface SummaryCardsProps {
  summary: AnalysisSummary | null
  status?: 'success' | 'syntax_error' | 'partial' | 'tool_unavailable' | 'error' | null
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({ summary, status }) => {
  if (!summary) return null

  const isClean = status === 'success' && summary.total_findings === 0

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '10px',
        marginBottom: '14px',
      }}
    >
      {/* Total Findings */}
      <div
        style={{
          backgroundColor: isClean ? 'var(--color-success-subtle)' : 'var(--bg-card)',
          border: `1px solid ${isClean ? 'var(--color-success-border)' : 'var(--border-subtle)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '10px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
          Total Issues
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {isClean ? (
            <CheckCircle size={16} color="var(--color-success-light)" />
          ) : (
            <AlertCircle size={16} color="var(--accent-cyan)" />
          )}
          <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {summary.total_findings + (summary.syntax_errors_count || 0)}
          </span>
        </div>
      </div>

      {/* Errors */}
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--color-error-light)', textTransform: 'uppercase' }}>
          Errors
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <AlertCircle size={16} color="var(--color-error)" />
          <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-error-light)' }}>
            {summary.errors_count + (summary.syntax_errors_count || 0)}
          </span>
        </div>
      </div>

      {/* Warnings */}
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--color-warning-light)', textTransform: 'uppercase' }}>
          Warnings
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <AlertTriangle size={16} color="var(--color-warning)" />
          <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-warning-light)' }}>
            {summary.warnings_count}
          </span>
        </div>
      </div>

      {/* ML Predictions */}
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--accent-violet-light)', textTransform: 'uppercase' }}>
          ML Augmented
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Cpu size={16} color="var(--accent-violet)" />
          <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-violet-light)' }}>
            {summary.ml_predicted_findings}
          </span>
        </div>
      </div>

      {/* Execution Latency */}
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '10px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
          Analysis Time
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Clock size={16} color="var(--text-muted)" />
          <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
            {summary.execution_time_ms ? `${summary.execution_time_ms.toFixed(1)}ms` : '<1ms'}
          </span>
        </div>
      </div>
    </div>
  )
}
