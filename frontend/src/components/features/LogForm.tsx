import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '../../store';
import { createInteraction } from '../../store/interactionSlice';
import { showToast } from '../../store/uiSlice';
import type { Interaction } from '../../types';

const MEETING_TYPES = ['In-person Visit', 'Virtual Call', 'Conference', 'Workshop', 'Pharmacy Visit', 'Hospital Round'];
const SPECIALIZATIONS = ['Cardiology', 'Oncology', 'Neurology', 'Gastroenterology', 'Endocrinology', 'Pulmonology', 'Nephrology', 'Rheumatology', 'General Practice', 'Other'];

export const defaultInteractionForm: Omit<Interaction, 'id'> = {
  hcp_name: '',
  hospital: '',
  specialization: '',
  interaction_date: new Date().toISOString().split('T')[0],
  interaction_time: '',
  meeting_type: 'In-person Visit',
  attendees: '',
  visit_duration: 30,
  discussion_topics: '',
  products_discussed: '',
  objections: '',
  competitor_mentioned: '',
  materials_shared: '',
  samples_distributed: '',
  outcomes: '',
  follow_up_actions: '',
  follow_up_required: false,
  follow_up_date: '',
  notes: '',
  sentiment: 'neutral',
  confidence_score: 1.0,
};

interface LogFormProps {
  form?: Omit<Interaction, 'id'>;
  setForm?: React.Dispatch<React.SetStateAction<Omit<Interaction, 'id'>>>;
}

export default function LogForm({ form: formProp, setForm: setFormProp }: LogFormProps = {}) {
  const dispatch = useDispatch<AppDispatch>();
  const { loading } = useSelector((s: RootState) => s.interaction);
  const [internalForm, setInternalForm] = useState<Omit<Interaction, 'id'>>(defaultInteractionForm);
  const form = formProp ?? internalForm;
  const setForm = setFormProp ?? setInternalForm;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked
               : type === 'number' ? Number(value)
               : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.hcp_name || !form.hospital || !form.interaction_date) {
      dispatch(showToast({ message: 'Please fill in all required fields.', type: 'error' }));
      return;
    }
    try {
      await dispatch(createInteraction(form)).unwrap();
      dispatch(showToast({ message: '✅ Interaction logged successfully!', type: 'success' }));
      setForm(defaultInteractionForm);
    } catch (err) {
      dispatch(showToast({ message: `Failed to log interaction: ${err}`, type: 'error' }));
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* ── HCP Details ── */}
      <div className="section-title">👨‍⚕️ HCP Details</div>
      <div className="form-grid" style={{ marginBottom: '20px' }}>
        <div className="form-group">
          <label className="form-label">Doctor Name <span className="required">*</span></label>
          <input className="form-input" name="hcp_name" value={form.hcp_name}
            onChange={handleChange} placeholder="Dr. Anjali Mehta" required />
        </div>
        <div className="form-group">
          <label className="form-label">Hospital / Clinic <span className="required">*</span></label>
          <input className="form-input" name="hospital" value={form.hospital}
            onChange={handleChange} placeholder="Apollo Hospitals, Mumbai" required />
        </div>
        <div className="form-group">
          <label className="form-label">Specialization</label>
          <select className="form-select" name="specialization" value={form.specialization} onChange={handleChange}>
            <option value="">Select specialty...</option>
            {SPECIALIZATIONS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Interaction Date <span className="required">*</span></label>
          <input className="form-input" type="date" name="interaction_date"
            value={form.interaction_date} onChange={handleChange} required />
        </div>
        <div className="form-group">
          <label className="form-label">Interaction Time</label>
          <input className="form-input" type="time" name="interaction_time"
            value={form.interaction_time ?? ''} onChange={handleChange} />
        </div>
        <div className="form-group">
          <label className="form-label">Attendees</label>
          <input className="form-input" name="attendees" value={form.attendees ?? ''}
            onChange={handleChange} placeholder="Enter names or search..." />
        </div>
      </div>

      {/* ── Meeting Details ── */}
      <div className="section-title">📅 Meeting Details</div>
      <div className="form-grid" style={{ marginBottom: '20px' }}>
        <div className="form-group">
          <label className="form-label">Meeting Type</label>
          <select className="form-select" name="meeting_type" value={form.meeting_type} onChange={handleChange}>
            {MEETING_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Visit Duration (minutes)</label>
          <input className="form-input" type="number" name="visit_duration"
            value={form.visit_duration ?? ''} onChange={handleChange} min={5} max={240} placeholder="30" />
        </div>
        <div className="form-group form-full">
          <label className="form-label">Discussion Topics</label>
          <input className="form-input" name="discussion_topics" value={form.discussion_topics ?? ''}
            onChange={handleChange} placeholder="e.g. New drug efficacy data, patient adherence" />
        </div>
        <div className="form-group form-full">
          <label className="form-label">Products Discussed</label>
          <input className="form-input" name="products_discussed" value={form.products_discussed ?? ''}
            onChange={handleChange} placeholder="e.g. Cardivex 10mg, Statinex Plus" />
        </div>
      </div>
      <div className="section-title">📦 Materials & Outcomes</div>
      <div className="form-grid" style={{ marginBottom: '20px' }}>
        <div className="form-group form-full">
          <label className="form-label">Materials Shared / Samples Distributed</label>
          <textarea className="form-textarea" name="materials_shared" value={form.materials_shared ?? ''}
            onChange={handleChange} placeholder="List materials or samples shared during the meeting" />
        </div>
        <div className="form-group form-full">
          <label className="form-label">Samples Distributed</label>
          <input className="form-input" name="samples_distributed" value={form.samples_distributed ?? ''}
            onChange={handleChange} placeholder="Enter sample names or counts" />
        </div>
        <div className="form-group form-full">
          <label className="form-label">Outcomes</label>
          <textarea className="form-textarea" name="outcomes" value={form.outcomes ?? ''}
            onChange={handleChange} placeholder="Key outcomes or agreements..." />
        </div>
        <div className="form-group form-full">
          <label className="form-label">Follow-up Actions</label>
          <textarea className="form-textarea" name="follow_up_actions" value={form.follow_up_actions ?? ''}
            onChange={handleChange} placeholder="Enter next steps or tasks..." />
        </div>
      </div>

      {/* ── Insights ── */}
      <div className="section-title">💡 Insights & Feedback</div>
      <div className="form-grid" style={{ marginBottom: '20px' }}>
        <div className="form-group">
          <label className="form-label">Objections Raised</label>
          <textarea className="form-textarea" name="objections" value={form.objections ?? ''}
            onChange={handleChange} placeholder="Doctor expressed concerns about side effects..." />
        </div>
        <div className="form-group">
          <label className="form-label">Competitor Mentioned</label>
          <input className="form-input" name="competitor_mentioned" value={form.competitor_mentioned ?? ''}
            onChange={handleChange} placeholder="e.g. MediCorp Cardio-X" />
        </div>
        <div className="form-group">
          <label className="form-label">Meeting Sentiment</label>
          <select className="form-select" name="sentiment" value={form.sentiment ?? 'neutral'} onChange={handleChange}>
            <option value="positive">😊 Positive</option>
            <option value="neutral">😐 Neutral</option>
            <option value="negative">😟 Negative</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Notes / Observations</label>
          <textarea className="form-textarea" name="notes" value={form.notes ?? ''}
            onChange={handleChange} placeholder="Doctor showed interest in the new clinical trial data..." />
        </div>
      </div>

      {/* ── Follow-Up ── */}
      <div className="section-title">🔔 Follow-Up</div>
      <div className="form-grid" style={{ marginBottom: '28px' }}>
        <div className="form-group form-full">
          <div className="form-checkbox-group">
            <input className="form-checkbox" type="checkbox" id="follow_up_required"
              name="follow_up_required" checked={form.follow_up_required} onChange={handleChange} />
            <label className="form-checkbox-label" htmlFor="follow_up_required">
              Follow-up required after this interaction
            </label>
          </div>
        </div>
        {form.follow_up_required && (
          <div className="form-group">
            <label className="form-label">Follow-Up Date</label>
            <input className="form-input" type="date" name="follow_up_date"
              value={form.follow_up_date ?? ''} onChange={handleChange} />
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
        <button type="button" className="btn btn-secondary" onClick={() => setForm(defaultInteractionForm)}>
          🔄 Reset
        </button>
        <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
          {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Saving...</> : '💾 Log Interaction'}
        </button>
      </div>
    </form>
  );
}
