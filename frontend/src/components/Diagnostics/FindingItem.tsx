import React, { useState } from 'react'
import type { DiagnosticFinding, SuggestedFix } from '../../types/api'
import { Badge } from '../Common/Badge'
import { FixDiffViewer } from './FixDiffViewer'
import { ChevronDown, ChevronRight, CornerDownRight, Cpu, ArrowRight } from 'lucide-react'

interface FindingItemProps {
  finding: DiagnosticFinding
  isSelected: boolean
  onSelect: () => void
  onApplyFix?: (fix: SuggestedFix) => void
  onCopySuccess?: (msg: string) => void
}

export const FindingItem: React.FC<FindingItemProps> = ({
  finding,
  isSelected,
  onSelect,
  onApplyFix,
  onCopySuccess,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true)

  const line = finding.location.line
  const col = finding.location.column

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsExpanded((prev) => !prev)
  }

  return (
    <div
      className={`finding-card severity-${finding.severity} ${isSelected ? 'is-selected' : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onSelect()
        }
      }}
      aria-label={`Diagnostic finding at line ${line}, column ${col}: ${finding.message}`}
    >
      <div className="finding-header">
        <div className="finding-badges">
          <Badge type="severity" severity={finding.severity} />
          <Badge type="origin" origin={finding.origin} />
          <Badge type="confirmed" isConfirmed={finding.is_confirmed} />
          {finding.rule_id && (
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.725rem',
                color: 'var(--text-muted)',
                backgroundColor: 'var(--bg-input)',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              {finding.rule_id}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="finding-location-pill"
            onClick={(e) => {
              e.stopPropagation()
              onSelect()
            }}
            title={`Scroll to line ${line}, column ${col} in editor`}
          >
            <CornerDownRight size={11} />
            <span>
              Ln {line}, Col {col}
            </span>
          </button>

          <button
            onClick={toggleExpand}
            className="btn btn-ghost"
            style={{ padding: '2px', height: 'auto', minWidth: 'unset', color: 'var(--text-secondary)' }}
            aria-label={isExpanded ? 'Collapse finding details' : 'Expand finding details'}
          >
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        </div>
      </div>

      <div className="finding-message">{finding.message}</div>

      {isExpanded && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {/* Expected vs Observed Type Box */}
          {(finding.expected_type || finding.observed_type) && (
            <div className="type-comparison-box">
              {finding.expected_type && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.725rem' }}>Expected:</span>
                  <span className="type-pill-expected">{finding.expected_type.raw_type}</span>
                </div>
              )}

              {finding.expected_type && finding.observed_type && (
                <ArrowRight size={12} color="var(--text-faint)" />
              )}

              {finding.observed_type && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.725rem' }}>Observed:</span>
                  <span className="type-pill-observed">{finding.observed_type.raw_type}</span>
                </div>
              )}
            </div>
          )}

          {/* Contextual Plain-Language Explanation */}
          {finding.explanation && (
            <div className="finding-explanation">
              <strong style={{ color: 'var(--accent-cyan-light)', display: 'block', marginBottom: '2px', fontSize: '0.75rem' }}>
                Explanation:
              </strong>
              {finding.explanation}
            </div>
          )}

          {/* Machine Learning Prediction Insights */}
          {finding.ml_prediction && (
            <div
              style={{
                backgroundColor: 'var(--bg-input)',
                border: '1px solid var(--accent-violet-border)',
                borderRadius: 'var(--radius-sm)',
                padding: '8px 12px',
                marginTop: '6px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Cpu size={13} color="var(--accent-violet-light)" />
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-violet-light)' }}>
                    ML Inference: {finding.ml_prediction.model_name}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--accent-violet-light)',
                    fontWeight: 600,
                  }}
                >
                  {(finding.ml_prediction.confidence * 100).toFixed(1)}% Confidence
                </span>
              </div>

              {/* Confidence Progress Bar */}
              <div
                style={{
                  height: '4px',
                  backgroundColor: 'rgba(255, 255, 255, 0.08)',
                  borderRadius: '2px',
                  overflow: 'hidden',
                  marginBottom: '6px',
                }}
              >
                <div
                  style={{
                    width: `${Math.round(finding.ml_prediction.confidence * 100)}%`,
                    height: '100%',
                    backgroundColor: 'var(--accent-violet)',
                  }}
                />
              </div>

              {finding.ml_prediction.features_used && finding.ml_prediction.features_used.length > 0 && (
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '4px' }}>
                  {finding.ml_prediction.features_used.slice(0, 4).map((feat, i) => (
                    <span
                      key={i}
                      style={{
                        fontSize: '0.675rem',
                        fontFamily: 'var(--font-mono)',
                        backgroundColor: 'var(--bg-card)',
                        color: 'var(--text-muted)',
                        padding: '1px 5px',
                        borderRadius: '3px',
                      }}
                    >
                      {feat}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Suggested Fixes */}
          {finding.suggested_fixes && finding.suggested_fixes.length > 0 && (
            <div style={{ marginTop: '4px' }}>
              {finding.suggested_fixes.map((fix) => (
                <FixDiffViewer
                  key={fix.id}
                  fix={fix}
                  onApplyFix={onApplyFix}
                  onCopySuccess={onCopySuccess}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
