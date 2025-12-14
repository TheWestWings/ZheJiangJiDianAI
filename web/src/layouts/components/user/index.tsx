import { useFetchUserInfo } from '@/hooks/user-setting-hooks';
import { LogoutOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { Avatar, Dropdown, Space } from 'antd';
import React from 'react';

import styles from '../../index.less';

const App: React.FC = () => {
  const { data: userInfo } = useFetchUserInfo();

  // 退出登录
  const handleLogout = () => {
    // 清除本地存储的 token
    localStorage.removeItem('Authorization');
    localStorage.removeItem('userInfo');
    // 跳转到登录页面
    window.location.href = '/login';
  };

  // 下拉菜单项
  const items: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  // 获取用户名显示
  const displayName = userInfo.nickname || userInfo.email || '用户';

  return (
    <Dropdown menu={{ items }} placement="bottomRight" trigger={['hover']}>
      <Space className={styles.clickAvailable} style={{ cursor: 'pointer' }}>
        <span style={{ fontSize: 14, color: '#333' }}>{displayName}，欢迎</span>
        <Avatar
          size={32}
          style={{ marginLeft: 40 }}
          src={
            userInfo.avatar ??
            'https://picx.zhimg.com/v2-aaf12b68b54b8812e6b449e7368d30cf_l.jpg'
          }
        />
      </Space>
    </Dropdown>
  );
};

export default App;
