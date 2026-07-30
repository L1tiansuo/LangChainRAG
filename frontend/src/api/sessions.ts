import apiClient from './client';

export interface SessionInfo {
  id: string;
  user_id: string;
  title: string;
  status: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export async function getSessions(
  page = 1,
  pageSize = 20
): Promise<{ sessions: SessionInfo[]; total: number }> {
  const res = await apiClient.get('/sessions', { params: { page, page_size: pageSize } });
  return res.data;
}

export async function createSession(title = '新会话'): Promise<SessionInfo> {
  const res = await apiClient.post('/sessions', { title });
  return res.data;
}

export async function getSession(id: string): Promise<SessionInfo> {
  const res = await apiClient.get(`/sessions/${id}`);
  return res.data;
}

export async function updateSession(
  id: string,
  data: { title?: string; status?: string }
): Promise<SessionInfo> {
  const res = await apiClient.patch(`/sessions/${id}`, data);
  return res.data;
}

export async function deleteSession(id: string): Promise<void> {
  await apiClient.delete(`/sessions/${id}`);
}
