import React, { useEffect, useRef, useState } from 'react'
import {
  Activity,
  Bot,
  Check,
  ChevronRight,
  Copy,
  Cpu,
  Play,
  RefreshCw,
  Send,
  Server,
  Shield,
  Sparkles,
  Terminal,
} from 'lucide-react'
import { api } from '../services/api'
import type { ChatMessage, CheckpointItem, HostHealth, TaskItem, ViewType } from '../types'

interface AssistantViewProps {
  hosts: HostHealth[]
  checkpoints: CheckpointItem[]
  tasks: TaskItem[]
  onNavigate: (view: ViewType) => void
}

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-init-1',
    sender: 'assistant',
    text: `**Welcome to the Training Copilot!** 🧠\n\nI am your interactive engineering assistant for the **Execution-Verified Coding Model Training Platform (FEAT-024)**.\n\nI can help you:\n- **Understand Algorithms:** Explain on-policy GRPO reinforcement learning on Apple Silicon and MLX LoRA fine-tuning.\n- **Verify Sandbox Security:** Inspect cgroups v2 resource limits and air-gapped \`CLONE_NEWNET\` isolation.\n- **Review Datasets:** Explore the 105 curated tasks and avoid common candidate pitfalls.\n- **Debug Divergence:** Interpret holdout Pass@1 metrics and cryptographic adapter SHA-256 digests.`,
    timestamp: '12:00 PM',
    contextRef: 'docs/architecture.md',
    suggestedActions: [
      'How does GRPO work on Apple Silicon?',
      'Explain Sandbox Isolation',
      'How does SFT adapter divergence work?',
      'Help with py-fib-001',
    ],
  },
]

export const AssistantView: React.FC<AssistantViewProps> = ({
  hosts,
  checkpoints,
  tasks,
  onNavigate,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES)
  const [input, setInput] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [copiedCodeId, setCopiedCodeId] = useState<string | null>(null)
  const chatBottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim()
    if (!query || isLoading) return

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    if (!textToSend) setInput('')
    setIsLoading(true)

    try {
      const assistantMsg = await api.askTrainingAssistant(query, {
        currentView: 'assistant',
      })
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          text: 'Encountered an unexpected error generating response. Please check controller logs.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleCopyCode = (snippet: string, id: string) => {
    navigator.clipboard.writeText(snippet)
    setCopiedCodeId(id)
    setTimeout(() => setCopiedCodeId(null), 2000)
  }

  const handleClear = () => {
    setMessages(INITIAL_MESSAGES)
  }

  return (
    <div className="assistant-workspace">
      {/* Main Conversation Stream */}
      <div className="assistant-chat-panel">
        <div className="assistant-chat-header">
          <div className="assistant-header-title">
            <div className="assistant-avatar">
              <Bot size={22} color="var(--accent)" />
            </div>
            <div>
              <h2>Training Copilot</h2>
              <p>Grounded in AI Lab FEAT-024 Execution-Verified Architecture</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span className="badge-grounded">
              <Sparkles size={12} /> Local First
            </span>
            <button
              className="btn-icon-subtle"
              title="Reset conversation"
              onClick={handleClear}
            >
              <RefreshCw size={15} />
            </button>
          </div>
        </div>

        {/* Message History */}
        <div className="assistant-message-list">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`chat-bubble-row ${m.sender === 'user' ? 'user-row' : 'assistant-row'}`}
            >
              {m.sender === 'assistant' && (
                <div className="chat-avatar-assistant">
                  <Bot size={16} />
                </div>
              )}

              <div className={`chat-bubble ${m.sender === 'user' ? 'user-bubble' : 'assistant-bubble'}`}>
                <div className="bubble-header">
                  <span className="bubble-sender">
                    {m.sender === 'user' ? 'Operator' : 'Training Copilot'}
                  </span>
                  <span className="bubble-time">{m.timestamp}</span>
                </div>

                <div className="bubble-body">
                  {m.text.split('\n\n').map((paragraph, idx) => (
                    <p key={idx} style={{ marginBottom: idx < m.text.split('\n\n').length - 1 ? '10px' : '0' }}>
                      {paragraph}
                    </p>
                  ))}
                </div>

                {m.codeSnippet && (
                  <div className="bubble-code-box">
                    <div className="code-box-header">
                      <span>Python Reference</span>
                      <button
                        className="btn-copy-code"
                        onClick={() => handleCopyCode(m.codeSnippet!, m.id)}
                      >
                        {copiedCodeId === m.id ? (
                          <>
                            <Check size={12} color="var(--live)" /> Copied
                          </>
                        ) : (
                          <>
                            <Copy size={12} /> Copy
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
                  <div className="bubble-context-ref">
                    <Terminal size={11} /> Context Reference: <code>{m.contextRef}</code>
                  </div>
                )}

                {m.suggestedActions && m.suggestedActions.length > 0 && (
                  <div className="bubble-actions">
                    <span style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
                      Suggested Follow-ups:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {m.suggestedActions.map((act, i) => (
                        <button
                          key={i}
                          className="action-chip"
                          onClick={() => handleSend(act)}
                        >
                          <ChevronRight size={12} /> {act}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="chat-bubble-row assistant-row">
              <div className="chat-avatar-assistant">
                <Bot size={16} />
              </div>
              <div className="chat-bubble assistant-bubble typing-indicator-box">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span style={{ fontSize: '12px', color: 'var(--muted)', marginLeft: '8px' }}>
                  Synthesizing training architecture answer...
                </span>
              </div>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Input Bar */}
        <div className="assistant-input-area">
          <div className="quick-prompts-bar">
            <span style={{ fontSize: '11px', color: 'var(--muted)', marginRight: '6px' }}>Quick:</span>
            <button className="quick-prompt-btn" onClick={() => handleSend('How does GRPO work on Apple Silicon?')}>
              GRPO on Apple Silicon
            </button>
            <button className="quick-prompt-btn" onClick={() => handleSend('Explain Sandbox Isolation')}>
              Sandbox Isolation
            </button>
            <button className="quick-prompt-btn" onClick={() => handleSend('How does SFT adapter divergence work?')}>
              SFT LoRA Divergence
            </button>
            <button className="quick-prompt-btn" onClick={() => handleSend('What is the Reward Formula?')}>
              Reward Formula
            </button>
          </div>

          <div className="chat-input-wrapper">
            <textarea
              className="chat-textarea"
              placeholder="Ask anything about model training, sandbox execution, or coding tasks (Enter to send, Shift+Enter for newline)..."
              value={input}
              rows={2}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <button
              className="btn-chat-send"
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              title="Send question"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Side Context Inspector */}
      <div className="assistant-context-panel">
        <div className="panel-card" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Server size={16} color="var(--accent)" />
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink)' }}>Cluster Architecture</span>
          </div>

          <div className="context-host-list">
            {hosts.map((h) => (
              <div key={h.name} className="context-host-item">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', fontWeight: 500 }}>{h.name}</span>
                  <span className={`status-dot ${h.status}`} />
                </div>
                <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>
                  {h.role} ({h.port})
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel-card" style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <Shield size={16} color="var(--live)" />
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink)' }}>Security Safeguards</span>
          </div>
          <ul className="context-safeguard-list">
            <li>
              <strong>CLONE_NEWNET:</strong> Zero outbound network access
            </li>
            <li>
              <strong>cgroups v2:</strong> 512MB RAM, 5.0s CPU quota
            </li>
            <li>
              <strong>Unscorable VM:</strong> Infra errors never scored 0.0
            </li>
            <li>
              <strong>Adapter Proof:</strong> SHA-256 weight divergence
            </li>
          </ul>
        </div>

        <div className="panel-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <Activity size={16} color="var(--purple)" />
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink)' }}>Quick Navigators</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button
              className="btn-subtle"
              style={{ width: '100%', justifyContent: 'flex-start', fontSize: '12px' }}
              onClick={() => onNavigate('playground')}
            >
              <Play size={14} /> Open Model Playground
            </button>
            <button
              className="btn-subtle"
              style={{ width: '100%', justifyContent: 'flex-start', fontSize: '12px' }}
              onClick={() => onNavigate('experiments')}
            >
              <Cpu size={14} /> View Experiments ({checkpoints.length} Adapters)
            </button>
            <button
              className="btn-subtle"
              style={{ width: '100%', justifyContent: 'flex-start', fontSize: '12px' }}
              onClick={() => onNavigate('datasets')}
            >
              <Terminal size={14} /> Browse {tasks.length} Curated Tasks
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
