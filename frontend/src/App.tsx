import React, { useState, useEffect } from 'react'
import { TopNavbar } from './components/Navigation/TopNavbar'
import { Sidebar } from './components/Navigation/Sidebar'
import { HeroBanner } from './components/Banner/HeroBanner'
import { EditorPanel } from './components/Editor/EditorPanel'
import { ResultsPanel } from './components/Diagnostics/ResultsPanel'
import { HistoryModal, type HistoryItem } from './components/Modals/HistoryModal'
import { ModelInsightsModal } from './components/Modals/ModelInsightsModal'
import { DocumentationModal } from './components/Modals/DocumentationModal'
import { SettingsModal } from './components/Modals/SettingsModal'
import { Toast } from './components/Common/Toast'
import { useAnalysis } from './hooks/useAnalysis'
import { useLanguages } from './hooks/useLanguages'
import { useServerStatus } from './hooks/useServerStatus'
import { CODE_SAMPLES, getSamplesForLanguage } from './services/samples'
import type { SuggestedFix } from './types/api'

export const App: React.FC = () => {
  const serverStatus = useServerStatus()
  const {
    languages,
    selectedLanguage,
    setSelectedLanguage,
    currentLanguageInfo,
    detectLanguageFromFile,
  } = useLanguages()

  const {
    sourceCode,
    setSourceCode,
    fileName,
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
  } = useAnalysis()

  // Navigation and Modal State
  const [activeNavTab, setActiveNavTab] = useState<'analyze' | 'history' | 'model' | 'docs'>('analyze')
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false)
  const [isModelInsightsOpen, setIsModelInsightsOpen] = useState<boolean>(false)
  const [isDocsOpen, setIsDocsOpen] = useState<boolean>(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false)

  // Settings
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.60)
  const [enableMl, setEnableMl] = useState<boolean>(true)

  // Active sample ID tracking
  const [activeSampleId, setActiveSampleId] = useState<string | null>('sample-type-mismatch')

  // History Items
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>(() => {
    try {
      const saved = localStorage.getItem('typemind_analysis_history')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

  // Toast notification
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  // Record history item when analysis response is received
  useEffect(() => {
    if (response) {
      const newItem: HistoryItem = {
        id: `hist-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        code: sourceCode,
        fileName: fileName || 'snippet.py',
        totalFindings: response.summary.total_findings + (response.syntax_error ? 1 : 0),
        errorsCount: response.summary.errors_count + (response.syntax_error ? 1 : 0),
      }
      setHistoryItems((prev) => {
        const updated = [newItem, ...prev.slice(0, 19)]
        try {
          localStorage.setItem('typemind_analysis_history', JSON.stringify(updated))
        } catch {
          // ignore
        }
        return updated
      })
    }
  }, [response, fileName, sourceCode, selectedLanguage])

  // Synchronize language selection
  const handleLanguageChange = (newLang: string) => {
    setSelectedLanguage(newLang)
    setLanguage(newLang)
    setActiveSampleId(null)
    setToastMessage(`Switched active language to ${newLang.toUpperCase()}`)
  }

  const handleNavTabChange = (tab: 'analyze' | 'history' | 'model' | 'docs') => {
    setActiveNavTab(tab)
    if (tab === 'history') setIsHistoryOpen(true)
    if (tab === 'model') setIsModelInsightsOpen(true)
    if (tab === 'docs') setIsDocsOpen(true)
  }

  const handleSelectSample = (sampleId: string) => {
    const sample = CODE_SAMPLES.find((s) => s.id === sampleId)
    if (sample) {
      setActiveSampleId(sampleId)
      const sampleLang = sample.language || 'python'
      setSelectedLanguage(sampleLang)
      setLanguage(sampleLang)
      loadSample(sample.code, sample.name, sampleLang)
      setToastMessage(`Loaded sample: ${sample.name}`)
    }
  }

  const handleApplyFix = (fix: SuggestedFix) => {
    applyFix(fix)
    setToastMessage(`Applied fix: "${fix.title}"`)
  }

  const handleNewAnalysis = () => {
    clearCode()
    setActiveSampleId(null)
    setToastMessage('Ready for new analysis')
  }

  return (
    <div className="app-shell">
      {/* 1. Top Navigation Bar */}
      <TopNavbar
        activeTab={activeNavTab}
        onTabChange={handleNavTabChange}
        serverStatus={serverStatus}
      />

      {/* 2. Body Container: Sidebar + Main Content */}
      <div className="body-container">
        {/* Left Sidebar */}
        <Sidebar
          onNewAnalysis={handleNewAnalysis}
          onOpenSamples={() => {
            const editorEl = document.querySelector('.samples-bar-card')
            editorEl?.scrollIntoView({ behavior: 'smooth' })
          }}
          onOpenHistory={() => setIsHistoryOpen(true)}
          onOpenModelInsights={() => setIsModelInsightsOpen(true)}
          onOpenSettings={() => setIsSettingsOpen(true)}
          activeView={activeNavTab}
          currentLanguageInfo={currentLanguageInfo}
        />

        {/* Main Content Workspace */}
        <main className="main-workspace">
          {/* Hero Banner */}
          <HeroBanner />

          {/* Primary Two-Panel Workspace */}
          <div className="panels-grid">
            {/* Left Panel: Multi-Language Code Editor */}
            <section aria-label="Code editor">
              <EditorPanel
                code={sourceCode}
                onChange={setSourceCode}
                onAnalyze={runAnalysis}
                isAnalyzing={isAnalyzing}
                findings={response?.findings || []}
                syntaxError={response?.syntax_error}
                selectedLine={selectedLine}
                onClear={clearCode}
                onFileUpload={(file) => {
                  const detected = detectLanguageFromFile(file.name)
                  if (detected) {
                    setSelectedLanguage(detected)
                    setLanguage(detected)
                  }
                  handleFileUpload(file, detected)
                  setToastMessage(`Loaded file: ${file.name}`)
                }}
                onSelectSample={handleSelectSample}
                activeSampleId={activeSampleId}
                language={selectedLanguage}
                onLanguageChange={handleLanguageChange}
                languages={languages}
                samples={getSamplesForLanguage(selectedLanguage)}
                languageWarning={languageWarning}
              />
            </section>

            {/* Right Panel: Analysis Results */}
            <section aria-label="Analysis results and diagnostics">
              <ResultsPanel
                response={response}
                error={error}
                isAnalyzing={isAnalyzing}
                selectedFindingId={selectedFindingId}
                onSelectFinding={selectFinding}
                onSelectLine={selectLine}
                onApplyFix={handleApplyFix}
                onCopySuccess={(msg) => setToastMessage(msg)}
                sourceCode={sourceCode}
              />
            </section>
          </div>
        </main>
      </div>

      {/* Modals for Secondary Views */}
      <HistoryModal
        isOpen={isHistoryOpen}
        onClose={() => {
          setIsHistoryOpen(false)
          setActiveNavTab('analyze')
        }}
        history={historyItems}
        onLoadHistoryItem={(code, name) => {
          loadSample(code, name)
          setToastMessage(`Restored from history: ${name}`)
        }}
        onClearHistory={() => {
          setHistoryItems([])
          localStorage.removeItem('typemind_analysis_history')
          setToastMessage('Analysis history cleared')
        }}
      />

      <ModelInsightsModal
        isOpen={isModelInsightsOpen}
        onClose={() => {
          setIsModelInsightsOpen(false)
          setActiveNavTab('analyze')
        }}
        modelInfo={serverStatus.modelInfo}
      />

      <DocumentationModal
        isOpen={isDocsOpen}
        onClose={() => {
          setIsDocsOpen(false)
          setActiveNavTab('analyze')
        }}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        confidenceThreshold={confidenceThreshold}
        onConfidenceChange={setConfidenceThreshold}
        enableMl={enableMl}
        onEnableMlChange={setEnableMl}
        onReset={() => {
          setConfidenceThreshold(0.60)
          setEnableMl(true)
          setToastMessage('Settings reset to defaults')
        }}
      />

      {/* Floating Action Feedback Toast */}
      {toastMessage && (
        <Toast message={toastMessage} onClose={() => setToastMessage(null)} />
      )}
    </div>
  )
}

export default App
