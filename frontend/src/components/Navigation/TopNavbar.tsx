import React from 'react'
import { Code2, History, Cpu, FileText } from 'lucide-react'
import type { ServerStatus } from '../../hooks/useServerStatus'

interface TopNavbarProps {
  activeTab: 'analyze' | 'history' | 'model' | 'docs'
  onTabChange: (tab: 'analyze' | 'history' | 'model' | 'docs') => void
  serverStatus: ServerStatus
}

export const TopNavbar: React.FC<TopNavbarProps> = ({ activeTab, onTabChange, serverStatus }) => {
  const { isOnline, health, modelInfo } = serverStatus

  return (
    <header className="top-navbar">
      {/* Brand & Identity */}
      <div className="nav-brand">
        <div className="nav-brand-logo" title="TypeMind AI Engine">
          <Code2 size={20} />
        </div>
        <div className="nav-brand-text">
          <div className="nav-brand-title">
            TypeMind <span className="ai-gradient">AI</span>
          </div>
          <div className="nav-brand-subtitle">
            Understand Code. Detect Errors. Think Smarter.
          </div>
        </div>
      </div>

      {/* Center Navigation Pills */}
      <nav className="nav-center-pills" aria-label="Primary Navigation">
        <button
          className={`nav-pill-btn ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => onTabChange('analyze')}
        >
          <Code2 size={14} />
          <span>Analyze</span>
        </button>

        <button
          className={`nav-pill-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => onTabChange('history')}
        >
          <History size={14} />
          <span>History</span>
        </button>

        <button
          className={`nav-pill-btn ${activeTab === 'model' ? 'active' : ''}`}
          onClick={() => onTabChange('model')}
        >
          <Cpu size={14} />
          <span>Model</span>
        </button>

        <button
          className={`nav-pill-btn ${activeTab === 'docs' ? 'active' : ''}`}
          onClick={() => onTabChange('docs')}
        >
          <FileText size={14} />
          <span>Documentation</span>
        </button>
      </nav>

      {/* Right Actions & Status Badges */}
      <div className="nav-right-actions">
        {/* Backend & ML Status Pill */}
        <div
          className="status-indicator-pill"
          title={
            isOnline
              ? `Backend v${health?.version || '0.1.0'} healthy | ML: ${
                  modelInfo?.status === 'loaded' ? modelInfo.model_architecture : 'Unavailable'
                }`
              : 'Backend connection offline'
          }
        >
          <div className={`status-dot ${isOnline ? 'online' : 'offline'}`} />
          <span>
            {isOnline
              ? modelInfo?.status === 'loaded'
                ? `Ready (${modelInfo.model_architecture || 'ML'})`
                : 'Ready (Rules only)'
              : 'Offline'}
          </span>
        </div>

        {/* Dark Theme Toggle Mockup */}
        <div className="theme-toggle-switch" title="Dark theme active (default)">
          <div className="theme-toggle-knob" />
        </div>

        {/* User Workspace Avatar */}
        <div className="user-avatar" title="TypeMind AI Developer">
          V
        </div>
      </div>
    </header>
  )
}
