import React from 'react'
import { ShieldCheck, Sparkles, Lightbulb, BarChart3 } from 'lucide-react'

export const HeroBanner: React.FC = () => {
  return (
    <div className="hero-banner">
      <div className="hero-titles">
        <h1 className="hero-title-main">
          TypeMind <span className="gradient-word">AI</span>
        </h1>
        <p className="hero-subtitle">
          Machine Learning-Based Semantic Analyzer for Intelligent Type Error Detection
        </p>
      </div>

      <div className="hero-features-grid">
        <div className="hero-feature-card">
          <ShieldCheck size={18} color="#38bdf8" />
          <span className="hero-feature-title">Detect Type Errors</span>
        </div>

        <div className="hero-feature-card">
          <Sparkles size={18} color="#c084fc" />
          <span className="hero-feature-title">AI-Powered Analysis</span>
        </div>

        <div className="hero-feature-card">
          <Lightbulb size={18} color="#facc15" />
          <span className="hero-feature-title">Smart Suggestions</span>
        </div>

        <div className="hero-feature-card">
          <BarChart3 size={18} color="#a78bfa" />
          <span className="hero-feature-title">Developer Insights</span>
        </div>
      </div>
    </div>
  )
}
