import React, { useState } from 'react'
import type { SuggestedFix } from '../../types/api'
import { Check, Copy, Wand2 } from 'lucide-react'

interface FixDiffViewerProps {
  fix: SuggestedFix
  onApplyFix?: (fix: SuggestedFix) => void
  onCopySuccess?: (message: string) => void
}

export const FixDiffViewer: React.FC<FixDiffViewerProps> = ({ fix, onApplyFix, onCopySuccess }) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation()
    const textToCopy =
      fix.replacements.length > 0
        ? fix.replacements.map((r) => r.new_text).join('\n')
        : fix.diff_preview || fix.title

    try {
      await navigator.clipboard.writeText(textToCopy)
      setCopied(true)
      onCopySuccess?.('Suggested fix copied to clipboard!')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback
    }
  }

  const handleApply = (e: React.MouseEvent) => {
    e.stopPropagation()
    onApplyFix?.(fix)
  }

  return (
    <div className="fix-box">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Wand2 size={13} color="var(--accent-cyan)" />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {fix.title}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleCopy}
            title="Copy fix code snippet to clipboard"
          >
            {copied ? <Check size={12} color="var(--color-success-light)" /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {onApplyFix && fix.replacements && fix.replacements.length > 0 && (
            <button
              className="btn btn-primary btn-sm"
              onClick={handleApply}
              title="Apply this suggested fix directly to the editor"
            >
              <span>Apply Fix</span>
            </button>
          )}
        </div>
      </div>

      <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '8px', lineHeight: 1.4 }}>
        {fix.description}
      </p>

      {/* Diff Preview */}
      {fix.diff_preview && (
        <div className="diff-preview" aria-label="Diff preview">
          {fix.diff_preview.split('\n').map((line, idx) => {
            const isDel = line.startsWith('-')
            const isAdd = line.startsWith('+')
            return (
              <div
                key={idx}
                style={{
                  color: isDel
                    ? 'var(--color-error-light)'
                    : isAdd
                    ? 'var(--color-success-light)'
                    : 'var(--text-secondary)',
                  backgroundColor: isDel
                    ? 'rgba(239, 68, 68, 0.08)'
                    : isAdd
                    ? 'rgba(16, 185, 129, 0.08)'
                    : 'transparent',
                  padding: '1px 6px',
                  borderRadius: '2px',
                }}
              >
                {line}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
