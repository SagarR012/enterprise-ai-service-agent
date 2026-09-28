// ── Auth ────────────────────────────────────────────────────────────
export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  name: string;
  role: string;
  workspace_id: string;
}

export interface UserInfo {
  id: string;
  name: string;
  email: string;
  role: string;
  workspace_id: string;
}

// ── Documents ───────────────────────────────────────────────────────
export interface DocumentOut {
  id: string;
  filename: string;
  workspace_id: string;
  uploader_id: string;
  sensitivity_level: string;
  upload_date: string;
  chunk_count: number;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  chunks_created: number;
  pii_detected: boolean;
  sensitivity_level: string;
}

// ── Chat ────────────────────────────────────────────────────────────
export interface Citation {
  chunk_id: string;
  source_name: string;
  relevance_score: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  pii_masked: boolean;
  rbac_blocked: boolean;
  conversation_id: string;
  withheld_notice: string | null;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  cited_chunks: Citation[];
  created_at: string;
}

export interface Conversation {
  id: string;
  created_at: string;
  message_count: number;
  messages?: Message[];
}

// ── Admin ───────────────────────────────────────────────────────────
export interface AuditLog {
  id: string;
  user_id: string;
  query_text: string;
  chunks_retrieved: any[];
  pii_masked: boolean;
  rbac_blocked: boolean;
  role_used: string;
  timestamp: string;
}

export interface AdminStats {
  total_queries: number;
  pii_redacted_count: number;
  rbac_blocked_count: number;
  documents_indexed: number;
  total_chunks: number;
  recent_logs: AuditLog[];
}

// ── Demo Users ──────────────────────────────────────────────────────
export interface DemoUser {
  id: string;
  name: string;
  email: string;
  role: string;
  workspace_id: string;
}
