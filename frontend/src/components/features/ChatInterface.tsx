import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '../../store';
import { sendMessage, addUserMessage, clearChat } from '../../store/chatSlice';
import { fetchInteractions } from '../../store/interactionSlice';

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

function parseJsonObject(value: unknown): Record<string, unknown> | null {
  if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value);
      if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>;
      }
    } catch {
      // ignore invalid JSON
    }
  }
  return null;
}

function extractJsonFromText(text?: string): Record<string, unknown> | null {
  if (!text || typeof text !== 'string') return null;
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start === -1 || end === -1 || end <= start) return null;

  const candidate = text.slice(start, end + 1);
  return parseJsonObject(candidate);
}

function normalizeExtractedData(data: unknown, fallbackText?: string): Record<string, unknown> | null {
  const parsed = parseJsonObject(data);
  if (parsed) return parsed;
  const fromText = extractJsonFromText(typeof data === 'string' ? data : undefined);
  if (fromText) return fromText;
  if (fallbackText) {
    const parsedFallback = parseJsonObject(fallbackText);
    if (parsedFallback) return parsedFallback;
    return extractJsonFromText(fallbackText);
  }
  return null;
}

function formatValue(value: unknown): string {
  if (typeof value === 'boolean') return value ? '✅ Yes' : '❌ No';
  if (Array.isArray(value)) {
    return value.map((item) => (typeof item === 'object' && item !== null ? JSON.stringify(item) : String(item))).join(', ');
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value);
  }
  return String(value ?? '');
}

function flattenExtractedData(value: unknown, prefix = ''): Array<{ key: string; value: string }> {
  if (Array.isArray(value)) {
    return [{ key: prefix || 'value', value: formatValue(value) }];
  }

  if (typeof value === 'object' && value !== null) {
    return Object.entries(value).flatMap(([key, nested]) =>
      flattenExtractedData(nested, prefix ? `${prefix}.${key}` : key)
    );
  }

  return [{ key: prefix || 'value', value: formatValue(value) }];
}

function ExtractedDataCard({ data, rawText }: { data?: Record<string, unknown>; rawText?: string }) {
  const rawData = data?.extracted_data || data?.insights || data?.follow_up_plan || data?.summary || data;
  const flatData = normalizeExtractedData(rawData, rawText);

  if (!flatData) return null;

  const rows = flattenExtractedData(flatData)
    .filter((row) => row.value !== '')
    .slice(0, 20)
    .map((row) => ({
      key: row.key.replace(/_/g, ' '),
      value: row.value,
    }));

  if (!rows.length) return null;

  return (
    <div className="extracted-card">
      <h4>📊 Extracted CRM Data</h4>
      <table className="extracted-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <td className="extracted-key">{row.key}</td>
              <td className="extracted-val">{row.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface ChatInterfaceProps {
  onExtractedData?: (data: Record<string, unknown>) => void;
  onSuggestionSelected?: (suggestion: string) => void;
  toolLabel?: string;
  toolDescription?: string;
  toolPlaceholder?: string;
}

export default function ChatInterface({
  onExtractedData,
  onSuggestionSelected,
  toolLabel = 'AI Chat',
  toolDescription = 'Use the AI chat to run CRM tools.',
  toolPlaceholder = 'Describe your HCP meeting, ask for insights, or request a follow-up plan...',
}: ChatInterfaceProps) {
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
    const assistantMessage = [...messages].reverse().find((msg) => msg.role === 'assistant');
    if (!assistantMessage || assistantMessage.id === lastProcessedMessage.current) return;

    lastProcessedMessage.current = assistantMessage.id;

    if (assistantMessage.extractedData && Object.keys(assistantMessage.extractedData).length > 0 && onExtractedData) {
      onExtractedData(assistantMessage.extractedData);
    }

    if (assistantMessage.toolUsed && ['log_interaction', 'edit_interaction'].includes(assistantMessage.toolUsed)) {
      dispatch(fetchInteractions());
    }
  }, [messages, onExtractedData, dispatch]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    dispatch(addUserMessage(text));
    dispatch(sendMessage(text));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const useSuggestion = (s: string) => {
    if (onSuggestionSelected) onSuggestionSelected(s);
    setInput(s);
    textareaRef.current?.focus();
    if (!loading) {
      dispatch(addUserMessage(s));
      dispatch(sendMessage(s));
    }
  };

  const formatTime = (ts: string) =>
    new Date(ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-avatar">🤖</div>
        <div className="chat-header-info">
          <h3>PharmaCRM AI Agent</h3>
          <p>● Online · llama-3.1-8b-instant via Groq</p>
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
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <span className="tool-badge">{formatToolName(msg.toolUsed)}</span>
                    {msg.extractedData && Object.keys(msg.extractedData).length > 0 && (
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.06)', padding: '8px 10px', borderRadius: '8px' }}>
                        {msg.toolUsed === 'log_interaction' && 'Structured CRM extraction completed.'}
                        {msg.toolUsed === 'edit_interaction' && 'Interaction update completed.'}
                        {msg.toolUsed === 'generate_follow_up_plan' && 'Follow-up plan generated.'}
                        {msg.toolUsed === 'doctor_insights' && 'Doctor insights generated.'}
                        {msg.toolUsed === 'meeting_summary_generator' && 'Meeting summary generated.'}
                      </div>
                    )}
                  </div>
                )}
                {msg.extractedData && Object.keys(msg.extractedData).length > 0 && (
                  <ExtractedDataCard data={msg.extractedData} rawText={msg.content} />
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

      <div className="chat-tool-banner" style={{ marginBottom: '12px', padding: '12px 14px', borderRadius: '12px', border: '1px solid rgba(124, 92, 252, 0.2)', background: 'rgba(124, 92, 252, 0.08)' }}>
        <div style={{ fontSize: '13px', fontWeight: 700 }}>{toolLabel}</div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>{toolDescription}</div>
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
            placeholder={toolPlaceholder}
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
