/**
 * TypeMind AI — TypeScript API Contracts
 * Fully mirrors backend FastAPI Pydantic v2 schemas.
 */

export type Severity = 'error' | 'warning' | 'information' | 'hint'

export type ErrorCategory =
  | 'type_mismatch'
  | 'incompatible_return'
  | 'argument_count_mismatch'
  | 'argument_type_mismatch'
  | 'unsupported_operand'
  | 'invalid_assignment'
  | 'none_safety'
  | 'syntax_error'
  | 'attribute_not_found'
  | 'undefined_name'
  | 'other'

export type FindingOrigin = 'rule_based' | 'ml_prediction' | 'hybrid'

export interface SourceLocation {
  file_path?: string | null
  line: number
  column: number
  end_line?: number | null
  end_column?: number | null
}

export interface TypeInfo {
  raw_type: string
  is_inferred?: boolean
  type_args?: string[]
  confidence?: number | null
  notes?: string | null
}

export interface CodeReplacement {
  location: SourceLocation
  new_text: string
  description?: string | null
}

export interface SuggestedFix {
  id: string
  title: string
  description: string
  replacements: CodeReplacement[]
  diff_preview?: string | null
  confidence?: number
  is_auto_applicable?: boolean
  requires_user_review?: boolean
}

export interface MLPrediction {
  predicted_error_type: string
  confidence: number
  model_name: string
  model_version: string
  probabilities: Record<string, number>
  features_used: string[]
  notes?: string | null
}

export interface DiagnosticFinding {
  id: string
  message: string
  category: ErrorCategory
  severity: Severity
  location: SourceLocation
  origin: FindingOrigin
  is_confirmed: boolean
  expected_type?: TypeInfo | null
  observed_type?: TypeInfo | null
  ml_prediction?: MLPrediction | null
  rule_id?: string | null
  suggested_fixes: SuggestedFix[]
  explanation?: string | null
}

export interface AnalysisSummary {
  total_findings: number
  rule_based_findings: number
  ml_predicted_findings: number
  errors_count: number
  warnings_count: number
  syntax_errors_count: number
  category_counts: Record<string, number>
  severity_counts: Record<string, number>
  execution_time_ms: number
  lines_analyzed: number
}

export interface AnalysisRequest {
  source_code: string
  file_path?: string | null
  language?: string | null
  python_version?: string
  enable_ml_analysis?: boolean
  min_confidence?: number
}

export interface AnalysisResponse {
  status: 'success' | 'syntax_error' | 'partial' | 'tool_unavailable' | 'error'
  language?: string
  analyzer_id?: string
  support_level?: 'supported' | 'partial' | 'tool_unavailable' | 'unsupported' | string
  status_message?: string | null
  syntax_error?: DiagnosticFinding | null
  findings: DiagnosticFinding[]
  summary: AnalysisSummary
  server_version: string
}

export type LanguageSupportLevel = 'supported' | 'partial' | 'tool_unavailable'

export interface LanguageInfo {
  id: string
  name: string
  extensions: string[]
  support_level: LanguageSupportLevel
  tool_name: string
  tool_available: boolean
  ml_supported: boolean
  description: string
  setup_instructions?: string | null
}

export interface LanguagesResponse {
  languages: LanguageInfo[]
  total: number
  default_language: string
}

export interface HealthResponse {
  status: string
  version: string
  environment: string
}

export interface CategoryDetail {
  code: string
  title: string
  description: string
  default_severity: Severity
  rule_ids: string[]
  fix_support: boolean
}

export interface CategoriesResponse {
  categories: CategoryDetail[]
  total_categories: number
}

export interface ModelInfoResponse {
  status: 'loaded' | 'unavailable'
  model_name?: string | null
  model_version?: string | null
  model_architecture?: string | null
  trained_at?: string | null
  features_count: number
  classes: string[]
  evaluation_summary?: Record<string, any> | null
  dataset_info?: Record<string, any> | null
}

export interface ApiError {
  status?: string
  error_type?: string
  message: string
  detail?: any
  details?: any
  path?: string
  request_id?: string
}
