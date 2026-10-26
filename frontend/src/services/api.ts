import type {
  AnalysisRequest,
  AnalysisResponse,
  CategoriesResponse,
  HealthResponse,
  ModelInfoResponse,
} from '../types/api'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')

export class ApiClientError extends Error {
  status?: number
  errorType?: string
  details?: unknown
  requestId?: string

  constructor(message: string, status?: number, errorType?: string, details?: unknown, requestId?: string) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.errorType = errorType
    this.details = details
    this.requestId = requestId
  }
}

/**
 * Fetch with unified error decoding and timeout handling.
 */
async function fetchJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')
  if (options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json')
  }

  let response: Response
  try {
    response = await fetch(url, {
      ...options,
      headers,
    })
  } catch (networkError: unknown) {
    const msg = networkError instanceof Error ? networkError.message : String(networkError)
    throw new ApiClientError(
      `Unable to connect to TypeMind AI backend at ${API_BASE_URL}. Ensure the backend server is running. (${msg})`,
      0,
      'NetworkError'
    )
  }

  const requestId = response.headers.get('X-Request-ID') || undefined

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`
    let errorType = 'HttpError'
    let details: unknown = null

    try {
      const errorJson = await response.json()
      if (errorJson.message) {
        errorMessage = errorJson.message
      }
      if (errorJson.error_type) {
        errorType = errorJson.error_type
      }
      if (errorJson.details || errorJson.detail) {
        details = errorJson.details || errorJson.detail
      }
    } catch {
      // Body not JSON
    }

    throw new ApiClientError(errorMessage, response.status, errorType, details, requestId)
  }

  return response.json() as Promise<T>
}

/**
 * Perform Python AST semantic and ML analysis.
 */
export async function analyzeCode(request: AnalysisRequest): Promise<AnalysisResponse> {
  if (!request.source_code || request.source_code.trim().length === 0) {
    throw new ApiClientError('Source code cannot be empty.', 422, 'ValidationError')
  }

  const byteLength = new Blob([request.source_code]).size
  if (byteLength > 500_000) {
    throw new ApiClientError(
      `Source code exceeds 500 KB limit (${(byteLength / 1024).toFixed(1)} KB). Please reduce code size.`,
      422,
      'ValidationError'
    )
  }

  return fetchJson<AnalysisResponse>('/api/v1/analyze', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Check backend operational health.
 */
export async function checkHealth(): Promise<HealthResponse> {
  return fetchJson<HealthResponse>('/health')
}

/**
 * Retrieve active ML type classifier metadata.
 */
export async function getModelInfo(): Promise<ModelInfoResponse> {
  return fetchJson<ModelInfoResponse>('/api/v1/model/info')
}

/**
 * Retrieve catalog of recognized diagnostic categories.
 */
export async function getDiagnosticCategories(): Promise<CategoriesResponse> {
  return fetchJson<CategoriesResponse>('/api/v1/diagnostics/categories')
}

/**
 * Retrieve supported programming languages and their live tool status.
 */
export async function fetchLanguages(): Promise<import('../types/api').LanguagesResponse> {
  return fetchJson<import('../types/api').LanguagesResponse>('/api/v1/languages')
}

export { API_BASE_URL }

