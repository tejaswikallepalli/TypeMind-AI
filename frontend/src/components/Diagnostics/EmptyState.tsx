import React from 'react'
import { CheckCircle2, Code2, WifiOff, RefreshCw } from 'lucide-react'

interface EmptyStateProps {
  type: 'initial' | 'clean' | 'network_error' | 'filtered_empty'
  errorMessage?: string | null
  onRetry?: () => void
}

export const EmptyState: React.FC<EmptyStateProps> = ({ type, errorMessage, onRetry }) => {
  if (type === 'clean') {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '48px 24px',
          textAlign: 'center',
          gap: '12px',
        }}
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: 'var(--color-success-subtle)',
            border: '1px solid var(--color-success-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-success-light)',
          }}
        >
          <CheckCircle2 size={26} />
        </div>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          Clean Code! No Type Errors Found
        </h3>
        <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', maxWidth: '380px', lineHeight: 1.5 }}>
          The semantic analyzer parsed the AST and confirmed that all annotated functions, operations, and variables conform to static type rules.
        </p>
      </div>
    )
  }

  if (type === 'network_error') {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '48px 24px',
          textAlign: 'center',
          gap: '12px',
        }}
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: 'var(--color-error-subtle)',
            border: '1px solid var(--color-error-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-error-light)',
          }}
        >
          <WifiOff size={24} />
        </div>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--color-error-light)' }}>
          Analysis Request Failed
        </h3>
        <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', maxWidth: '420px', lineHeight: 1.5 }}>
          {errorMessage || 'Unable to connect to the TypeMind AI backend. Verify that the FastAPI server is running.'}
        </p>
        {onRetry && (
          <button className="btn btn-secondary btn-sm" onClick={onRetry} style={{ marginTop: '4px' }}>
            <RefreshCw size={12} />
            <span>Retry Analysis</span>
          </button>
        )}
      </div>
    )
  }

  if (type === 'filtered_empty') {
    return (
      <div style={{ padding: '36px 16px', textAlign: 'center', color: 'var(--text-muted)' }}>
        No findings match the selected filter.
      </div>
    )
  }

  // Initial state
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '56px 24px',
        textAlign: 'center',
        gap: '12px',
        color: 'var(--text-muted)',
      }}
    >
      <div
        style={{
          width: '48px',
          height: '48px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--bg-input)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--accent-cyan)',
        }}
      >
        <Code2 size={24} />
      </div>
      <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
        Ready for Semantic Analysis
      </h3>
      <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', maxWidth: '340px', lineHeight: 1.5 }}>
        Click <strong>Analyze Code</strong> or press <code>Ctrl+Enter</code> to run deterministic AST type checks and machine-learning anomaly detection.
      </p>
    </div>
  )
}
