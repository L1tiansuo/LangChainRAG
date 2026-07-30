import apiClient from './client';

export interface UserInfo {
  id: string;
  username: string;
  email: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await apiClient.post('/auth/login', { username, password });
  return res.data;
}

export async function register(
  username: string,
  password: string,
  email?: string
): Promise<{ user_id: string; username: string; message: string }> {
  const res = await apiClient.post('/auth/register', { username, password, email });
  return res.data;
}

export async function logout(): Promise<void> {
  try {
    await apiClient.post('/auth/logout');
  } finally {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }
}

export async function changePassword(
  oldPassword: string,
  newPassword: string
): Promise<void> {
  await apiClient.post('/auth/change-password', {
    old_password: oldPassword,
    new_password: newPassword,
  });
}

export async function getMe(): Promise<UserInfo> {
  const res = await apiClient.get('/auth/me');
  return res.data;
}
