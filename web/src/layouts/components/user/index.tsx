import { useIsMobile } from '@/hooks/use-mobile';
import { useFetchUserInfo } from '@/hooks/user-setting-hooks';
import authorizationUtil from '@/utils/authorization-util';
import { LogoutOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { Avatar, Dropdown, Space, message } from 'antd';
import React from 'react';

import styles from '../../index.less';

const App: React.FC = () => {
  const { data: userInfo } = useFetchUserInfo();
  const { isMobile } = useIsMobile();

  // 退出登录 - 跳转到后端 logout，后端会重定向到 CAS 退出
  const handleLogout = () => {
    // 清除本地存储的 token
    authorizationUtil.removeAll();
    message.success('退出登录成功');
    // 跳转到后端 logout，触发 CAS 退出
    window.location.href = '/v1/user/logout';
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
        {/* 移动端隐藏欢迎文字 */}
        {!isMobile && (
          <span style={{ fontSize: 14, color: '#333' }}>
            {displayName}，欢迎
          </span>
        )}
        <Avatar
          size={isMobile ? 28 : 32}
          style={{ marginLeft: 0 }}
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
