export const BACKEND_URL = (
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  (process.env.NODE_ENV === 'production'
    ? 'https://jansahayak-ai-qyjd.onrender.com'
    : 'http://localhost:8000')
).replace(/\/+$/, '');

// Types matching the backend Pydantic models
export type Language = 'en' | 'hi' | 'te';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface SourceCitation {
  title: string;
  url?: string;
  source_type: string;
  page_number?: number;
  section?: string;
  retrieved_at?: string;
  is_verified: boolean;
}

export interface ChatResponse {
  answer: string;
  language: Language;
  sources: SourceCitation[];
  agent_steps: string[];
  has_audio: boolean;
  audio_url?: string;
  suggested_questions: string[];
  eligibility_data?: Record<string, unknown>;
  session_id: string;
}

export interface GovernmentScheme {
  id: string;
  name: string;
  name_hindi?: string;
  name_telugu?: string;
  description: string;
  ministry?: string;
  state?: string;
  beneficiary_types: string[];
  benefits: string[];
  eligibility_criteria: string[];
  required_documents: string[];
  application_url?: string;
  official_url: string;
  source: string;
  last_verified?: string;
  category?: string;
}

export interface SchemeSearchResponse {
  schemes: GovernmentScheme[];
  total: number;
  source: string;
  retrieved_at: string;
  warning?: string;
}

export interface EligibilityProfile {
  age?: number;
  state?: string;
  occupation?: string;
  annual_income?: number;
  is_student?: boolean;
  is_employed?: boolean;
  gender?: string;
  category?: string;
  additional_info?: Record<string, unknown>;
}

export interface EligibilityResult {
  scheme: GovernmentScheme;
  status: 'likely_eligible' | 'possibly_eligible' | 'not_eligible' | 'insufficient_info';
  satisfied_conditions: string[];
  unsatisfied_conditions: string[];
  missing_information: string[];
  required_documents: string[];
  application_steps: string[];
  official_link?: string;
  disclaimer: string;
  sources: SourceCitation[];
}

export interface DocumentUploadResponse {
  document_id: string;
  access_token?: string;
  filename: string;
  page_count: number;
  extracted_text_preview: string;
  key_clauses: string[];
  important_dates: string[];
  eligibility_mentions: string[];
  required_documents_mentioned: string[];
  language_detected: string;
  processing_notes: string[];
  is_scanned?: boolean;
  document_type?: string;
}

// API functions
export const api = {
  chat: async (
    message: string,
    language: Language,
    history: ChatMessage[],
    sessionId?: string,
    documentId?: string,
    documentAccessToken?: string,
    userProfile?: Record<string, unknown>
  ): Promise<ChatResponse> => {
    const res = await fetch(`${BACKEND_URL}/api/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        language,
        conversation_history: history,
        session_id: sessionId,
        document_id: documentId,
        document_access_token: documentAccessToken,
        user_profile: userProfile,
        include_audio: false,
      }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Chat request failed: ${res.statusText}`);
    }
    return res.json();
  },

  searchSchemes: async (
    query: string,
    state?: string,
    category?: string,
    language: Language = 'en',
    beneficiaryType?: string,
    signal?: AbortSignal
  ): Promise<SchemeSearchResponse> => {
    const res = await fetch(`${BACKEND_URL}/api/schemes/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, state, category, beneficiary_type: beneficiaryType, language }),
      signal,
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Scheme search failed: ${res.statusText}`);
    }
    return res.json();
  },

  getStates: async (): Promise<string[]> => {
    const res = await fetch(`${BACKEND_URL}/api/schemes/states/list`);
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Failed to fetch states: ${res.statusText}`);
    }
    const data = await res.json();
    const raw = data.states || [];
    return raw.map((s: any) => (typeof s === "string" ? s : s.name || ""));
  },

  getCategories: async (): Promise<string[]> => {
    const res = await fetch(`${BACKEND_URL}/api/schemes/categories/list`);
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Failed to fetch categories: ${res.statusText}`);
    }
    const data = await res.json();
    const raw = data.categories || [];
    return raw.map((c: any) => (typeof c === "string" ? c : c.name || ""));
  },

  checkEligibility: async (
    profile: EligibilityProfile,
    schemeQuery: string,
    language: Language
  ): Promise<EligibilityResult[]> => {
    const res = await fetch(
      `${BACKEND_URL}/api/eligibility/check?scheme_query=${encodeURIComponent(schemeQuery)}&language=${language}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      }
    );
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Eligibility check failed: ${res.statusText}`);
    }
    return res.json();
  },

  uploadDocument: async (file: File): Promise<DocumentUploadResponse> => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BACKEND_URL}/api/documents/upload`, {
      method: 'POST',
      body: form,
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Document upload failed: ${res.statusText}`);
    }
    return res.json();
  },

  queryDocument: async (
    documentId: string,
    accessToken: string,
    question: string,
    language: Language
  ): Promise<{ answer: string; sources: SourceCitation[]; language: Language }> => {
    const res = await fetch(`${BACKEND_URL}/api/documents/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId, access_token: accessToken, question, language }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Document query failed: ${res.statusText}`);
    }
    return res.json();
  },

  deleteDocument: async (documentId: string, accessToken: string): Promise<void> => {
    const res = await fetch(`${BACKEND_URL}/api/documents/${encodeURIComponent(documentId)}`, {
      method: 'DELETE',
      headers: { 'X-Document-Token': accessToken },
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Document deletion failed: ${res.statusText}`);
    }
  },

  synthesizeSpeech: async (text: string, language: Language): Promise<{ audio_url: string }> => {
    const res = await fetch(`${BACKEND_URL}/api/voice/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Voice synthesis failed: ${res.statusText}`);
    }
    return res.json();
  },

  healthCheck: async (): Promise<{ status: string }> => {
    const res = await fetch(`${BACKEND_URL}/health`);
    if (!res.ok) throw new Error('Backend unavailable');
    return res.json();
  },

  deleteChatSession: async (sessionId: string): Promise<void> => {
    const res = await fetch(`${BACKEND_URL}/api/chat/session/${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
    });
    if (!res.ok && res.status !== 404) {
      throw new Error(`Could not clear the server conversation (${res.status}).`);
    }
  },
};
