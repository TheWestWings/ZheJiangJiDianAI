import { useEffect, useState } from 'react';

// 移动端断点阈值
const MOBILE_BREAKPOINT = 768;

/**
 * 检测当前设备是否为移动端
 * @returns {{ isMobile: boolean, screenWidth: number }}
 */
export const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth < MOBILE_BREAKPOINT;
    }
    return false;
  });

  const [screenWidth, setScreenWidth] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth;
    }
    return 1024;
  });

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      setScreenWidth(width);
      setIsMobile(width < MOBILE_BREAKPOINT);
    };

    // 添加事件监听
    window.addEventListener('resize', handleResize);

    // 初始化时执行一次
    handleResize();

    // 清理事件监听
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return { isMobile, screenWidth };
};

export default useIsMobile;
