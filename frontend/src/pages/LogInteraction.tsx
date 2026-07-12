import { useState } from 'react';
import LogForm, { defaultInteractionForm } from '../components/features/LogForm';
import ChatInterface from '../components/features/ChatInterface';
import type { Interaction } from '../types';

const normalizeValue = (value: unknown): string => {
  if (value == null) return '';
  if (Array.isArray(value)) return value.map(String).join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
};

const mapExtractedDataToForm = (data: Record<string, unknown>): Partial<Omit<Interaction, 'id'>> => {
  const extracted: Partial<Omit<Interaction, 'id'>> = {};

  const setIfPresent = (key: string, field: keyof Omit<Interaction, 'id'>) => {
    if (data[key] !== undefined && data[key] !== null) {
      const value = normalizeValue(data[key]);
      if (field === 'visit_duration') {
        const parsed = Number(value.toString().replace(/[^0-9]/g, ''));
        extracted[field] = Number.isFinite(parsed) ? parsed : undefined;
      } else if (field === 'follow_up_required') {
        extracted[field] = ['yes', 'true', 'required', 'needed'].includes(value.toLowerCase());
      } else {
        extracted[field] = value as any;
      }
    }
  };

  setIfPresent('doctor_name', 'hcp_name');
  setIfPresent('hcp_name', 'hcp_name');
  setIfPresent('doctor', 'hcp_name');
  setIfPresent('hospital', 'hospital');
  setIfPresent('clinic', 'hospital');
  setIfPresent('specialty', 'specialization');
  setIfPresent('specialization', 'specialization');
  setIfPresent('interaction_date', 'interaction_date');
  setIfPresent('date', 'interaction_date');
  setIfPresent('meeting_type', 'meeting_type');
  setIfPresent('visit_duration', 'visit_duration');
  setIfPresent('duration', 'visit_duration');
  setIfPresent('discussion_topics', 'discussion_topics');
  setIfPresent('topics', 'discussion_topics');
  setIfPresent('products_discussed', 'products_discussed');
  setIfPresent('products', 'products_discussed');
  setIfPresent('objections', 'objections');
  setIfPresent('objection', 'objections');
  setIfPresent('competitor_mentioned', 'competitor_mentioned');
  setIfPresent('competitor', 'competitor_mentioned');
  setIfPresent('notes', 'notes');
  setIfPresent('summary', 'notes');
  setIfPresent('sentiment', 'sentiment');
  setIfPresent('follow_up_required', 'follow_up_required');
  setIfPresent('follow_up_date', 'follow_up_date');
  setIfPresent('follow_up_plan', 'notes');

  return extracted;
};

export default function LogInteraction() {
  const [form, setForm] = useState<Omit<Interaction, 'id'>>(defaultInteractionForm);

  const handleExtractedData = (data: Record<string, unknown>) => {
    const mapped = mapExtractedDataToForm(data);
    if (Object.keys(mapped).length > 0) {
      setForm((prev) => ({ ...prev, ...mapped }));
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Log HCP Interaction</h1>
          <p>Record a new interaction with a Healthcare Professional. Use the AI chat on the right to auto-fill the form on the left.</p>
        </div>
      </div>

      <div className="page-split">
        <div className="left-panel">
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '4px' }}>
              📋 New Interaction Entry
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Enter notes or use AI chat to auto-populate fields. Required fields are marked with <span style={{ color: 'var(--accent-danger)' }}>*</span>.
            </p>
          </div>
          <LogForm form={form} setForm={setForm} />
        </div>

        <div className="right-panel">
          <div style={{ marginBottom: '16px', padding: '16px 20px', background: 'rgba(79,142,247,0.06)', borderRadius: '14px', border: '1px solid rgba(79,142,247,0.15)' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              💡 Type your meeting notes, objectives, or follow-up request on the right. The AI will extract structured CRM fields and fill the form automatically on the left.
            </p>
          </div>
          <ChatInterface onExtractedData={handleExtractedData} />
        </div>
      </div>
    </div>
  );
}
