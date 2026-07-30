import apiClient from './client';

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: string | null;
  token_count: number | null;
  latency_ms: number | null;
  created_at: string;
}

export async function getMessages(
  sessionId: string,
  cursor?: string,
  limit = 30
): Promise<{ messages: ChatMessage[]; next_cursor: string | null; has_more: boolean }> {
  const params: Record<string, string | number> = { limit };
  if (cursor) params.cursor = cursor;
  const res = await apiClient.get(`/sessions/${sessionId}/messages`, { params });
  return res.data;
}

/**
 * Stream a chat query via SSE.
 * Returns an AbortController and an async generator of SSE events.
 */
export function streamQuery(
  sessionId: string,
  message: string,
  onToken: (token: string) => void,
  onThinking: (stage: string) => void,
  onSources: (sources: Array<{ id: number; file: string; page: number; snippet: string }>) => void,
  onDone: (data: { message_id: string; tokens_used: number; latency_ms: number }) => void,
  onError: (error: string) => void
): AbortController {
  const controller = new AbortController();
  const token = localStorage.getItem('access_token');

  fetch('/api/v1/chat/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ session_id: sessionId, message }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({ error: { message: 'Request failed' } }));
        onError(err.error?.message || `HTTP ${response.status}`);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        onError('No response body');
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let eventType = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const parsed = JSON.parse(data);
              switch (eventType) {
                case 'token':
                  onToken(parsed.token || '');
                  break;
                case 'thinking':
                  onThinking(parsed.stage || '');
                  break;
                case 'sources':
                  onSources(parsed);
                  break;
                case 'done':
                  onDone(parsed);
                  break;
                case 'error':
                  onError(parsed.message || 'Unknown error');
                  break;
              }
            } catch {
              // skip parse errors
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError(err.message || 'Network error');
      }
    });

  return controller;
}
