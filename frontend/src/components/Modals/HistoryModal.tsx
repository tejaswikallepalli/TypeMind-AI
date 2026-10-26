import React from 'react'
import { X, Clock, ArrowRight, Trash2 } from 'lucide-react'

export interface HistoryItem {
  id: string
  timestamp: string
  code: string
  fileName: string
  totalFindings: number
  errorsCount: number
}

interface HistoryModalProps {
  isOpen: boolean
  onClose: () => void
  history: HistoryItem[]
  onLoadHistoryItem: (code: string, fileName: string) => void
  onClearHistory: () => void
}

export const HistoryModal: React.FC<HistoryModalProps> = ({
  isOpen,
  onClose,
  history,
  onLoadHistoryItem,
  onClearHistory,
}) => {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={18} color="var(--accent-purple-light)" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff' }}>Analysis History</h3>
          </div>
          <button className="btn-tool" onClick={onClose} aria-label="Close history modal">
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          {history.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '36px 16px', color: 'var(--text-muted)' }}>
              No previous analyses recorded yet. Run code analysis to track your history.
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={onClearHistory}
                  style={{ color: 'var(--color-error-light)' }}
                >
                  <Trash2 size={12} />
                  <span>Clear History</span>
                </button>
              </div>

              {history.map((item) => (
                <div
                  key={item.id}
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.85rem' }}>
                        {item.fileName}
                      </span>
                      <span
                        style={{
                          fontSize: '0.7rem',
                          padding: '1px 6px',
                          borderRadius: '10px',
                          backgroundColor:
                            item.errorsCount > 0 ? 'var(--color-error-bg)' : 'var(--color-success-bg)',
                          color:
                            item.errorsCount > 0 ? 'var(--color-error-light)' : 'var(--color-success-light)',
                        }}
                      >
                        {item.totalFindings} {item.totalFindings === 1 ? 'issue' : 'issues'}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                      {item.timestamp} • {item.code.split('\n').length} lines
                    </span>
                  </div>

                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      onLoadHistoryItem(item.code, item.fileName)
                      onClose()
                    }}
                  >
                    <span>Load</span>
                    <ArrowRight size={12} />
                  </button>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
