import { ReactComponent as ChatAppCube } from '@/assets/svg/chat-app-cube.svg';
import RenameModal from '@/components/rename-modal';
import SvgIcon from '@/components/svg-icon';
import { useTheme } from '@/components/theme-provider';
import { useSafeLocalStorageState } from '@/hooks/chat-font-hooks';
import {
  useClickConversationCard,
  useFetchNextDialogList,
  useGetChatSearchParams,
} from '@/hooks/chat-hooks';
import { useTranslate } from '@/hooks/common-hooks';
import { useIsMobile } from '@/hooks/use-mobile';
import {
  DeleteOutlined,
  EditOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import {
  Button,
  Card,
  Divider,
  Dropdown,
  Flex,
  MenuProps,
  Space,
  Spin,
  Tag,
  Typography,
} from 'antd';
import { MenuItemProps } from 'antd/lib/menu/MenuItem';
import classNames from 'classnames';
import { useCallback, useEffect, useRef, useState } from 'react';
import ChatContainer from './chat-container';
import {
  useDeleteConversation,
  useHandleItemHover,
  useRenameConversation,
  useSelectDerivedConversationList,
} from './hooks';
import styles from './index.less';

const { Text } = Typography;

const FONT_SIZE_STORAGE_KEY = 'chat_font_size_v2';
const DEFAULT_FONT_SIZE = 20;

const Chat = () => {
  const { onRemoveConversation } = useDeleteConversation();
  const { handleClickConversation } = useClickConversationCard();
  const { conversationId } = useGetChatSearchParams();
  const { theme } = useTheme();

  // 自动获取助理列表并设置默认助理
  useFetchNextDialogList();

  const {
    list: conversationList,
    addTemporaryConversation,
    loading: conversationLoading,
  } = useSelectDerivedConversationList();
  const {
    activated: conversationActivated,
    handleItemEnter: handleConversationItemEnter,
    handleItemLeave: handleConversationItemLeave,
  } = useHandleItemHover();
  const {
    conversationRenameLoading,
    initialConversationName,
    onConversationRenameOk,
    conversationRenameVisible,
    hideConversationRenameModal,
    showConversationRenameModal,
  } = useRenameConversation();
  const { t } = useTranslate('chat');
  const [controller, setController] = useState(new AbortController());

  // 历史记录折叠状态 - 默认收起
  const [historyCollapsed, setHistoryCollapsed] = useState(true);
  const { isMobile } = useIsMobile();

  const [fontSize] = useSafeLocalStorageState(
    FONT_SIZE_STORAGE_KEY,
    DEFAULT_FONT_SIZE,
  );

  // 可拖拽调节宽度
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const isResizing = useRef(false);
  const MIN_WIDTH = 200;
  const MAX_WIDTH = 450;

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isResizing.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      const newWidth = e.clientX;
      if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const handleConversationCardEnter = (id: string) => () => {
    handleConversationItemEnter(id);
  };

  const handleRemoveConversation =
    (conversationId: string): MenuItemProps['onClick'] =>
    ({ domEvent }) => {
      domEvent.preventDefault();
      domEvent.stopPropagation();
      onRemoveConversation([conversationId]);
    };

  const handleShowConversationRenameModal =
    (conversationId: string): MenuItemProps['onClick'] =>
    ({ domEvent }) => {
      domEvent.preventDefault();
      domEvent.stopPropagation();
      showConversationRenameModal(conversationId);
    };

  const handleConversationCardClick = useCallback(
    (conversationId: string, isNew: boolean) => () => {
      handleClickConversation(conversationId, isNew ? 'true' : '');
      setController((pre) => {
        pre.abort();
        return new AbortController();
      });
    },
    [handleClickConversation],
  );

  const handleCreateTemporaryConversation = useCallback(() => {
    addTemporaryConversation();
  }, [addTemporaryConversation]);

  // 切换历史记录折叠状态
  const toggleHistoryCollapsed = useCallback(() => {
    setHistoryCollapsed((prev) => !prev);
  }, []);

  const buildConversationItems = (conversationId: string) => {
    const appItems: MenuProps['items'] = [
      {
        key: '1',
        onClick: handleShowConversationRenameModal(conversationId),
        label: (
          <Space>
            <EditOutlined />
            {t('rename', { keyPrefix: 'common' })}
          </Space>
        ),
      },
      { type: 'divider' },
      {
        key: '2',
        onClick: handleRemoveConversation(conversationId),
        label: (
          <Space>
            <DeleteOutlined />
            {t('delete', { keyPrefix: 'common' })}
          </Space>
        ),
      },
    ];

    return appItems;
  };

  return (
    <Flex className={styles.chatWrapper}>
      {/* 移动端浮动历史按钮 */}
      {isMobile && (
        <Button
          type="text"
          className={styles.mobileHistoryButton}
          icon={
            historyCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />
          }
          onClick={toggleHistoryCollapsed}
        />
      )}
      {/* 可收起的历史记录面板 */}
      <Flex
        className={classNames(styles.chatTitleWrapper, {
          [styles.chatTitleWrapperCollapsed]: historyCollapsed,
          [styles.chatTitleWrapperMobile]: isMobile && !historyCollapsed,
        })}
        style={{ width: historyCollapsed ? 60 : sidebarWidth }}
      >
        <Flex flex={1} vertical>
          <Flex
            justify={'space-between'}
            align="center"
            className={styles.chatTitle}
          >
            {!historyCollapsed && (
              <Space>
                <b>{t('chat')}</b>
                <Tag>{conversationList.length}</Tag>
              </Space>
            )}
            <Space>
              {!historyCollapsed && (
                <SvgIcon
                  name="plus-circle-fill"
                  width={20}
                  onClick={handleCreateTemporaryConversation}
                ></SvgIcon>
              )}
              <Button
                type="text"
                icon={
                  historyCollapsed ? (
                    <MenuUnfoldOutlined />
                  ) : (
                    <MenuFoldOutlined />
                  )
                }
                onClick={toggleHistoryCollapsed}
                size="small"
              />
            </Space>
          </Flex>
          {!historyCollapsed && (
            <>
              <Divider></Divider>
              <Flex vertical gap={10} className={styles.chatTitleContent}>
                <Spin
                  spinning={conversationLoading}
                  wrapperClassName={styles.chatSpin}
                >
                  {conversationList.map((x) => (
                    <Card
                      key={x.id}
                      hoverable
                      onClick={handleConversationCardClick(x.id, x.is_new)}
                      onMouseEnter={handleConversationCardEnter(x.id)}
                      onMouseLeave={handleConversationItemLeave}
                      className={classNames(styles.chatTitleCard, {
                        [theme === 'dark'
                          ? styles.chatTitleCardSelectedDark
                          : styles.chatTitleCardSelected]:
                          x.id === conversationId,
                      })}
                    >
                      <Flex justify="space-between" align="center">
                        <div>
                          <Text
                            ellipsis={{ tooltip: x.name }}
                            style={{ width: 150 }}
                          >
                            {x.name}
                          </Text>
                        </div>
                        {conversationActivated === x.id &&
                          x.id !== '' &&
                          !x.is_new && (
                            <section>
                              <Dropdown
                                menu={{ items: buildConversationItems(x.id) }}
                              >
                                <ChatAppCube
                                  className={styles.cubeIcon}
                                ></ChatAppCube>
                              </Dropdown>
                            </section>
                          )}
                      </Flex>
                    </Card>
                  ))}
                </Spin>
              </Flex>
            </>
          )}
        </Flex>
      </Flex>
      {/* 拖拽调节宽度的手柄 */}
      {!historyCollapsed && (
        <div className={styles.resizeHandle} onMouseDown={handleMouseDown} />
      )}
      <ChatContainer
        controller={controller}
        fontSize={fontSize}
      ></ChatContainer>
      <RenameModal
        visible={conversationRenameVisible}
        hideModal={hideConversationRenameModal}
        onOk={onConversationRenameOk}
        initialName={initialConversationName}
        loading={conversationRenameLoading}
      ></RenameModal>
    </Flex>
  );
};

export default Chat;
