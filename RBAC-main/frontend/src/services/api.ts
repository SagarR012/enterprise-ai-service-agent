import type {
  LoginRequest,
  TokenResponse,
  UserInfo,
  DocumentOut,
  DocumentUploadResponse,
  ChatResponse,
  Conversation,
  AdminStats,
  AuditLog,
  DemoUser,
} from '../types';

const BASE = '';

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...opts, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Auth ────────────────────────────────────────────────────────────
export const auth = {
  login: (data: LoginRequest) =>
    request<TokenResponse>('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  me: () => request<UserInfo>('/api/auth/me'),

  switchUser: (userId: string) =>
    request<TokenResponse>('/api/auth/switch-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId }),
    }),

  demoUsers: () => request<DemoUser[]>('/api/demo/users'),
};

// ── Documents ───────────────────────────────────────────────────────
export const documents = {
  list: () => request<{ documents: DocumentOut[]; total: number }>('/api/documents/'),

  upload: async (file: File, sensitivityLevel: string): Promise<DocumentUploadResponse> => {
    const token = localStorage.getItem('token');
    const form = new FormData();
    form.append('file', file);
    form.append('sensitivity_level', sensitivityLevel);

    const res = await fetch(`${BASE}/api/documents/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  remove: (docId: string) =>
    request<{ detail: string; chunks_removed: number }>(`/api/documents/${docId}`, {
      method: 'DELETE',
    }),
};

// ── Chat ────────────────────────────────────────────────────────────
export const chat = {
  send: (message: string, conversationId?: string) =>
    request<ChatResponse>('/api/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),

  conversations: () => request<any[]>('/api/chat/conversations'),

  getConversation: (id: string) =>
    request<Conversation & { messages: any[] }>(`/api/chat/conversations/${id}`),

  feedback: (messageId: string, rating: number, comment?: string) =>
    request<{ detail: string }>('/api/chat/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message_id: messageId, rating, comment }),
    }),
};

// ── Admin ───────────────────────────────────────────────────────────
export const admin = {
  stats: () => request<AdminStats>('/api/admin/stats'),

  auditLogs: (limit = 50) =>
    request<AuditLog[]>(`/api/admin/audit-logs?limit=${limit}`),
};
