import { useState, useEffect, useCallback } from 'react'
import { analyzeCode, ApiClientError } from '../services/api'
import type { AnalysisResponse, DiagnosticFinding, SuggestedFix } from '../types/api'
import { CODE_SAMPLES } from '../services/samples'

const STORAGE_KEY = 'typemind_code_draft'
const DEFAULT_CODE = CODE_SAMPLES[1].code // Type mismatch sample by default

export function useAnalysis() {
  const [sourceCode, setSourceCode] = useState<string>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved !== null ? saved : DEFAULT_CODE
    } catch {
      return DEFAULT_CODE
    }
  })

  const [fileName, setFileName] = useState<string | null>('demo_error.py')
  const [language, setLanguage] = useState<string>('python')
  const [languageWarning, setLanguageWarning] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false)
  const [response, setResponse] = useState<AnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null)
  const [selectedLine, setSelectedLine] = useState<number | null>(null)
  const [isDirty, setIsDirty] = useState<boolean>(false)

  // Persist code draft to localStorage
  const updateCode = useCallback((newCode: string) => {
    setSourceCode(newCode)
    setIsDirty(true)
    try {
      localStorage.setItem(STORAGE_KEY, newCode)
    } catch {
      // storage unavailable
    }
  }, [])

  // Warn user on page unload if they have unsaved work
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty && sourceCode.trim().length > 0) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [isDirty, sourceCode])

  // Run analysis against FastAPI backend
  const runAnalysis = useCallback(async () => {
    if (!sourceCode || sourceCode.trim().length === 0) {
      setError(`Please enter or paste ${language.toUpperCase()} code before analyzing.`)
      setResponse(null)
      return
    }

    setIsAnalyzing(true)
    setError(null)
    setSelectedFindingId(null)
    setSelectedLine(null)

    try {
      const result = await analyzeCode({
        source_code: sourceCode,
        file_path: fileName || `snippet.${language === 'python' ? 'py' : language}`,
        language: language,
        enable_ml_analysis: language === 'python',
        min_confidence: 0.60,
      })

      setResponse(result)

      // Auto-select first finding if available
      if (result.syntax_error) {
        setSelectedLine(result.syntax_error.location.line)
      } else if (result.findings.length > 0) {
        setSelectedFindingId(result.findings[0].id)
        setSelectedLine(result.findings[0].location.line)
      }
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : 'An unexpected error occurred during analysis.')
      }
      setResponse(null)
    } finally {
      setIsAnalyzing(false)
    }
  }, [sourceCode, fileName, language])

  // Apply suggested fix directly into editor code
  const applyFix = useCallback(
    (fix: SuggestedFix) => {
      if (!fix.replacements || fix.replacements.length === 0) return

      let updated = sourceCode
      const lines = updated.split('\n')

      for (const replacement of fix.replacements) {
        const lineIdx = replacement.location.line - 1
        if (lineIdx >= 0 && lineIdx < lines.length) {
          const targetLine = lines[lineIdx]
          const startCol = Math.max(0, replacement.location.column - 1)
          const endCol =
            replacement.location.end_column !== null && replacement.location.end_column !== undefined
              ? replacement.location.end_column
              : targetLine.length

          const newLine =
            targetLine.substring(0, startCol) + replacement.new_text + targetLine.substring(endCol)
          lines[lineIdx] = newLine
        }
      }

      updated = lines.join('\n')
      updateCode(updated)

      // Automatically re-run analysis to verify the fix resolved the error
      setTimeout(() => {
        analyzeCode({
          source_code: updated,
          file_path: fileName || 'snippet.py',
          language: language,
          enable_ml_analysis: language === 'python',
          min_confidence: 0.60,
        })
          .then((newRes) => {
            setResponse(newRes)
            setSelectedFindingId(null)
          })
          .catch(() => {})
      }, 50)
    },
    [sourceCode, fileName, language, updateCode]
  )

  // Select a specific finding
  const selectFinding = useCallback((finding: DiagnosticFinding) => {
    setSelectedFindingId(finding.id)
    setSelectedLine(finding.location.line)
  }, [])

  // Jump to line directly
  const selectLine = useCallback((line: number) => {
    setSelectedLine(line)
  }, [])

  // Load a preset code sample
  const loadSample = useCallback(
    (code: string, name: string, sampleLang?: string) => {
      updateCode(code)
      if (sampleLang) {
        setLanguage(sampleLang)
      }
      const ext = sampleLang === 'typescript' ? 'ts' : sampleLang === 'javascript' ? 'js' : sampleLang === 'java' ? 'java' : sampleLang === 'cpp' ? 'cpp' : sampleLang === 'c' ? 'c' : sampleLang === 'go' ? 'go' : sampleLang === 'rust' ? 'rs' : 'py'
      setFileName(`${name.toLowerCase().replace(/[^a-z0-9]/g, '_')}.${ext}`)
      setResponse(null)
      setError(null)
      setLanguageWarning(null)
      setSelectedFindingId(null)
      setSelectedLine(null)
    },
    [updateCode]
  )

  // Clear editor content
  const clearCode = useCallback(() => {
    if (sourceCode.trim().length > 0) {
      if (window.confirm('Clear all code from the editor?')) {
        updateCode('')
        setFileName(null)
        setResponse(null)
        setError(null)
        setLanguageWarning(null)
        setSelectedFindingId(null)
        setSelectedLine(null)
      }
    }
  }, [sourceCode, updateCode])

  // Handle uploaded source file across any supported language
  const handleFileUpload = useCallback(
    (file: File, detectedLang?: string | null) => {
      // 1. Client-side size limit validation (500 KB)
      if (file.size > 500_000) {
        setError(`File size (${(file.size / 1024).toFixed(1)} KB) exceeds the 500 KB limit.`)
        return
      }

      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result
        if (typeof content === 'string') {
          updateCode(content)
          setFileName(file.name)
          setResponse(null)
          setError(null)

          if (detectedLang) {
            setLanguage(detectedLang)
            setLanguageWarning(null)
          } else {
            setLanguageWarning(
              `Uploaded file "${file.name}" extension was not recognized. Analyzed as ${language.toUpperCase()}.`
            )
          }
        }
      }
      reader.onerror = () => {
        setError('Failed to read the selected file.')
      }
      reader.readAsText(file)
    },
    [language, updateCode]
  )

  return {
    sourceCode,
    setSourceCode: updateCode,
    fileName,
    language,
    setLanguage,
    languageWarning,
    isAnalyzing,
    response,
    error,
    selectedFindingId,
    selectedLine,
    runAnalysis,
    applyFix,
    selectFinding,
    selectLine,
    loadSample,
    clearCode,
    handleFileUpload,
  }
}
