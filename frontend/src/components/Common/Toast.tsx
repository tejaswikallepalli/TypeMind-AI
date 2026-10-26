import React, { useEffect } from 'react'
import { Check, Info } from 'lucide-react'

interface ToastProps {
  message: string
  type?: 'success' | 'info'
  onClose: () => void
  durationMs?: number
}

export const Toast: React.FC<ToastProps> = ({ message, type = 'success', onClose, durationMs = 2500 }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose()
    }, durationMs)
    return () => clearTimeout(timer)
  }, [onClose, durationMs])

  return (
    <div
      role="status"
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '10px 16px',
        borderRadius: '8px',
        backgroundColor: '#151c2d',
        border: '1px solid rgba(6, 182, 212, 0.4)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
        color: '#f8fafc',
        fontSize: '0.85rem',
        animation: 'fadeIn 0.2s ease-in-out',
      }}
    >
      {type === 'success' ? <Check size={16} color="#10b981" /> : <Info size={16} color="#06b6d4" />}
      <span>{message}</span>
    </div>
  )
}
