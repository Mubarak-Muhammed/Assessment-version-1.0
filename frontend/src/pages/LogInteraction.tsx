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

const flattenExtractedData = (data: Record<string, unknown>): Record<string, unknown> => {
  if (!data || typeof data !== 'object') return {};

  const candidates: Record<string, unknown>[] = [];
  if (typeof data.extracted_data === 'object' && data.extracted_data !== null) candidates.push(data.extracted_data as Record<string, unknown>);
  if (typeof data.data === 'object' && data.data !== null) candidates.push(data.data as Record<string, unknown>);
  if (typeof data.result === 'object' && data.result !== null) candidates.push(data.result as Record<string, unknown>);
  if (data.status && typeof data.status === 'string' && data.message && candidates.length > 0) {
    return candidates[0];
  }

  if (Object.keys(data).some((key) => key.includes('_') || key.match(/doctor|hospital|special|product|objection|competitor|follow/i))) {
    return data;
  }

  for (const value of Object.values(data)) {
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      const nested = flattenExtractedData(value as Record<string, unknown>);
      if (Object.keys(nested).length > 0) return nested;
    }
  }

  return data;
};

const mapExtractedDataToForm = (data: Record<string, unknown>): Partial<Omit<Interaction, 'id'>> => {
  const extracted: Partial<Omit<Interaction, 'id'>> = {};
  const normalized = flattenExtractedData(data);

  const setIfPresent = (key: string, field: keyof Omit<Interaction, 'id'>) => {
    if (normalized[key] !== undefined && normalized[key] !== null) {
      const value = normalizeValue(normalized[key]);
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
  setIfPresent('physician_name', 'hcp_name');
  setIfPresent('hospital', 'hospital');
  setIfPresent('clinic', 'hospital');
  setIfPresent('hospital_name', 'hospital');
  setIfPresent('facility', 'hospital');
  setIfPresent('specialty', 'specialization');
  setIfPresent('specialization', 'specialization');
  setIfPresent('doctor_specialty', 'specialization');
  setIfPresent('interaction_date', 'interaction_date');
  setIfPresent('date', 'interaction_date');
  setIfPresent('visit_date', 'interaction_date');
  setIfPresent('meeting_date', 'interaction_date');
  setIfPresent('meeting_type', 'meeting_type');
  setIfPresent('visit_type', 'meeting_type');
  setIfPresent('meeting_format', 'meeting_type');
  setIfPresent('visit_duration', 'visit_duration');
  setIfPresent('duration', 'visit_duration');
  setIfPresent('meeting_duration', 'visit_duration');
  setIfPresent('discussion_topics', 'discussion_topics');
  setIfPresent('topics', 'discussion_topics');
  setIfPresent('conversation_points', 'discussion_topics');
  setIfPresent('products_discussed', 'products_discussed');
  setIfPresent('products', 'products_discussed');
  setIfPresent('drugs', 'products_discussed');
  setIfPresent('medications', 'products_discussed');
  setIfPresent('objections', 'objections');
  setIfPresent('objection', 'objections');
  setIfPresent('concerns', 'objections');
  setIfPresent('competitor_mentioned', 'competitor_mentioned');
  setIfPresent('competitor', 'competitor_mentioned');
  setIfPresent('competitor_product', 'competitor_mentioned');
  setIfPresent('notes', 'notes');
  setIfPresent('summary', 'notes');
  setIfPresent('meeting_summary', 'notes');
  setIfPresent('follow_up_required', 'follow_up_required');
  setIfPresent('follow_up_date', 'follow_up_date');
  setIfPresent('next_visit_date', 'follow_up_date');
  setIfPresent('follow_up', 'follow_up_required');
  setIfPresent('follow_up_plan', 'notes');
  setIfPresent('confidence_score', 'confidence_score');

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
