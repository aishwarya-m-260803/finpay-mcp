import { useRef, useState } from 'react'

const EXAMPLE_QUESTIONS = [
  "What is Arjun Sharma's account balance?",
  "Show total transaction summary for account 1",
  "Find recent debit transactions over ₹5,000",
  "List all transactions for merchant Swiggy",
]

const CHAT_API_URL = '/api/chat/'
const FALLBACK_CHAT_API_URL = 'http://127.0.0.1:8000/api/chat/'

export default function App() {
  const [inputQuery, setInputQuery] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)

  const handleQuerySubmit = async (queryText) => {
    const trimmed = queryText.trim()
    if (!trimmed || loading) return

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: trimmed,
    }

    setMessages((prev) => [...prev, userMessage])
    setInputQuery('')
    setLoading(true)

    try {
      let res
      const payload = { message: trimmed }
      try {
        res = await fetch(CHAT_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
      } catch (err) {
        res = await fetch(FALLBACK_CHAT_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
      }

      const json = await res.json()
      const responseText = json.response || json.error || 'No response received.'

      const assistantMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: responseText,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      console.error('API execution error:', err)
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          text: 'Sorry, I encountered an error querying your financial data.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleQuerySubmit(inputQuery)
    }
  }

  const handleExampleClick = (question) => {
    setInputQuery(question)
    handleQuerySubmit(question)
  }

  return (
    <>
      {/* Navigation Header */}
      <header>
        <div className="brand">
          <div className="brand-logo">FP</div>
          <div className="brand-title">
            Fin<span>Pay</span>
          </div>
        </div>
        <div className="user-pill">
          <span className="status-dot"></span>
          <span>Arjun Sharma</span>
        </div>
      </header>

      <main>
        {/* Centered Hero Section */}
        <div className="hero">
          <div className="hero-badge">✨ AI Financial Assistant</div>
          <h1>Ask FinPay Anything</h1>
          <p>
            FinPay is an AI-powered financial assistant that lets you query your financial data using natural language.
          </p>
        </div>

        {/* Chat Input Card */}
        <div className="input-card">
          <form
            className="input-form"
            onSubmit={(e) => {
              e.preventDefault()
              handleQuerySubmit(inputQuery)
            }}
          >
            <textarea
              ref={inputRef}
              className="chat-input"
              rows={2}
              placeholder="Ask FinPay anything about your financial data..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              type="submit"
              className="send-btn"
              disabled={!inputQuery.trim() || loading}
              title="Send question"
            >
              <svg viewBox="0 0 24 24">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            </button>
          </form>
        </div>

        {/* Clickable Example Questions */}
        <div className="examples-section">
          <div className="examples-title">Suggested Questions</div>
          <div className="examples-grid">
            {EXAMPLE_QUESTIONS.map((question, idx) => (
              <button
                key={idx}
                className="example-chip"
                onClick={() => handleExampleClick(question)}
              >
                {question}
              </button>
            ))}
          </div>
        </div>

        {/* Message Stream */}
        {messages.length > 0 && (
          <div className="messages-list">
            {messages.map((msg) => (
              <div key={msg.id} className={`message-item ${msg.sender}`}>
                <div className="avatar">
                  {msg.sender === 'user' ? 'AS' : 'AI'}
                </div>
                <div className="bubble">{msg.text}</div>
              </div>
            ))}

            {loading && (
              <div className="message-item assistant">
                <div className="avatar">AI</div>
                <div className="bubble loading-bubble">
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      <footer>
        &copy; 2026 FinPay Platform. Premium Emerald Banking Theme.
      </footer>
    </>
  )
}
