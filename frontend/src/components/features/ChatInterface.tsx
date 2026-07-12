import { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '../../store';
import { sendMessage, addUserMessage, clearChat } from '../../store/chatSlice';

const SUGGESTIONS = [
  "I met Dr. Priya Sharma at Fortis Hospital today to discuss Cardivex 10mg",
  "Get doctor insights for Dr. Rajesh Kumar, Cardiologist",
  "Generate a follow-up plan for my last meeting with Dr. Mehta",
  "Summarize my notes: Met Dr. Singh, discussed side effects of Statinex, he showed interest",
  "Edit interaction abc123: update sentiment to positive",
];

function formatToolName(tool: string) {
  const map: Record<string, string> = {
    log_interaction: '🔬 Log Interaction',
    edit_interaction: '✏️ Edit Interaction',
    generate_follow_up_plan: '📅 Follow-Up Plan',
    doctor_insights: '👨‍⚕️ Doctor Insights',
    meeting_summary_generator: '📝 Meeting Summary',
  };
  return map[tool] || tool;
}

function ExtractedDataCard({ data }: { data: Record<string, unknown> }) {
  const flat = data?.extracted_data || data?.insights || data?.follow_up_plan || data?.summary || data;
  if (!flat || typeof flat !== 'object') return null;

  return (
    <div className="extracted-card">
      <h4>📊 Extracted CRM Data</h4>
      {Object.entries(flat as Record<string, unknown>)
        .filter(([, v]) => v !== null && v !== undefined && v !== '')
        .slice(0, 10)
        .map(([k, v]) => (
          <div key={k} className="extracted-row">
            <span className="extracted-key">{k.replace(/_/g, ' ')}</span>
            <span className="extracted-val">
              {typeof v === 'boolean' ? (v ? '✅ Yes' : '❌ No')
               : Array.isArray(v) ? v.join(', ')
               : String(v)}
            </span>
          </div>
        ))}
    </div>
  );
}

interface ChatInterfaceProps {
  onExtractedData?: (data: Record<string, unknown>) => void;
}

export default function ChatInterface({ onExtractedData }: ChatInterfaceProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { messages, loading } = useSelector((s: RootState) => s.chat);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lastProcessedMessage = useRef<string>('');

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (!onExtractedData) return;
    const assistantMessage = [...messages].reverse().find((msg) => msg.role === 'assistant' && msg.extractedData && Object.keys(msg.extractedData).length > 0);
    if (assistantMessage && assistantMessage.id !== lastProcessedMessage.current) {
      lastProcessedMessage.current = assistantMessage.id;
      onExtractedData(assistantMessage.extractedData!);
    }
  }, [messages, onExtractedData]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    dispatch(addUserMessage(text));
    dispatch(sendMessage(text));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const useSuggestion = (s: string) => { setInput(s); textareaRef.current?.focus(); };

  const formatTime = (ts: string) =>
    new Date(ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-avatar">🤖</div>
        <div className="chat-header-info">
          <h3>PharmaCRM AI Agent</h3>
          <p>● Online · gemma2-9b-it via Groq</p>
        </div>
        <button className="btn btn-ghost btn-sm" style={{ marginLeft: 'auto' }}
          onClick={() => dispatch(clearChat())} title="Clear chat">
          🗑️
        </button>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <div className="welcome-icon">🤖</div>
            <h3>Hello! I'm your CRM AI Assistant</h3>
            <p>I can help you log HCP interactions, generate follow-up plans,<br />
               get doctor insights, and summarize your meeting notes.<br />
               Try one of these prompts to get started:</p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} className="suggestion-chip" onClick={() => useSuggestion(s)}>
                  {s.length > 70 ? s.substring(0, 70) + '...' : s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`message-bubble ${msg.role}`}>
              <div className={`message-avatar ${msg.role}`}>
                {msg.role === 'user' ? 'AC' : '🤖'}
              </div>
              <div className="message-content">
                <div className="message-text" style={{ whiteSpace: 'pre-wrap' }}>
                  {msg.content}
                </div>
                {msg.toolUsed && (
                  <span className="tool-badge">{formatToolName(msg.toolUsed)}</span>
                )}
                {msg.extractedData && Object.keys(msg.extractedData).length > 0 && (
                  <ExtractedDataCard data={msg.extractedData} />
                )}
                <span className="message-time">{formatTime(msg.timestamp)}</span>
              </div>
            </div>
          ))
        )}

        {/* Typing indicator */}
        {loading && (
          <div className="message-bubble assistant">
            <div className="message-avatar assistant">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <div className="chat-input-row">
          <textarea
            ref={textareaRef}
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your HCP meeting, ask for insights, or request a follow-up plan..."
            rows={1}
            disabled={loading}
          />
          <button className="chat-send-btn" onClick={handleSend} disabled={loading || !input.trim()}>
            {loading ? <span className="spinner" style={{ width: 18, height: 18 }} /> : '➤'}
          </button>
        </div>
        <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>
          Press Enter to send · Shift+Enter for new line · Powered by LangGraph + Groq
        </p>
      </div>
    </div>
  );
}
