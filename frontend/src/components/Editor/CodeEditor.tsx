import React, { useRef, useEffect, useState, useMemo } from 'react'
import type { DiagnosticFinding } from '../../types/api'

interface CodeEditorProps {
  code: string
  onChange: (newCode: string) => void
  onAnalyze: () => void
  findings: DiagnosticFinding[]
  syntaxError?: DiagnosticFinding | null
  selectedLine?: number | null
  onCursorChange?: (line: number, column: number) => void
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  code,
  onChange,
  onAnalyze,
  findings,
  syntaxError,
  selectedLine,
  onCursorChange,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const gutterRef = useRef<HTMLDivElement>(null)
  const [activeLine, setActiveLine] = useState<number>(1)

  // Map findings and syntax errors to line numbers for gutter indicators
  const lineSeverityMap = useMemo(() => {
    const map = new Map<number, 'error' | 'warning' | 'syntax'>()

    if (syntaxError) {
      map.set(syntaxError.location.line, 'syntax')
    }

    for (const f of findings) {
      const line = f.location.line
      const current = map.get(line)
      if (current === 'syntax' || current === 'error') continue
      if (f.severity === 'error') {
        map.set(line, 'error')
      } else if (f.severity === 'warning') {
        map.set(line, 'warning')
      }
    }
    return map
  }, [findings, syntaxError])

  const lines = useMemo(() => {
    const split = code.split('\n')
    return split.length > 0 ? split : ['']
  }, [code])

  // Synchronize gutter scrolling with textarea scrolling
  const handleScroll = (e: React.UIEvent<HTMLTextAreaElement>) => {
    if (gutterRef.current) {
      gutterRef.current.scrollTop = e.currentTarget.scrollTop
    }
  }

  // Update cursor position and active line on selection change or keyup
  const updateCursorPosition = () => {
    if (!textareaRef.current) return
    const selStart = textareaRef.current.selectionStart
    const textBefore = code.substring(0, selStart)
    const linesBefore = textBefore.split('\n')
    const currentLine = linesBefore.length
    const currentColumn = linesBefore[linesBefore.length - 1].length + 1

    setActiveLine(currentLine)
    onCursorChange?.(currentLine, currentColumn)
  }

  // Scroll to selected line when user clicks a finding in the findings panel
  useEffect(() => {
    if (selectedLine && selectedLine > 0 && textareaRef.current) {
      const targetLine = Math.min(selectedLine, lines.length)
      const lineHeightPx = 22.4 // approx 0.85rem * 1.6
      const scrollTarget = Math.max(0, (targetLine - 5) * lineHeightPx)

      if (typeof textareaRef.current.scrollTo === 'function') {
        textareaRef.current.scrollTo({
          top: scrollTarget,
          behavior: 'smooth',
        })
      } else {
        textareaRef.current.scrollTop = scrollTarget
      }

      // Calculate character index to position cursor at target line
      let charIdx = 0
      for (let i = 0; i < targetLine - 1; i++) {
        charIdx += lines[i].length + 1
      }
      textareaRef.current.setSelectionRange(charIdx, charIdx)
      textareaRef.current.focus()
      setActiveLine(targetLine)
    }
  }, [selectedLine, lines])

  // Handle Tab key for 4-space indentation and Ctrl+Enter for analysis
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Shortcut: Ctrl+Enter or Cmd+Enter to analyze
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      onAnalyze()
      return
    }

    // Tab key handling: Insert 4 spaces
    if (e.key === 'Tab') {
      e.preventDefault()
      const textarea = textareaRef.current
      if (!textarea) return

      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const updatedCode = code.substring(0, start) + '    ' + code.substring(end)

      onChange(updatedCode)

      // Move cursor forward 4 spaces
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 4
          updateCursorPosition()
        }
      }, 0)
    }
  }

  return (
    <div className="editor-wrapper">
      {/* Left Gutter: Line Numbers & Finding Badges */}
      <div
        ref={gutterRef}
        className="line-numbers-gutter"
        aria-hidden="true"
      >
        {lines.map((_, idx) => {
          const lineNum = idx + 1
          const severity = lineSeverityMap.get(lineNum)
          const isSelected = selectedLine === lineNum
          const isActive = activeLine === lineNum

          let severityClass = ''
          if (severity === 'syntax' || severity === 'error') {
            severityClass = 'has-error'
          } else if (severity === 'warning') {
            severityClass = 'has-warning'
          }

          return (
            <div
              key={lineNum}
              className={`line-number-cell ${severityClass} ${isSelected || isActive ? 'is-active-line' : ''}`}
              title={severity ? `Line ${lineNum}: Has ${severity}` : `Line ${lineNum}`}
              onClick={() => {
                if (textareaRef.current) {
                  let charIdx = 0
                  for (let i = 0; i < lineNum - 1; i++) {
                    charIdx += lines[i].length + 1
                  }
                  textareaRef.current.setSelectionRange(charIdx, charIdx)
                  textareaRef.current.focus()
                  setActiveLine(lineNum)
                }
              }}
            >
              {severity && (
                <span
                  style={{
                    display: 'inline-block',
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor:
                      severity === 'warning' ? 'var(--color-warning)' : 'var(--color-error)',
                  }}
                />
              )}
              <span>{lineNum}</span>
            </div>
          )
        })}
      </div>

      {/* Code Area */}
      <div className="editor-textarea-container">
        <textarea
          ref={textareaRef}
          className="code-textarea"
          value={code}
          onChange={(e) => {
            onChange(e.target.value)
            updateCursorPosition()
          }}
          onKeyDown={handleKeyDown}
          onKeyUp={updateCursorPosition}
          onClick={updateCursorPosition}
          onScroll={handleScroll}
          spellCheck={false}
          autoCapitalize="off"
          autoComplete="off"
          autoCorrect="off"
          aria-label="Python source code editor"
          placeholder="# Write or paste Python code here...&#10;def greet(name: str) -> str:&#10;    return name + 42"
        />
      </div>
    </div>
  )
}
