import React from 'react'
import type { DiagnosticFinding } from '../../types/api'
import { AlertOctagon, CornerDownRight } from 'lucide-react'

interface SyntaxErrorCardProps {
  syntaxError: DiagnosticFinding
  onSelectLine?: (line: number) => void
}

export const SyntaxErrorCard: React.FC<SyntaxErrorCardProps> = ({ syntaxError, onSelectLine }) => {
  const line = syntaxError.location.line
  const col = syntaxError.location.column

  return (
    <div
      style={{
        backgroundColor: 'rgba(239, 68, 68, 0.08)',
        border: '1px solid var(--color-error-border)',
        borderLeft: '4px solid var(--color-error)',
        borderRadius: 'var(--radius-md)',
        padding: '14px 16px',
        marginBottom: '14px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertOctagon size={16} color="var(--color-error)" />
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-error-light)' }}>
            Python Syntax Error
          </span>
          <span className="badge badge-error">TM000_SYNTAX_ERROR</span>
        </div>

        <button
          className="finding-location-pill"
          onClick={() => onSelectLine?.(line)}
          title={`Jump to line ${line}, col ${col} in editor`}
        >
          <CornerDownRight size={11} />
          <span>
            Ln {line}, Col {col}
          </span>
        </button>
      </div>

      <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>
        {syntaxError.message}
      </p>

      <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
        Python AST grammar parsing halted due to this syntax error. Please correct the syntax to proceed with complete semantic type checking.
      </p>
    </div>
  )
}
