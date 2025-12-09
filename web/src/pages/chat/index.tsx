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
import { useCallback, useState } from 'react';
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

  const [fontSize] = useSafeLocalStorageState(
    FONT_SIZE_STORAGE_KEY,
    DEFAULT_FONT_SIZE,
  );

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
      {/* 可收起的历史记录面板 */}
      <Flex
        className={classNames(styles.chatTitleWrapper, {
          [styles.chatTitleWrapperCollapsed]: historyCollapsed,
        })}
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
      <Divider type={'vertical'} className={styles.divider}></Divider>
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
