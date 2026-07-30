import { useState } from 'react';
import { Typography, Card, Form, Input, Button, Descriptions, message } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';
import { changePassword } from '../api/auth';

const { Title } = Typography;

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [form] = Form.useForm();

  const handleChangePassword = async (values: {
    old_password: string;
    new_password: string;
  }) => {
    setPasswordLoading(true);
    try {
      await changePassword(values.old_password, values.new_password);
      message.success('密码修改成功');
      form.resetFields();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      message.error(detail || '密码修改失败');
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div style={{ padding: 24, maxWidth: 600, margin: '0 auto' }}>
      <Title level={3} style={{ marginBottom: 24 }}>
        个人设置
      </Title>

      <Card title="用户信息" style={{ marginBottom: 24 }}>
        <Descriptions column={1} size="middle">
          <Descriptions.Item label="用户名">{user?.username}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{user?.email || '未设置'}</Descriptions.Item>
          <Descriptions.Item label="角色">
            {user?.role === 'admin' ? '管理员' : '普通用户'}
          </Descriptions.Item>
          <Descriptions.Item label="注册时间">
            {user?.created_at ? new Date(user.created_at).toLocaleString('zh-CN') : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="修改密码">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleChangePassword}
          style={{ maxWidth: 400 }}
        >
          <Form.Item
            name="old_password"
            label="当前密码"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="当前密码" />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 8, message: '密码至少 8 个字符' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="新密码（至少 8 个字符）" />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="确认新密码"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次密码输入不一致'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="确认新密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={passwordLoading}>
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
