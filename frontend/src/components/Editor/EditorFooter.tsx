import React from 'react'

interface EditorFooterProps {
  lineCount: number
  characterCount: number
  cursorLine: number
  cursorColumn: number
  fileName?: string | null
}

const MAX_BYTES = 500_000

export const EditorFooter: React.FC<EditorFooterProps> = ({
  lineCount,
  characterCount,
  cursorLine,
  cursorColumn,
  fileName,
}) => {
  // Approximate UTF-8 byte size
  const approximateBytes = new Blob([new Array(characterCount).fill('a').join('')]).size
  const percentage = Math.min(100, (approximateBytes / MAX_BYTES) * 100)
  const isNearLimit = percentage > 85

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    return `${(bytes / 1024).toFixed(1)} KB`
  }

  return (
    <footer className="editor-status-bar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <span>
          Ln {cursorLine}, Col {cursorColumn}
        </span>
        <span style={{ color: 'var(--border-medium)' }}>|</span>
        <span>
          {lineCount} {lineCount === 1 ? 'line' : 'lines'}, {characterCount} chars
        </span>
        {fileName && (
          <>
            <span style={{ color: 'var(--border-medium)' }}>|</span>
            <span style={{ color: 'var(--accent-cyan-light)' }}>{fileName}</span>
          </>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <span
          style={{
            color: isNearLimit ? 'var(--color-warning-light)' : 'var(--text-muted)',
          }}
          title="Source code payload size limit: 500 KB"
        >
          {formatBytes(approximateBytes)} / 500 KB ({percentage.toFixed(1)}%)
        </span>
        <span style={{ color: 'var(--border-medium)' }}>|</span>
        <span style={{ color: 'var(--text-secondary)' }}>Python 3.12+ (AST Grammar)</span>
        <span style={{ color: 'var(--border-medium)' }}>|</span>
        <span style={{ color: 'var(--text-muted)' }}>UTF-8</span>
      </div>
    </footer>
  )
}
