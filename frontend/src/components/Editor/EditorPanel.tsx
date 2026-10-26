import React, { useRef, useState } from 'react'
import {
  Code,
  Upload,
  ChevronDown,
  Trash2,
  AlignLeft,
  Play,
  FolderCode,
  AlertCircle,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  Info,
} from 'lucide-react'
import { CodeEditor } from './CodeEditor'
import type { DiagnosticFinding, LanguageInfo } from '../../types/api'
import type { CodeSample } from '../../types/editor'

interface EditorPanelProps {
  code: string
  onChange: (code: string) => void
  onAnalyze: () => void
  isAnalyzing: boolean
  findings: DiagnosticFinding[]
  syntaxError?: DiagnosticFinding | null
  selectedLine?: number | null
  onClear: () => void
  onFileUpload: (file: File) => void
  onSelectSample: (sampleId: string) => void
  activeSampleId?: string | null
  language: string
  onLanguageChange: (lang: string) => void
  languages: LanguageInfo[]
  samples: CodeSample[]
  languageWarning?: string | null
}

export const EditorPanel: React.FC<EditorPanelProps> = ({
  code,
  onChange,
  onAnalyze,
  isAnalyzing,
  findings,
  syntaxError,
  selectedLine,
  onClear,
  onFileUpload,
  onSelectSample,
  activeSampleId,
  language,
  onLanguageChange,
  languages,
  samples,
  languageWarning,
}) => {
  const [activeTab, setActiveTab] = useState<'editor' | 'upload'>('editor')
  const [isSamplesOpen, setIsSamplesOpen] = useState<boolean>(true)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const currentLangInfo = languages.find((l) => l.id === language) || languages[0]

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onFileUpload(file)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  // Format code utility: Standardizes 4-space indentation and strips trailing whitespaces
  const handleFormatCode = () => {
    const formatted = code
      .split('\n')
      .map((line) => line.replace(/\t/g, '    ').trimEnd())
      .join('\n')
    onChange(formatted)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Optional Warning Banner on File Upload or Extension Conflict */}
      {languageWarning && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 14px',
            marginBottom: 10,
            background: 'rgba(234, 179, 8, 0.1)',
            border: '1px solid rgba(234, 179, 8, 0.3)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.78rem',
            color: '#fbbf24',
          }}
        >
          <Info size={14} />
          <span>{languageWarning}</span>
        </div>
      )}

      {/* Primary Editor Card */}
      <div className="panel-card">
        {/* Header Tabs */}
        <div className="panel-header-tabs">
          <div className="tab-btn-group">
            <button
              className={`tab-btn ${activeTab === 'editor' ? 'active' : ''}`}
              onClick={() => setActiveTab('editor')}
            >
              <Code size={14} />
              <span>Code Editor</span>
            </button>

            <button
              className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('upload')
                fileInputRef.current?.click()
              }}
            >
              <Upload size={14} />
              <span>Upload File</span>
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept=".py,.java,.js,.jsx,.ts,.tsx,.c,.h,.cpp,.cc,.cxx,.hpp,.cs,.go,.rs,.php,.rb,text/plain"
              style={{ display: 'none' }}
              onChange={handleFileChange}
              aria-label="Upload source code"
            />
          </div>

          {/* Multi-Language Dropdown Selector with Live Support Status Indicator */}
          <div
            className="lang-selector-pill"
            title={`Active: ${currentLangInfo?.name || 'Python'} — ${currentLangInfo?.tool_name || ''} (${currentLangInfo?.support_level || 'supported'})`}
          >
            <span
              className={`lang-status-dot ${currentLangInfo?.support_level || 'supported'}`}
            />
            <select
              className="lang-select-dropdown"
              value={language}
              onChange={(e) => onLanguageChange(e.target.value)}
              aria-label="Select Programming Language"
            >
              {languages.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name} {l.support_level === 'supported' ? '● Available' : l.support_level === 'partial' ? '◐ Partial' : '○ Tool Missing'}
                </option>
              ))}
            </select>
            <ChevronDown size={12} color="var(--text-muted)" style={{ pointerEvents: 'none' }} />
          </div>
        </div>

        {/* Editor Body */}
        <CodeEditor
          code={code}
          onChange={onChange}
          onAnalyze={onAnalyze}
          findings={findings}
          syntaxError={syntaxError}
          selectedLine={selectedLine}
        />

        {/* Editor Bottom Actions */}
        <div className="editor-action-footer">
          <div className="editor-left-tools">
            <button
              className="btn-tool"
              onClick={onClear}
              title="Clear current code from editor"
              disabled={code.trim().length === 0}
            >
              <Trash2 size={13} />
              <span>Clear</span>
            </button>

            <button
              className="btn-tool"
              onClick={handleFormatCode}
              title="Format indentation (4 spaces) and clean whitespace"
              disabled={code.trim().length === 0}
            >
              <AlignLeft size={13} />
              <span>Format</span>
            </button>
          </div>

          <button
            className="btn-analyze-glow"
            onClick={onAnalyze}
            disabled={isAnalyzing || code.trim().length === 0}
            title={`Analyze ${currentLangInfo?.name || 'Python'} Code (Ctrl+Enter)`}
          >
            {isAnalyzing ? (
              <>
                <div className="spinner" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Play size={14} fill="currentColor" />
                <span>Analyze Code</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Sample Programs Collapsible Row */}
      <div className="samples-bar-card">
        <div className="samples-bar-header" onClick={() => setIsSamplesOpen(!isSamplesOpen)}>
          <div className="samples-bar-title">
            <FolderCode size={14} color="var(--accent-purple-light)" />
            <span>Sample Programs ({currentLangInfo?.name || 'Python'})</span>
          </div>
          <ChevronDown
            size={14}
            color="var(--text-muted)"
            style={{
              transform: isSamplesOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s',
            }}
          />
        </div>

        {isSamplesOpen && (
          <div className="samples-buttons-grid">
            {samples.map((sample) => {
              const isClean = sample.name.toLowerCase().includes('valid') || sample.name.toLowerCase().includes('clean')
              const isMismatch = sample.name.toLowerCase().includes('mismatch') || sample.name.toLowerCase().includes('incompatible')
              const isArg = sample.name.toLowerCase().includes('argument')
              
              let IconComponent = AlertCircle
              let iconColor = '#f87171'
              if (isClean) {
                IconComponent = CheckCircle2
                iconColor = '#94a3b8'
              } else if (isArg) {
                IconComponent = FileCode
                iconColor = '#60a5fa'
              } else if (!isMismatch) {
                IconComponent = AlertTriangle
                iconColor = '#fbbf24'
              }

              return (
                <button
                  key={sample.id}
                  className={`btn-sample-pill ${activeSampleId === sample.id ? 'active' : ''}`}
                  onClick={() => onSelectSample(sample.id)}
                  title={sample.description}
                >
                  <IconComponent size={14} color={iconColor} />
                  <span>{sample.name}</span>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
