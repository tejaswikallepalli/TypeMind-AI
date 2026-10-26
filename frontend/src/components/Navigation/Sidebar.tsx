import React from 'react'
import { Plus, FolderCode, History, Cpu, Settings } from 'lucide-react'

import type { LanguageInfo } from '../../types/api'

interface SidebarProps {
  onNewAnalysis: () => void
  onOpenSamples: () => void
  onOpenHistory: () => void
  onOpenModelInsights: () => void
  onOpenSettings: () => void
  activeView: string
  currentLanguageInfo?: LanguageInfo
}

export const Sidebar: React.FC<SidebarProps> = ({
  onNewAnalysis,
  onOpenSamples,
  onOpenHistory,
  onOpenModelInsights,
  onOpenSettings,
  activeView,
  currentLanguageInfo,
}) => {
  return (
    <aside className="sidebar">
      {/* Primary New Analysis Action */}
      <button className="btn-new-analysis" onClick={onNewAnalysis} title="Start new code analysis">
        <Plus size={16} />
        <span>New Analysis</span>
      </button>

      {/* Sidebar Navigation */}
      <ul className="sidebar-nav-list">
        <li>
          <button
            className={`sidebar-nav-item ${activeView === 'samples' ? 'active' : ''}`}
            onClick={onOpenSamples}
          >
            <FolderCode size={15} />
            <span>Sample Programs</span>
          </button>
        </li>

        <li>
          <button
            className={`sidebar-nav-item ${activeView === 'history' ? 'active' : ''}`}
            onClick={onOpenHistory}
          >
            <History size={15} />
            <span>History</span>
          </button>
        </li>

        <li>
          <button
            className={`sidebar-nav-item ${activeView === 'model' ? 'active' : ''}`}
            onClick={onOpenModelInsights}
          >
            <Cpu size={15} />
            <span>Model Insights</span>
          </button>
        </li>

        <li>
          <button
            className={`sidebar-nav-item ${activeView === 'settings' ? 'active' : ''}`}
            onClick={onOpenSettings}
          >
            <Settings size={15} />
            <span>Settings</span>
          </button>
        </li>
      </ul>

      <div className="sidebar-spacer" />

      {/* Language Support Status Card */}
      <div className="sidebar-lang-card">
        <div className="sidebar-lang-header">
          <div className="sidebar-lang-title">
            <span
              className={`lang-status-dot ${currentLanguageInfo?.support_level || 'supported'}`}
            />
            <span>{currentLanguageInfo?.name || 'Python'}</span>
          </div>
          <span
            className="sidebar-lang-badge"
            style={{
              backgroundColor:
                currentLanguageInfo?.support_level === 'supported'
                  ? 'rgba(16, 185, 129, 0.15)'
                  : currentLanguageInfo?.support_level === 'partial'
                  ? 'rgba(56, 189, 248, 0.15)'
                  : 'rgba(239, 68, 68, 0.15)',
              color:
                currentLanguageInfo?.support_level === 'supported'
                  ? '#34d399'
                  : currentLanguageInfo?.support_level === 'partial'
                  ? '#38bdf8'
                  : '#f87171',
              borderColor:
                currentLanguageInfo?.support_level === 'supported'
                  ? 'rgba(16, 185, 129, 0.3)'
                  : currentLanguageInfo?.support_level === 'partial'
                  ? 'rgba(56, 189, 248, 0.3)'
                  : 'rgba(239, 68, 68, 0.3)',
            }}
          >
            {currentLanguageInfo?.support_level === 'supported'
              ? 'Supported'
              : currentLanguageInfo?.support_level === 'partial'
              ? 'Partial'
              : 'Missing Tool'}
          </span>
        </div>
        <p className="sidebar-lang-desc">{currentLanguageInfo?.tool_name || 'Built-in AST + ML'}</p>
      </div>

      {/* Quote with Background Curves */}
      <div className="sidebar-quote">
        <p>"Cleaner Code Smarter Developers"</p>
        <span>— TypeMind AI</span>
      </div>
    </aside>
  )
}
