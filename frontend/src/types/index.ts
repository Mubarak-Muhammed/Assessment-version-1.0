export interface Interaction {
  id: string;
  hcp_name: string;
  hospital: string;
  specialization?: string;
  interaction_date: string;
  interaction_time?: string;
  meeting_type: string;
  attendees?: string;
  visit_duration?: number;
  discussion_topics?: string;
  products_discussed?: string;
  objections?: string;
  competitor_mentioned?: string;
  materials_shared?: string;
  samples_distributed?: string;
  outcomes?: string;
  follow_up_actions?: string;
  follow_up_required: boolean;
  follow_up_date?: string;
  notes?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  confidence_score?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  toolUsed?: string;
  extractedData?: Record<string, unknown>;
}

export interface AgentResponse {
  response: string;
  extracted_data?: Record<string, unknown>;
  tool_used?: string;
}

export type TabMode = 'form' | 'chat';
