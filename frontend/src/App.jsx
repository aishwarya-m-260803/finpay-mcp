import { useRef, useState } from 'react'

const EXAMPLE_QUESTIONS = [
  "What is Arjun Sharma's account balance?",
  "Show total transaction summary for account 1",
  "Find recent debit transactions over ₹5,000",
  "List all transactions for merchant Swiggy",
]

const CHAT_API_URL = '/api/chat/'
const FALLBACK_CHAT_API_URL = 'http://127.0.0.1:8000/api/chat/'

function parseInline(text) {
  if (!text) return null
  const regex = /(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*|`.*?`)/g
  const parts = []
  let lastIdx = 0
  let match

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.substring(lastIdx, match.index))
    }
    const token = match[0]
    if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(<code key={match.index}>{token.slice(1, -1)}</code>)
    } else if (token.startsWith('***') && token.endsWith('***')) {
      parts.push(<strong key={match.index}><em>{token.slice(3, -3)}</em></strong>)
    } else if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(<strong key={match.index}>{token.slice(2, -2)}</strong>)
    } else if (token.startsWith('*') && token.endsWith('*')) {
      parts.push(<em key={match.index}>{token.slice(1, -1)}</em>)
    } else {
      parts.push(token)
    }
    lastIdx = regex.lastIndex
  }

  if (lastIdx < text.length) {
    parts.push(text.substring(lastIdx))
  }

  return parts.length === 1 ? parts[0] : parts
}

function FormattedText({ content }) {
  if (!content) return null

  const lines = content.split('\n')
  const elements = []
  let listItems = []

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}-${Math.random()}`}>
          {listItems.map((item, idx) => (
            <li key={idx}>{parseInline(item)}</li>
          ))}
        </ul>
      )
      listItems = []
    }
  }

  lines.forEach((line, index) => {
    const trimmed = line.trim()
    if (!trimmed) {
      flushList()
      return
    }

    if (trimmed.startsWith('### ')) {
      flushList()
      elements.push(<h4 key={`h4-${index}`}>{parseInline(trimmed.replace(/^###\s+/, ''))}</h4>)
    } else if (trimmed.startsWith('## ')) {
      flushList()
      elements.push(<h3 key={`h3-${index}`}>{parseInline(trimmed.replace(/^##\s+/, ''))}</h3>)
    } else if (trimmed.startsWith('# ')) {
      flushList()
      elements.push(<h2 key={`h2-${index}`}>{parseInline(trimmed.replace(/^#\s+/, ''))}</h2>)
    } else if (/^(\*+|-|•)\s+/.test(trimmed) || /^\*\*\*/.test(trimmed)) {
      let itemText = trimmed
      if (/^(\*+|-|•)\s+/.test(trimmed)) {
        itemText = trimmed.replace(/^(\*+|-|•)\s+/, '')
      } else if (/^\*\*\*/.test(trimmed)) {
        itemText = trimmed.replace(/^\*\*\*/, '**')
      }
      listItems.push(itemText)
    } else if (/^\d+\.\s+/.test(trimmed)) {
      listItems.push(trimmed.replace(/^\d+\.\s+/, ''))
    } else {
      flushList()
      elements.push(<p key={`p-${index}`}>{parseInline(trimmed)}</p>)
    }
  })

  flushList()

  return <div className="formatted-markdown">{elements}</div>
}

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

    const historyPayload = messages
      .filter((msg) => !msg.errorCategory && (msg.sender === 'user' || msg.sender === 'assistant'))
      .map((msg) => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text,
      }))

    setMessages((prev) => [...prev, userMessage])
    setInputQuery('')
    setLoading(true)

    try {
      let res
      const payload = {
        message: trimmed,
        history: historyPayload,
      }
      try {
        res = await fetch(CHAT_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
      } catch (err) {
        res = await fetch(FALLBACK_CHAT_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
      }


      const json = await res.json().catch(() => ({}))
      if (!res.ok || json.success === false) {
        // Backend returns structured: {success, error_type, message, details, category}
        const errorObj = new Error(json.message || json.error || `Server error (${res.status})`)
        errorObj.category = json.category || 'unhandled'
        errorObj.errorType = json.error_type || 'UnknownError'
        errorObj.details = json.details || ''
        throw errorObj
      }

      const responseText = json.response || 'No response received.'

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
          text: err.message || 'Sorry, I encountered an error querying your financial data.',
          errorCategory: err.category || 'unhandled',
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
                  {msg.sender === 'user' ? 'AS' : msg.errorCategory ? '⚠' : 'AI'}
                </div>
                <div className={`bubble${msg.errorCategory ? ` error-bubble error-${msg.errorCategory}` : ''}`}>
                  {msg.sender === 'assistant' ? (
                    <FormattedText content={msg.text} />
                  ) : (
                    msg.text
                  )}
                </div>
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
