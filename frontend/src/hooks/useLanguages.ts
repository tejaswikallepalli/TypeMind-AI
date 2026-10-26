import { useState, useEffect, useCallback } from 'react'
import { fetchLanguages } from '../services/api'
import type { LanguageInfo } from '../types/api'

// Fallback initial languages list matching backend registry
const DEFAULT_LANGUAGES: LanguageInfo[] = [
  {
    id: 'python',
    name: 'Python',
    extensions: ['.py', '.pyi', '.pyw'],
    support_level: 'supported',
    tool_name: 'Built-in AST + ML',
    tool_available: true,
    ml_supported: true,
    description: 'Static AST semantic analysis with symbol table inference and ML pattern classification.',
  },
  {
    id: 'typescript',
    name: 'TypeScript',
    extensions: ['.ts', '.tsx'],
    support_level: 'supported',
    tool_name: 'TypeScript Compiler (tsc)',
    tool_available: true,
    ml_supported: false,
    description: 'Static type checking using TypeScript compiler diagnostics (tsc --noEmit).',
  },
  {
    id: 'javascript',
    name: 'JavaScript',
    extensions: ['.js', '.jsx'],
    support_level: 'supported',
    tool_name: 'JavaScript Engine (tsc/Node)',
    tool_available: true,
    ml_supported: false,
    description: 'JavaScript static analysis with type checking via JSDoc/inference and syntax checking.',
  },
  {
    id: 'java',
    name: 'Java',
    extensions: ['.java'],
    support_level: 'tool_unavailable',
    tool_name: 'Java Compiler (javac)',
    tool_available: false,
    ml_supported: false,
    description: 'Static semantic and type analysis using Java compiler diagnostics (-proc:none -Xlint).',
    setup_instructions: 'Install JDK 17+ (Adoptium Temurin) and ensure javac is on PATH.',
  },
  {
    id: 'c',
    name: 'C',
    extensions: ['.c', '.h'],
    support_level: 'tool_unavailable',
    tool_name: 'C Compiler (gcc/clang/cl)',
    tool_available: false,
    ml_supported: false,
    description: 'Static type and syntax verification using C compiler diagnostics (-fsyntax-only).',
    setup_instructions: 'Install GCC, Clang, or MSVC Build Tools.',
  },
  {
    id: 'cpp',
    name: 'C++',
    extensions: ['.cpp', '.cc', '.cxx', '.hpp'],
    support_level: 'tool_unavailable',
    tool_name: 'C++ Compiler (g++/clang++/cl)',
    tool_available: false,
    ml_supported: false,
    description: 'Static type and template diagnostics using C++ compiler (-fsyntax-only -std=c++20).',
    setup_instructions: 'Install G++, Clang++, or MSVC Build Tools.',
  },
  {
    id: 'csharp',
    name: 'C#',
    extensions: ['.cs'],
    support_level: 'tool_unavailable',
    tool_name: 'C# Roslyn (csc/dotnet)',
    tool_available: false,
    ml_supported: false,
    description: 'Static type checking via Roslyn compiler diagnostics (csc /t:module).',
    setup_instructions: 'Install .NET SDK 8.0+.',
  },
  {
    id: 'go',
    name: 'Go',
    extensions: ['.go'],
    support_level: 'tool_unavailable',
    tool_name: 'Go Toolchain (go vet/build)',
    tool_available: false,
    ml_supported: false,
    description: 'Static type and semantic checking using the Go compiler and vet tooling.',
    setup_instructions: 'Install Go toolchain: https://go.dev/dl/.',
  },
  {
    id: 'rust',
    name: 'Rust',
    extensions: ['.rs'],
    support_level: 'tool_unavailable',
    tool_name: 'Rust Compiler (rustc)',
    tool_available: false,
    ml_supported: false,
    description: 'Static type and borrow checking using rustc compiler diagnostics (--emit=metadata).',
    setup_instructions: 'Install Rust toolchain: https://rustup.rs/.',
  },
  {
    id: 'php',
    name: 'PHP',
    extensions: ['.php'],
    support_level: 'tool_unavailable',
    tool_name: 'PHP CLI (php -l)',
    tool_available: false,
    ml_supported: false,
    description: 'PHP syntax checking and fatal error linting (php -l).',
    setup_instructions: 'Install PHP CLI: https://windows.php.net/download/.',
  },
  {
    id: 'ruby',
    name: 'Ruby',
    extensions: ['.rb'],
    support_level: 'tool_unavailable',
    tool_name: 'Ruby CLI (ruby -c)',
    tool_available: false,
    ml_supported: false,
    description: 'Ruby syntax and compile-time check (ruby -c).',
    setup_instructions: 'Install Ruby: https://rubyinstaller.org/.',
  },
]

export function useLanguages() {
  const [languages, setLanguages] = useState<LanguageInfo[]>(DEFAULT_LANGUAGES)
  const [selectedLanguage, setSelectedLanguage] = useState<string>('python')
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const loadLanguages = useCallback(async () => {
    try {
      const resp = await fetchLanguages()
      if (resp && resp.languages && resp.languages.length > 0) {
        setLanguages(resp.languages)
      }
    } catch {
      // Keep DEFAULT_LANGUAGES on error
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadLanguages()
  }, [loadLanguages])

  const detectLanguageFromFile = useCallback(
    (fileName: string): string | null => {
      const lower = fileName.toLowerCase()
      for (const lang of languages) {
        for (const ext of lang.extensions) {
          if (lower.endsWith(ext.toLowerCase())) {
            return lang.id
          }
        }
      }
      return null
    },
    [languages]
  )

  const currentLanguageInfo = languages.find((l) => l.id === selectedLanguage) || DEFAULT_LANGUAGES[0]

  return {
    languages,
    selectedLanguage,
    setSelectedLanguage,
    currentLanguageInfo,
    detectLanguageFromFile,
    isLoading,
    refreshLanguages: loadLanguages,
  }
}
