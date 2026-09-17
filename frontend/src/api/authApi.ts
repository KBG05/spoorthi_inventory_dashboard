import { apiClient } from './client';
import type { TokenResponse, UserResponse } from './types';

export const authApi = {
  login: async (username: string, password: string): Promise<TokenResponse> => {
    const form = new URLSearchParams();
    form.set('username', username);
    form.set('password', password);
    const { data } = await apiClient.post<TokenResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  },
  me: async (): Promise<UserResponse> => {
    const { data } = await apiClient.get<UserResponse>('/auth/me');
    return data;
  },
};
