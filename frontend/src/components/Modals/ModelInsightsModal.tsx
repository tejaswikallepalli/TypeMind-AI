import React from 'react'
import { X, Cpu, CheckCircle2, AlertCircle, Database, Layers } from 'lucide-react'
import type { ModelInfoResponse } from '../../types/api'

interface ModelInsightsModalProps {
  isOpen: boolean
  onClose: () => void
  modelInfo: ModelInfoResponse | null
}

export const ModelInsightsModal: React.FC<ModelInsightsModalProps> = ({
  isOpen,
  onClose,
  modelInfo,
}) => {
  if (!isOpen) return null

  const isLoaded = modelInfo?.status === 'loaded'

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={18} color="var(--accent-purple-light)" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff' }}>
              Machine Learning Model Insights
            </h3>
          </div>
          <button className="btn-tool" onClick={onClose} aria-label="Close model insights">
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          {/* Status Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              backgroundColor: isLoaded ? 'var(--color-success-bg)' : 'var(--color-error-bg)',
              border: `1px solid ${isLoaded ? 'var(--color-success-border)' : 'var(--color-error-border)'}`,
              borderRadius: 'var(--radius-md)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {isLoaded ? (
                <CheckCircle2 size={16} color="var(--color-success-light)" />
              ) : (
                <AlertCircle size={16} color="var(--color-error-light)" />
              )}
              <span style={{ fontWeight: 600, color: '#ffffff' }}>
                Status: {isLoaded ? 'Model Loaded & Active' : 'Model Weights Unavailable'}
              </span>
            </div>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
              v{modelInfo?.model_version || '1.0.0'}
            </span>
          </div>

          {/* Model Architecture Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
            <div style={{ backgroundColor: 'var(--bg-card)', padding: '12px', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                <Layers size={14} />
                <span style={{ fontSize: '0.725rem' }}>Architecture</span>
              </div>
              <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#ffffff' }}>
                {modelInfo?.model_architecture || 'RandomForestClassifier'}
              </span>
            </div>

            <div style={{ backgroundColor: 'var(--bg-card)', padding: '12px', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                <Database size={14} />
                <span style={{ fontSize: '0.725rem' }}>AST Features Vectorized</span>
              </div>
              <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#38bdf8' }}>
                {modelInfo?.features_count || 47} Features
              </span>
            </div>
          </div>

          {/* Classification Classes */}
          {modelInfo?.classes && modelInfo.classes.length > 0 && (
            <div style={{ backgroundColor: 'var(--bg-card)', padding: '12px', borderRadius: 'var(--radius-md)' }}>
              <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
                Target Error Categories ({modelInfo.classes.length}):
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {modelInfo.classes.map((cls) => (
                  <span
                    key={cls}
                    style={{
                      fontSize: '0.725rem',
                      fontFamily: 'var(--font-mono)',
                      backgroundColor: 'var(--bg-input)',
                      color: 'var(--text-secondary)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    {cls}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Training Dataset Provenance */}
          <div style={{ backgroundColor: 'var(--bg-card)', padding: '12px', borderRadius: 'var(--radius-md)' }}>
            <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>
              Dataset Provenance & Benchmark
            </h4>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Trained on a curated synthetic dataset of 42 diverse Python code structures. Features represent AST node types, expression depths, operator contexts, and inferred operand types. Pure ML predictions are subject to strict confidence thresholding (0.60) with automatic abstention.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
