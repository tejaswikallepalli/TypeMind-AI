import React from 'react'
import type { ErrorCategory, FindingOrigin, Severity } from '../../types/api'
import { AlertCircle, AlertTriangle, Cpu, CheckCircle2, ShieldCheck, Sparkles } from 'lucide-react'

interface BadgeProps {
  type?: 'severity' | 'origin' | 'category' | 'confirmed' | 'custom'
  severity?: Severity
  origin?: FindingOrigin
  category?: ErrorCategory | string
  isConfirmed?: boolean
  label?: string
  className?: string
}

export const Badge: React.FC<BadgeProps> = ({
  type = 'custom',
  severity,
  origin,
  category,
  isConfirmed,
  label,
  className = '',
}) => {
  if (type === 'severity' && severity) {
    if (severity === 'error') {
      return (
        <span className={`badge badge-error ${className}`}>
          <AlertCircle size={12} />
          Error
        </span>
      )
    }
    if (severity === 'warning') {
      return (
        <span className={`badge badge-warning ${className}`}>
          <AlertTriangle size={12} />
          Warning
        </span>
      )
    }
    return <span className={`badge badge-neutral ${className}`}>{severity}</span>
  }

  if (type === 'origin' && origin) {
    if (origin === 'rule_based') {
      return (
        <span className={`badge badge-neutral ${className}`} title="Deterministically proven by static AST analysis">
          <ShieldCheck size={12} />
          Rule-Based
        </span>
      )
    }
    if (origin === 'hybrid') {
      return (
        <span className={`badge badge-cyan ${className}`} title="Rule finding corroborated by ML classifier">
          <Sparkles size={12} />
          Hybrid
        </span>
      )
    }
    if (origin === 'ml_prediction') {
      return (
        <span className={`badge badge-violet ${className}`} title="Probabilistic machine learning prediction">
          <Cpu size={12} />
          ML Predicted
        </span>
      )
    }
  }

  if (type === 'confirmed') {
    if (isConfirmed) {
      return (
        <span className={`badge badge-success ${className}`} title="Confirmed by deterministic semantic verification">
          <CheckCircle2 size={12} />
          Confirmed
        </span>
      )
    }
    return (
      <span className={`badge badge-neutral ${className}`} title="Unconfirmed statistical candidate">
        Probabilistic
      </span>
    )
  }

  if (type === 'category' && category) {
    const formatted = category.replace(/_/g, ' ')
    return <span className={`badge badge-neutral ${className}`}>{formatted}</span>
  }

  return <span className={`badge badge-neutral ${className}`}>{label}</span>
}
