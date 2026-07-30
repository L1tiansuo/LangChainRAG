import { Layout, Menu, Button, Dropdown, Space, Typography } from 'antd';
import {
  MessageOutlined,
  DatabaseOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

const { Header, Content } = Layout;
const { Text } = Typography;

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const currentKey = location.pathname.startsWith('/kb')
    ? '/kb'
    : location.pathname.startsWith('/settings')
    ? '/settings'
    : '/chat';

  const menuItems = [
    { key: '/chat', icon: <MessageOutlined />, label: '智能问答' },
    ...(user?.role === 'admin'
      ? [{ key: '/kb', icon: <DatabaseOutlined />, label: '知识库管理' }]
      : []),
    { key: '/settings', icon: <SettingOutlined />, label: '个人设置' },
  ];

  const userMenuItems = [
    {
      key: 'info',
      label: (
        <div>
          <Text strong>{user?.username}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {user?.role === 'admin' ? '管理员' : '普通用户'}
          </Text>
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: handleLogout },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#fff',
          borderBottom: '1px solid #f0f0f0',
          padding: '0 24px',
          height: 56,
        }}
      >
        <Space>
          <Text strong style={{ fontSize: 18, color: '#1677ff' }}>
            📚 企业知识库助手
          </Text>
          <Menu
            mode="horizontal"
            selectedKeys={[currentKey]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ border: 'none', marginLeft: 24 }}
          />
        </Space>

        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/chat')}
            size="small"
          >
            新建会话
          </Button>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Button icon={<UserOutlined />} type="text">
              {user?.username}
            </Button>
          </Dropdown>
        </Space>
      </Header>
      <Content style={{ background: '#f5f5f5' }}>{children}</Content>
    </Layout>
  );
}
