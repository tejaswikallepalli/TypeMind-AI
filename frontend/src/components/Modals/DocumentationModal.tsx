import React, { useState } from 'react'
import { X, FileText, Layers, Cpu, ShieldCheck } from 'lucide-react'

interface DocumentationModalProps {
  isOpen: boolean
  onClose: () => void
}

const LANGUAGES_CATALOG = [
  { id: 'python', name: 'Python', exts: '.py, .pyi', tool: 'Built-in AST + ML', tier: 'Supported', desc: 'Symbol table inference, deterministic rules TM000–TM007, and Random Forest classifier.' },
  { id: 'typescript', name: 'TypeScript', exts: '.ts, .tsx', tool: 'tsc --noEmit', tier: 'Supported', desc: 'Comprehensive static type checking using TypeScript compiler diagnostics without binary emission.' },
  { id: 'javascript', name: 'JavaScript', exts: '.js, .jsx', tool: 'tsc / Node.js', tier: 'Supported', desc: 'JSDoc type checking via tsc --checkJs and syntax verification.' },
  { id: 'java', name: 'Java', exts: '.java', tool: 'javac -proc:none', tier: 'Host Toolchain', desc: 'Compiler type checks and linting (-proc:none -Xlint) with safe annotation processor suppression.' },
  { id: 'c', name: 'C', exts: '.c, .h', tool: 'gcc/clang -fsyntax-only', tier: 'Host Toolchain', desc: 'Static syntax and type check using GCC, Clang, or MSVC cl /Zs.' },
  { id: 'cpp', name: 'C++', exts: '.cpp, .hpp', tool: 'g++/clang++ -fsyntax-only', tier: 'Host Toolchain', desc: 'Template type analysis and modern C++20 semantic checks without code generation.' },
  { id: 'csharp', name: 'C#', exts: '.cs', tool: 'csc / dotnet build', tier: 'Host Toolchain', desc: 'Roslyn compiler diagnostics (/t:module) with strict error normalization.' },
  { id: 'go', name: 'Go', exts: '.go', tool: 'go vet / build', tier: 'Host Toolchain', desc: 'Go compiler diagnostics and vet static analyzer.' },
  { id: 'rust', name: 'Rust', exts: '.rs', tool: 'rustc --emit=metadata', tier: 'Host Toolchain', desc: 'Rust compiler JSON diagnostics covering type mismatches and borrow checker rules.' },
  { id: 'php', name: 'PHP', exts: '.php', tool: 'php -l', tier: 'Partial (Syntax)', desc: 'PHP fatal error and syntax linting.' },
  { id: 'ruby', name: 'Ruby', exts: '.rb', tool: 'ruby -c', tier: 'Partial (Syntax)', desc: 'Ruby syntax and compile-time check.' },
]

const RULES = [
  { id: 'TM000', name: 'SYNTAX_ERROR', desc: 'Syntax failure during AST grammar parsing; halts further checking.' },
  { id: 'TM001', name: 'STRING_NUMBER_CONCAT', desc: 'Binary + concatenation between str and numeric (int, float, bool).' },
  { id: 'TM002', name: 'UNSUPPORTED_ARITHMETIC', desc: 'Incompatible operands like str - str, None + num, or list + tuple.' },
  { id: 'TM003', name: 'ARGUMENT_COUNT_MISMATCH', desc: 'Calling function with too few or excessive positional arguments.' },
  { id: 'TM004', name: 'ARGUMENT_TYPE_MISMATCH', desc: 'Passing argument of incompatible type to annotated parameter.' },
  { id: 'TM005', name: 'INCOMPATIBLE_RETURN', desc: 'Return expression does not match declared return annotation.' },
  { id: 'TM006', name: 'INVALID_ANNOTATED_ASSIGNMENT', desc: 'Assigning incompatible expression to explicitly annotated variable.' },
  { id: 'TM007', name: 'INCOMPATIBLE_REASSIGNMENT', desc: 'Reassigning a variable in the same scope to an incompatible type.' },
]

export const DocumentationModal: React.FC<DocumentationModalProps> = ({ isOpen, onClose }) => {
  const [activeDocTab, setActiveDocTab] = useState<'languages' | 'rules'>('languages')

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content-card" style={{ maxWidth: '800px', maxHeight: '85vh' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} color="var(--accent-purple-light)" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff' }}>
              TypeMind AI Architecture & Specifications
            </h3>
          </div>
          <button className="btn-tool" onClick={onClose} aria-label="Close documentation">
            <X size={16} />
          </button>
        </div>

        {/* Tab Toggle */}
        <div style={{ display: 'flex', gap: 8, padding: '10px 18px', borderBottom: '1px solid var(--border-subtle)' }}>
          <button
            className={`tab-btn ${activeDocTab === 'languages' ? 'active' : ''}`}
            onClick={() => setActiveDocTab('languages')}
          >
            <Layers size={13} />
            <span>Supported Languages (11)</span>
          </button>
          <button
            className={`tab-btn ${activeDocTab === 'rules' ? 'active' : ''}`}
            onClick={() => setActiveDocTab('rules')}
          >
            <Cpu size={13} />
            <span>Python Semantic Rules</span>
          </button>
        </div>

        <div className="modal-body" style={{ overflowY: 'auto', maxHeight: '60vh', padding: '16px 20px' }}>
          {activeDocTab === 'languages' ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10, color: 'var(--accent-cyan)' }}>
                <ShieldCheck size={16} />
                <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Zero-Execution Safe Sandbox</span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 14 }}>
                TypeMind AI analyzes source code across 11 programming languages using dedicated language adapters. Submitted code is <strong>never executed</strong>, avoiding arbitrary code execution or project script vulnerabilities. Compilers are run strictly in syntax/metadata mode (e.g. <code>--noEmit</code>, <code>-fsyntax-only</code>, <code>-proc:none</code>).
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {LANGUAGES_CATALOG.map((lang) => (
                  <div
                    key={lang.id}
                    style={{
                      backgroundColor: 'var(--bg-card)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '10px 14px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 4,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.85rem' }}>{lang.name}</span>
                        <code style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{lang.exts}</code>
                      </div>
                      <span
                        style={{
                          fontSize: '0.68rem',
                          fontWeight: 600,
                          padding: '2px 8px',
                          borderRadius: '10px',
                          background: lang.tier.includes('Supported') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(56, 189, 248, 0.15)',
                          color: lang.tier.includes('Supported') ? '#34d399' : '#38bdf8',
                        }}
                      >
                        {lang.tier}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', margin: 0 }}>
                      <strong>Toolchain:</strong> <code>{lang.tool}</code> — {lang.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 12 }}>
                Python source code undergoes symbol table collection, AST type inference, deterministic rule validation, and corroboration with the Random Forest classifier:
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {RULES.map((rule) => (
                  <div
                    key={rule.id}
                    style={{
                      backgroundColor: 'var(--bg-card)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '8px 12px',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '10px',
                    }}
                  >
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.725rem',
                        fontWeight: 700,
                        padding: '2px 6px',
                        backgroundColor: 'rgba(168, 85, 247, 0.15)',
                        color: 'var(--accent-purple-light)',
                        borderRadius: '4px',
                        flexShrink: 0,
                      }}
                    >
                      {rule.id}
                    </span>
                    <div>
                      <div style={{ fontSize: '0.825rem', fontWeight: 600, color: '#ffffff' }}>{rule.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        {rule.desc}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ borderTop: '1px solid var(--border-subtle)', padding: '12px 18px', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn-tool" onClick={onClose} style={{ padding: '6px 14px' }}>
            <span>Close</span>
          </button>
        </div>
      </div>
    </div>
  )
}
