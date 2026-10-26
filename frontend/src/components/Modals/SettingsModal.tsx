import React from 'react'
import { X, Settings, RotateCcw } from 'lucide-react'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  confidenceThreshold: number
  onConfidenceChange: (val: number) => void
  enableMl: boolean
  onEnableMlChange: (val: boolean) => void
  onReset: () => void
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  confidenceThreshold,
  onConfidenceChange,
  enableMl,
  onEnableMlChange,
  onReset,
}) => {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content-card" style={{ maxWidth: '520px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Settings size={18} color="var(--accent-purple-light)" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff' }}>Analysis Settings</h3>
          </div>
          <button className="btn-tool" onClick={onClose} aria-label="Close settings">
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          {/* ML Enable Toggle */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              padding: '12px 14px',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.825rem' }}>
                Machine Learning Assistance
              </div>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                Enable Random Forest pattern classification alongside static AST rules
              </div>
            </div>

            <input
              type="checkbox"
              checked={enableMl}
              onChange={(e) => onEnableMlChange(e.target.checked)}
              style={{ width: '16px', height: '16px', cursor: 'pointer', accentColor: 'var(--accent-purple)' }}
              aria-label="Toggle machine learning assistance"
            />
          </div>

          {/* Confidence Slider */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              padding: '12px 14px',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.825rem' }}>
                  Minimum Confidence Threshold
                </div>
                <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                  Model abstains from predicting when confidence is below this cutoff
                </div>
              </div>
              <span
                style={{
                  fontSize: '0.85rem',
                  fontFamily: 'var(--font-mono)',
                  color: '#38bdf8',
                  fontWeight: 600,
                }}
              >
                {(confidenceThreshold * 100).toFixed(0)}%
              </span>
            </div>

            <input
              type="range"
              min="0.4"
              max="0.95"
              step="0.05"
              value={confidenceThreshold}
              onChange={(e) => onConfidenceChange(parseFloat(e.target.value))}
              disabled={!enableMl}
              style={{ width: '100%', cursor: enableMl ? 'pointer' : 'not-allowed', accentColor: 'var(--accent-purple)' }}
              aria-label="Confidence threshold slider"
            />
          </div>

          {/* Static Python Version Target */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              padding: '12px 14px',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.825rem' }}>
                Python Grammar Target
              </div>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                Supported AST grammar and type annotation syntax
              </div>
            </div>
            <span
              style={{
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                backgroundColor: 'var(--bg-input)',
                padding: '2px 8px',
                borderRadius: '4px',
                color: '#34d399',
              }}
            >
              Python 3.12+
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '6px' }}>
            <button className="btn btn-secondary btn-sm" onClick={onReset}>
              <RotateCcw size={12} />
              <span>Reset Defaults</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
