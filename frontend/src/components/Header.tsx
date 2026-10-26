import React from 'react'
import { Code2, ExternalLink, RefreshCw, Cpu, Activity } from 'lucide-react'
import type { ServerStatus } from '../hooks/useServerStatus'
import { API_BASE_URL } from '../services/api'

interface HeaderProps {
  serverStatus: ServerStatus
}

export const Header: React.FC<HeaderProps> = ({ serverStatus }) => {
  const { isOnline, health, modelInfo, isLoading, refresh } = serverStatus

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-logo" title="TypeMind AI Engine">
          <Code2 size={22} />
        </div>
        <div className="brand-titles">
          <span className="brand-name">TypeMind AI</span>
          <span className="brand-tagline">Understand Code. Detect Errors. Think Smarter.</span>
        </div>
      </div>

      <div className="header-status-group">
        {/* Backend Health Badge */}
        <div
          className="badge"
          style={{
            backgroundColor: isOnline ? 'var(--color-success-subtle)' : 'var(--color-error-subtle)',
            color: isOnline ? 'var(--color-success-light)' : 'var(--color-error-light)',
            borderColor: isOnline ? 'var(--color-success-border)' : 'var(--color-error-border)',
            gap: '6px',
            padding: '5px 10px',
          }}
          title={isOnline ? `Connected to ${API_BASE_URL}` : `Cannot connect to ${API_BASE_URL}`}
        >
          <Activity size={12} />
          <span>
            Backend: {isOnline ? `Healthy (v${health?.version || '0.1.0'})` : 'Offline'}
          </span>
          <button
            onClick={refresh}
            className="btn btn-ghost"
            style={{ padding: '0 2px', height: 'auto', minWidth: 'unset', color: 'inherit' }}
            title="Refresh status"
            aria-label="Refresh backend status"
          >
            <RefreshCw size={11} className={isLoading ? 'spinner' : ''} />
          </button>
        </div>

        {/* ML Model Status Badge */}
        <div
          className="badge"
          style={{
            backgroundColor:
              modelInfo?.status === 'loaded' ? 'var(--accent-violet-subtle)' : 'var(--bg-elevated)',
            color: modelInfo?.status === 'loaded' ? 'var(--accent-violet-light)' : 'var(--text-muted)',
            borderColor:
              modelInfo?.status === 'loaded' ? 'var(--accent-violet-border)' : 'var(--border-subtle)',
            gap: '6px',
            padding: '5px 10px',
          }}
          title={
            modelInfo?.status === 'loaded'
              ? `Architecture: ${modelInfo.model_architecture || 'RandomForestClassifier'} (${modelInfo.features_count} features)`
              : 'Machine learning model not loaded; static AST checks remain active'
          }
        >
          <Cpu size={12} />
          <span>
            {modelInfo?.status === 'loaded'
              ? `ML: ${modelInfo.model_architecture || 'PatternClassifier'}`
              : 'ML: Unavailable'}
          </span>
        </div>

        {/* API Docs Link */}
        <a
          href={`${API_BASE_URL}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary btn-sm"
          style={{ textDecoration: 'none' }}
          title="Open FastAPI interactive OpenAPI documentation"
        >
          <span>OpenAPI Docs</span>
          <ExternalLink size={12} />
        </a>
      </div>
    </header>
  )
}
