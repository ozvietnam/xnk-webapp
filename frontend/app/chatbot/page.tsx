'use client'

import { useState } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: string[]
}

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMsg: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chatbot/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }),
      })
      const data = await res.json()
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: data.answer, citations: data.citations },
      ])
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-6">Chatbot XNK AI</h1>
      <div className="border rounded-lg h-[500px] overflow-y-auto p-4 mb-4 bg-gray-50 flex flex-col gap-3">
        {messages.length === 0 && (
          <p className="text-gray-400 text-center mt-8">
            Hỏi tôi về HS code, thuế suất, quy trình XNK...
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === 'user' ? 'bg-primary text-white' : 'bg-white border'
              }`}
            >
              <p>{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <p className="text-xs mt-1 opacity-70">Mã HS: {msg.citations.join(', ')}</p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-lg px-4 py-2">
              <span className="animate-pulse">Đang xử lý...</span>
            </div>
          </div>
        )}
      </div>
      <form onSubmit={sendMessage} className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Hỏi về HS code, thuế, quy định XNK..."
          className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          Gửi
        </button>
      </form>
    </div>
  )
}
