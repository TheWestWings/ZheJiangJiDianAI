import { Authorization, Token, UserInfo } from '@/constants/authorization';
import { getSearchValue } from './common-util';
const KeySet = [Authorization, Token, UserInfo];

const storage = {
  getAuthorization: () => {
    return localStorage.getItem(Authorization);
  },
  getToken: () => {
    return localStorage.getItem(Token);
  },
  getUserInfo: () => {
    return localStorage.getItem(UserInfo);
  },
  getUserInfoObject: () => {
    return JSON.parse(localStorage.getItem('userInfo') || '');
  },
  setAuthorization: (value: string) => {
    localStorage.setItem(Authorization, value);
  },
  setToken: (value: string) => {
    localStorage.setItem(Token, value);
  },
  setUserInfo: (value: string | Record<string, unknown>) => {
    let valueStr = typeof value !== 'string' ? JSON.stringify(value) : value;
    localStorage.setItem(UserInfo, valueStr);
  },
  setItems: (pairs: Record<string, string>) => {
    Object.entries(pairs).forEach(([key, value]) => {
      localStorage.setItem(key, value);
    });
  },
  removeAuthorization: () => {
    localStorage.removeItem(Authorization);
  },
  removeAll: () => {
    KeySet.forEach((x) => {
      localStorage.removeItem(x);
    });
  },
  setLanguage: (lng: string) => {
    localStorage.setItem('lng', lng);
  },
  getLanguage: (): string => {
    return localStorage.getItem('lng') as string;
  },
};

export const getAuthorization = () => {
  const auth = getSearchValue('auth');
  const authorization = auth
    ? 'Bearer ' + auth
    : storage.getAuthorization() || '';

  return authorization;
};

export default storage;

// ZIME CAS 统一身份认证配置
const CAS_CONFIG = {
  authorizeUrl: 'https://account.zime.edu.cn/cas/oauth2.0/authorize',
  clientId: '9Qy5UMKiAs2aoCSlXK',
  redirectUri: window.location.origin + '/api/user/cas_callback',
};

/**
 * 跳转到 CAS 统一身份认证登录页面
 * 未登录用户访问受限资源时会自动调用此函数
 */
export function redirectToLogin() {
  const casLoginUrl =
    `${CAS_CONFIG.authorizeUrl}?` +
    `response_type=code&` +
    `client_id=${CAS_CONFIG.clientId}&` +
    `redirect_uri=${encodeURIComponent(CAS_CONFIG.redirectUri)}`;

  window.location.href = casLoginUrl;
}
