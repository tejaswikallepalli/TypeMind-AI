import { useState, useEffect, useCallback } from 'react'
import { checkHealth, getModelInfo } from '../services/api'
import type { HealthResponse, ModelInfoResponse } from '../types/api'

export interface ServerStatus {
  isOnline: boolean
  health: HealthResponse | null
  modelInfo: ModelInfoResponse | null
  isLoading: boolean
  lastChecked: Date | null
  refresh: () => Promise<void>
}

export function useServerStatus(): ServerStatus {
  const [isOnline, setIsOnline] = useState<boolean>(false)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [lastChecked, setLastChecked] = useState<Date | null>(null)

  const checkStatus = useCallback(async () => {
    setIsLoading(true)
    try {
      const [healthData, modelData] = await Promise.all([
        checkHealth().catch(() => null),
        getModelInfo().catch(() => null),
      ])

      if (healthData && healthData.status === 'healthy') {
        setIsOnline(true)
        setHealth(healthData)
      } else {
        setIsOnline(false)
        setHealth(null)
      }

      setModelInfo(modelData)
      setLastChecked(new Date())
    } catch {
      setIsOnline(false)
      setHealth(null)
      setModelInfo(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    checkStatus()
    // Periodic check every 30 seconds
    const interval = setInterval(checkStatus, 30_000)
    return () => clearInterval(interval)
  }, [checkStatus])

  return {
    isOnline,
    health,
    modelInfo,
    isLoading,
    lastChecked,
    refresh: checkStatus,
  }
}
