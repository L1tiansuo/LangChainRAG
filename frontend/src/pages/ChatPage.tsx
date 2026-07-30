import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout, Input, Button, List, Typography, Space, Spin, Tag, Empty, Popconfirm } from 'antd';
import {
  SendOutlined,
  DeleteOutlined,
  RobotOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';
import { getSessions, createSession, deleteSession, type SessionInfo } from '../api/sessions';
import type { ChatMessage } from '../api/chat';
import { getMessages, streamQuery } from '../api/chat';

const { Sider, Content } = Layout;
const { TextArea } = Input;
const { Text, Paragraph } = Typography;

interface UIMessage extends ChatMessage {
  sources?: Array<{ id: number; file: string; page: number; snippet: string }>;
}

export default function ChatPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(sessionId || null);
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [thinking, setThinking] = useState('');
  const [loadingSessions, setLoadingSessions] = useState(false);

  // Load sessions
  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      loadMessages(activeSessionId);
    }
  }, [activeSessionId]);

  const loadSessions = async () => {
    setLoadingSessions(true);
    try {
      const data = await getSessions();
      setSessions(data.sessions);
      if (!activeSessionId && data.sessions.length > 0) {
        setActiveSessionId(data.sessions[0].id);
        navigate(`/chat/${data.sessions[0].id}`);
      }
    } catch {
      // ignore
    } finally {
      setLoadingSessions(false);
    }
  };

  const loadMessages = async (sid: string) => {
    try {
      const data = await getMessages(sid);
      const msgs: UIMessage[] = data.messages.map((m) => ({
        ...m,
        sources: m.citations ? JSON.parse(m.citations) : undefined,
      }));
      setMessages(msgs);
    } catch {
      setMessages([]);
    }
  };

  const handleNewSession = async () => {
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
      navigate(`/chat/${session.id}`);
    } catch {
      // ignore
    }
  };

  const handleDeleteSession = async (sid: string) => {
    try {
      await deleteSession(sid);
      setSessions((prev) => prev.filter((s) => s.id !== sid));
      if (activeSessionId === sid) {
        const remaining = sessions.filter((s) => s.id !== sid);
        if (remaining.length > 0) {
          setActiveSessionId(remaining[0].id);
          navigate(`/chat/${remaining[0].id}`);
        } else {
          setActiveSessionId(null);
          setMessages([]);
          navigate('/chat');
        }
      }
    } catch {
      // ignore
    }
  };

  const handleSend = async () => {
    const text = inputValue.trim();
    if (!text || streaming || !activeSessionId) return;

    setInputValue('');
    setStreaming(true);
    setThinking('检索中...');

    const userMsg: UIMessage = {
      id: `temp-${Date.now()}`,
      session_id: activeSessionId,
      role: 'user',
      content: text,
      citations: null,
      token_count: null,
      latency_ms: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    const aiMsg: UIMessage = {
      id: `temp-ai-${Date.now()}`,
      session_id: activeSessionId,
      role: 'assistant',
      content: '',
      citations: null,
      token_count: null,
      latency_ms: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, aiMsg]);

    let fullText = '';

    streamQuery(
      activeSessionId,
      text,
      (token) => {
        fullText += token;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsg.id ? { ...m, content: fullText } : m
          )
        );
      },
      (stage) => {
        const stages: Record<string, string> = {
          rewriting: '正在改写查询...',
          retrieving: '正在检索知识库...',
          reranking: '正在精排结果...',
          generating: '正在生成回答...',
        };
        setThinking(stages[stage] || stage);
      },
      (sources) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsg.id ? { ...m, sources, citations: JSON.stringify(sources) } : m
          )
        );
      },
      () => {
        setStreaming(false);
        setThinking('');
        loadSessions(); // refresh session list
      },
      (error) => {
        setStreaming(false);
        setThinking('');
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsg.id
              ? { ...m, content: `❌ 错误: ${error}` }
              : m
          )
        );
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Layout style={{ height: 'calc(100vh - 56px)' }}>
      <Sider
        width={260}
        style={{
          background: '#fff',
          borderRight: '1px solid #f0f0f0',
          overflow: 'auto',
        }}
      >
        <div style={{ padding: 16 }}>
          <Button type="primary" block onClick={handleNewSession} icon={<SendOutlined />}>
            新建会话
          </Button>
        </div>
        <List
          loading={loadingSessions}
          dataSource={sessions}
          locale={{ emptyText: <Empty description="暂无会话" /> }}
          renderItem={(session) => (
            <List.Item
              onClick={() => {
                setActiveSessionId(session.id);
                navigate(`/chat/${session.id}`);
              }}
              style={{
                cursor: 'pointer',
                padding: '8px 16px',
                background: activeSessionId === session.id ? '#e6f4ff' : 'transparent',
              }}
              actions={[
                <Popconfirm
                  key="delete"
                  title="确定删除此会话？"
                  onConfirm={(e) => {
                    e?.stopPropagation();
                    handleDeleteSession(session.id);
                  }}
                  onCancel={(e) => e?.stopPropagation()}
                >
                  <Button
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => e.stopPropagation()}
                  />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Text ellipsis style={{ width: 180, fontSize: 14 }}>
                    {session.title}
                  </Text>
                }
                description={
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {session.message_count} 条消息
                  </Text>
                }
              />
            </List.Item>
          )}
        />
      </Sider>

      <Content style={{ display: 'flex', flexDirection: 'column' }}>
        {/* Messages */}
        <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
          {messages.length === 0 && !streaming ? (
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
              }}
            >
              <Empty description="开始提问吧！">
                <Space direction="vertical" size="small">
                  <Text type="secondary">示例问题：</Text>
                  <Tag>这个产品有哪些规格参数？</Tag>
                  <Tag>iPhone 15 的价格是多少？</Tag>
                  <Tag>有哪些优惠活动？</Tag>
                </Space>
              </Empty>
            </div>
          ) : (
            <div style={{ width: '100%', maxWidth: 900, margin: '0 auto', padding: '0 16px' }}>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    display: 'flex',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    marginBottom: 16,
                  }}
                >
                  <div
                    style={{
                      maxWidth: '75%',
                      padding: '12px 16px',
                      borderRadius: msg.role === 'user'
                        ? '12px 12px 4px 12px'
                        : '12px 12px 12px 4px',
                      background: msg.role === 'user' ? '#1677ff' : '#fff',
                      color: msg.role === 'user' ? '#fff' : 'inherit',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
                    }}
                  >
                    <div style={{ marginBottom: 4 }}>
                      {msg.role === 'user' ? (
                        <Space>
                          <UserOutlined />
                          <Text strong style={{ color: '#fff' }}>{user?.username}</Text>
                        </Space>
                      ) : (
                        <Space>
                          <RobotOutlined />
                          <Text strong>AI 助手</Text>
                        </Space>
                      )}
                    </div>
                    <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                      {msg.content || (msg.id.startsWith('temp-ai') && streaming ? (
                        <Text type={msg.role === 'user' ? undefined : 'secondary'}>
                          思考中...
                        </Text>
                      ) : null)}
                    </Paragraph>
                    {msg.sources && msg.sources.length > 0 && (
                      <div
                        style={{
                          marginTop: 12,
                          padding: 8,
                          background: '#f5f5f5',
                          borderRadius: 4,
                          fontSize: 12,
                        }}
                      >
                        <Text type="secondary" strong>📎 参考来源：</Text>
                        {msg.sources.map((s) => (
                          <Tag key={s.id} style={{ marginTop: 4 }}>
                            [{s.id}] {s.file}, p.{s.page}
                          </Tag>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {thinking && streaming && (
                <div style={{ textAlign: 'center' }}>
                  <Spin size="small" />
                  <Text type="secondary" style={{ marginLeft: 8 }}>{thinking}</Text>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid #f0f0f0',
            background: '#fff',
          }}
        >
          <div style={{ maxWidth: 800, margin: '0 auto', display: 'flex', gap: 8 }}>
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={activeSessionId ? '输入您的问题，Enter 发送，Shift+Enter 换行' : '请先创建或选择一个会话'}
              disabled={!activeSessionId || streaming}
              autoSize={{ minRows: 1, maxRows: 4 }}
              style={{ flex: 1 }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={streaming}
              disabled={!inputValue.trim() || !activeSessionId}
            >
              发送
            </Button>
          </div>
        </div>
      </Content>
    </Layout>
  );
}
