/**
 * Editor and workspace domain types.
 */


export interface CodeSample {
  id: string
  name: string
  description: string
  code: string
  language?: string
  expectedCategory?: string
}

export interface EditorPosition {
  line: number
  column: number
}

export interface AnalysisState {
  isAnalyzing: boolean
  lastAnalyzedAt: Date | null
  executionDurationMs: number | null
  error: string | null
  selectedFindingId: string | null
  filterSeverity: 'all' | 'error' | 'warning'
  filterCategory: string | null
}
