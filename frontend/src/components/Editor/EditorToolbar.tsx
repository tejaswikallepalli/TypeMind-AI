import React, { useRef } from 'react'
import { Play, Upload, Clipboard, Trash2, FileCode } from 'lucide-react'
import { CODE_SAMPLES } from '../../services/samples'

interface EditorToolbarProps {
  onAnalyze: () => void
  isAnalyzing: boolean
  onLoadSample: (code: string, name: string) => void
  onFileUpload: (file: File) => void
  onPasteClipboard: () => void
  onClear: () => void
  hasContent: boolean
}

export const EditorToolbar: React.FC<EditorToolbarProps> = ({
  onAnalyze,
  isAnalyzing,
  onLoadSample,
  onFileUpload,
  onPasteClipboard,
  onClear,
  hasContent,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onFileUpload(file)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleSampleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedId = e.target.value
    if (!selectedId) return
    const sample = CODE_SAMPLES.find((s) => s.id === selectedId)
    if (sample) {
      onLoadSample(sample.code, sample.name)
    }
    e.target.value = ''
  }

  return (
    <div className="pane-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <div className="pane-title">
          <FileCode size={16} color="var(--accent-cyan)" />
          <span>Python Source Workspace</span>
        </div>

        {/* Preset Samples Selector */}
        <select
          className="select-input"
          onChange={handleSampleChange}
          defaultValue=""
          aria-label="Load code sample"
        >
          <option value="" disabled>
            📂 Load Sample Scenario...
          </option>
          {CODE_SAMPLES.map((sample) => (
            <option key={sample.id} value={sample.id}>
              {sample.name}
            </option>
          ))}
        </select>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".py,text/x-python,text/plain"
          style={{ display: 'none' }}
          onChange={handleFileChange}
          aria-label="Upload Python file"
        />

        {/* Upload File Button */}
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => fileInputRef.current?.click()}
          title="Upload Python source file (.py, max 500 KB)"
        >
          <Upload size={13} />
          <span>Upload .py</span>
        </button>

        {/* Paste from Clipboard Button */}
        <button
          className="btn btn-secondary btn-sm"
          onClick={onPasteClipboard}
          title="Paste code from clipboard"
        >
          <Clipboard size={13} />
          <span>Paste</span>
        </button>

        {/* Clear Button */}
        <button
          className="btn btn-ghost btn-sm"
          onClick={onClear}
          disabled={!hasContent}
          title="Clear editor"
          aria-label="Clear code editor"
        >
          <Trash2 size={13} />
          <span>Clear</span>
        </button>

        {/* Primary Analyze Button */}
        <button
          className="btn btn-primary"
          onClick={onAnalyze}
          disabled={isAnalyzing || !hasContent}
          title="Run AST Semantic and Machine Learning Analysis (Ctrl+Enter)"
          style={{ minWidth: '130px' }}
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
  )
}
