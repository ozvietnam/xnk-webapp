'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { createClient } from '@/lib/supabase'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: string[]
  error?: boolean
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

const SUGGESTED = [
  'Mã HS cho điện thoại thông minh nhập từ Trung Quốc?',
  'Thuế nhập khẩu máy tính xách tay theo ACFTA?',
  'Mã HS thép cuộn cán nguội là gì?',
  'Nhôm thanh định hình nhập khẩu chịu thuế bao nhiêu?',
]

function TypingDots() {
  return (
    <div className="flex gap-1 items-center px-1 py-0.5">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  )
}

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => crypto.randomUUID())
  const [authToken, setAuthToken] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Get auth token on mount
  useEffect(() => {
    const supabase = createClient()
    supabase.auth.getSession().then(({ data }) => {
      setAuthToken(data.session?.access_token ?? null)
    })
  }, [])

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = useCallback(
    async (question: string) => {
      const q = question.trim()
      if (!q || loading) return

      setMessages(prev => [...prev, { role: 'user', content: q }])
      setInput('')
      setLoading(true)

      try {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' }
        if (authToken) headers['Authorization'] = `Bearer ${authToken}`

        const res = await fetch(`${API_URL}/api/chatbot/ask`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ question: q, session_id: sessionId }),
        })

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`)
        }

        const data = await res.json()
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: data.answer,
            citations: data.citations ?? [],
          },
        ])
      } catch (err) {
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: 'Xin lỗi, không kết nối được máy chủ. Vui lòng thử lại.',
            error: true,
          },
        ])
      } finally {
        setLoading(false)
        setTimeout(() => inputRef.current?.focus(), 50)
      }
    },
    [loading, authToken, sessionId]
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage(input)
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-3xl flex flex-col h-[calc(100vh-130px)]">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">Chatbot XNK AI</h1>
        <p className="text-sm text-gray-500">
          Tư vấn mã HS, thuế suất XNK Việt Nam – Trung Quốc · Powered by Ollama
        </p>
      </div>

      {/* Chat window */}
      <div className="flex-1 border rounded-xl bg-gray-50 overflow-y-auto p-4 flex flex-col gap-3 min-h-0">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <div className="text-4xl">🤖</div>
            <p className="text-gray-400 text-center text-sm">
              Hỏi tôi về mã HS, thuế suất, quy trình XNK...
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg mt-2">
              {SUGGESTED.map(s => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="text-left text-xs border rounded-lg px-3 py-2 bg-white hover:bg-blue-50 hover:border-primary transition-colors text-gray-600"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-white text-xs mr-2 mt-0.5 flex-shrink-0">
                AI
              </div>
            )}
            <div
              className={`max-w-[82%] rounded-2xl px-4 py-2.5 text-sm ${
                msg.role === 'user'
                  ? 'bg-primary text-white rounded-tr-sm'
                  : msg.error
                  ? 'bg-red-50 border border-red-200 text-red-700 rounded-tl-sm'
                  : 'bg-white border rounded-tl-sm'
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-100 flex flex-wrap gap-1">
                  {msg.citations.map(code => (
                    <a
                      key={code}
                      href={`/tra-cuu-hs?q=${encodeURIComponent(code)}`}
                      className="font-mono text-xs bg-blue-50 text-primary px-2 py-0.5 rounded hover:bg-blue-100 transition-colors"
                    >
                      {code}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-white text-xs mr-2 mt-0.5 flex-shrink-0">
              AI
            </div>
            <div className="bg-white border rounded-2xl rounded-tl-sm px-4 py-3">
              <TypingDots />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <form onSubmit={handleSubmit} className="flex gap-2 mt-3">
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Nhập câu hỏi về HS code, thuế, quy định XNK..."
          className="flex-1 border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-gray-50"
          disabled={loading}
          autoFocus
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed px-5"
        >
          {loading ? (
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          ) : (
            'Gửi'
          )}
        </button>
      </form>

      {messages.length > 0 && (
        <p className="text-xs text-gray-400 text-center mt-2">
          Session: {sessionId.slice(0, 8)}… ·{' '}
          <button
            className="underline hover:text-gray-600"
            onClick={() => setMessages([])}
          >
            Xoá lịch sử
          </button>
        </p>
      )}
    </div>
  )
}
