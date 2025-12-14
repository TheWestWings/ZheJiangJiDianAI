import { Space } from 'antd';
import React from 'react';
import User from '../user';

import styled from './index.less';

const Circle = ({ children, ...restProps }: React.PropsWithChildren) => {
  return (
    <div {...restProps} className={styled.circle}>
      {children}
    </div>
  );
};

const RightToolBar = () => {
  return (
    <div className={styled.toolbarWrapper}>
      <Space wrap size={16}>
        <User></User>
      </Space>
    </div>
  );
};

export default RightToolBar;
