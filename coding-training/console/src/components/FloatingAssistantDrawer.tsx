import React, { useEffect, useRef, useState } from 'react'
import {
  Bot,
  Check,
  Copy,
  Maximize2,
  Send,
  X,
} from 'lucide-react'
import { api } from '../services/api'
import type { ChatMessage, ViewType } from '../types'

interface FloatingAssistantDrawerProps {
  currentView: ViewType
  onNavigate: (view: ViewType) => void
}

export const FloatingAssistantDrawer: React.FC<FloatingAssistantDrawerProps> = ({
  currentView,
  onNavigate,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'drawer-welcome',
      sender: 'assistant',
      text: 'Need help with training, sandbox execution, or coding tasks? Ask me anything!',
      timestamp: 'Now',
    },
  ])
  const [input, setInput] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen, isLoading])

  // Context-aware quick suggestions based on the active console screen
  const getContextSuggestions = (): string[] => {
    switch (currentView) {
      case 'playground':
        return [
          'Help with py-fib-001',
          'Explain sandbox execution',
          'Why did my code fail?',
        ]
      case 'experiments':
        return [
          'How does GRPO work on Apple Silicon?',
          'What is parameter divergence?',
          'Explain the loss curve',
        ]
      case 'monitor':
        return [
          'Explain worker throughput',
          'What is CLONE_NEWNET?',
          'How is telemetry streamed?',
        ]
      case 'models':
        return [
          'How does SFT adapter divergence work?',
          'What is LoRA rank 8?',
        ]
      case 'datasets':
        return [
          'How are splits kept disjoint?',
          'Why are test assertions hidden?',
        ]
      default:
        return [
          'How does GRPO work on Apple Silicon?',
          'Explain Sandbox Isolation',
          'What is the Reward Formula?',
        ]
    }
  }

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim()
    if (!query || isLoading) return

    const userMsg: ChatMessage = {
      id: `drawer-user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    if (!textToSend) setInput('')
    setIsLoading(true)

    try {
      const resp = await api.askTrainingAssistant(query, { currentView })
      setMessages((prev) => [...prev, resp])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `drawer-err-${Date.now()}`,
          sender: 'assistant',
          text: 'Unable to connect to assistant backend. Check controller logs.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopyCode = (snippet: string, id: string) => {
    navigator.clipboard.writeText(snippet)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  // If already on the full assistant view, hide the floating drawer to prevent redundancy
  if (currentView === 'assistant') {
    return null
  }

  return (
    <div className="floating-assistant-container">
      {/* Trigger Button */}
      {!isOpen && (
        <button
          className="floating-assistant-trigger"
          onClick={() => setIsOpen(true)}
          title="Open Training Copilot"
        >
          <span className="trigger-pulse" />
          <Bot size={20} />
          <span>Training Copilot</span>
          <span className="trigger-context-badge">
            {currentView.toUpperCase()}
          </span>
        </button>
      )}

      {/* Expanded Sliding Drawer */}
      {isOpen && (
        <div className="floating-drawer-card">
          {/* Header */}
          <div className="floating-drawer-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div className="drawer-avatar">
                <Bot size={16} color="var(--accent)" />
              </div>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink)' }}>
                  Training Copilot
                </div>
                <div style={{ fontSize: '10px', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span className="status-dot healthy" style={{ width: '6px', height: '6px' }} />
                  Context: <strong style={{ color: 'var(--accent)' }}>{currentView}</strong>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <button
                className="btn-icon-subtle"
                title="Expand to Full View"
                onClick={() => {
                  setIsOpen(false)
                  onNavigate('assistant')
                }}
              >
                <Maximize2 size={14} />
              </button>
              <button
                className="btn-icon-subtle"
                title="Minimize Copilot"
                onClick={() => setIsOpen(false)}
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {/* Quick Context Prompts */}
          <div className="drawer-quick-prompts">
            {getContextSuggestions().map((s, i) => (
              <button
                key={i}
                className="drawer-prompt-chip"
                onClick={() => handleSend(s)}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Messages Stream */}
          <div className="floating-drawer-messages">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`drawer-msg-row ${m.sender === 'user' ? 'drawer-user' : 'drawer-assistant'}`}
              >
                <div className="drawer-msg-bubble">
                  <div className="drawer-msg-text">
                    {m.text.split('\n\n').map((p, idx) => (
                      <p key={idx} style={{ marginBottom: idx < m.text.split('\n\n').length - 1 ? '6px' : '0' }}>
                        {p}
                      </p>
                    ))}
                  </div>

                  {m.codeSnippet && (
                    <div className="drawer-code-box">
                      <div className="drawer-code-header">
                        <span>Code Reference</span>
                        <button
                          className="btn-copy-code"
                          style={{ padding: '2px 6px', fontSize: '10px' }}
                          onClick={() => handleCopyCode(m.codeSnippet!, m.id)}
                        >
                          {copiedId === m.id ? (
                            <>
                              <Check size={10} color="var(--live)" /> Copied
                            </>
                          ) : (
                            <>
                              <Copy size={10} /> Copy
                            </>
                          )}
                        </button>
                      </div>
                      <pre>
                        <code>{m.codeSnippet}</code>
                      </pre>
                    </div>
                  )}

                  {m.contextRef && (
                    <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '4px' }}>
                      Ref: <code>{m.contextRef}</code>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="drawer-msg-row drawer-assistant">
                <div className="drawer-msg-bubble" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Input Box */}
          <div className="floating-drawer-input">
            <input
              type="text"
              className="drawer-input-field"
              placeholder={`Ask about ${currentView}... (Enter)`}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleSend()
                }
              }}
              disabled={isLoading}
            />
            <button
              className="drawer-send-btn"
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
            >
              <Send size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
