import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CodeEditor } from '../components/Editor/CodeEditor'

describe('CodeEditor Component', () => {
  it('renders line numbers and code content', () => {
    const code = 'def test():\n    return 42'
    const onChange = vi.fn()
    const onAnalyze = vi.fn()

    render(
      <CodeEditor
        code={code}
        onChange={onChange}
        onAnalyze={onAnalyze}
        findings={[]}
      />
    )

    // Check textarea exists with proper accessibility label
    const textarea = screen.getByLabelText(/Python source code editor/i)
    expect(textarea).toBeInTheDocument()
    expect(textarea).toHaveValue(code)

    // Check line numbers 1 and 2
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('triggers onAnalyze on Ctrl+Enter shortcut', () => {
    const code = 'print("hello")'
    const onChange = vi.fn()
    const onAnalyze = vi.fn()

    render(
      <CodeEditor
        code={code}
        onChange={onChange}
        onAnalyze={onAnalyze}
        findings={[]}
      />
    )

    const textarea = screen.getByLabelText(/Python source code editor/i)
    fireEvent.keyDown(textarea, { key: 'Enter', ctrlKey: true })

    expect(onAnalyze).toHaveBeenCalledTimes(1)
  })

  it('inserts 4 spaces when Tab is pressed', () => {
    const code = 'line1\n'
    const onChange = vi.fn()
    const onAnalyze = vi.fn()

    render(
      <CodeEditor
        code={code}
        onChange={onChange}
        onAnalyze={onAnalyze}
        findings={[]}
      />
    )

    const textarea = screen.getByLabelText(/Python source code editor/i) as HTMLTextAreaElement
    textarea.setSelectionRange(0, 0)
    fireEvent.keyDown(textarea, { key: 'Tab' })

    expect(onChange).toHaveBeenCalledWith('    line1\n')
  })
})
