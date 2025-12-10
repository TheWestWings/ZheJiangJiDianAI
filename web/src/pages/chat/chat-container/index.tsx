import MessageInput from '@/components/message-input';
import MessageItem from '@/components/message-item';
import PdfDrawer from '@/components/pdf-drawer';
import { useClickDrawer } from '@/components/pdf-drawer/hooks';
import { MessageType } from '@/constants/chat';
import {
  useFetchNextConversation,
  useGetChatSearchParams,
} from '@/hooks/chat-hooks';
import { useFetchUserInfo } from '@/hooks/user-setting-hooks';
import { buildMessageUuidWithRole } from '@/utils/chat';
import { Flex, Spin, Typography } from 'antd';
import { memo, useCallback, useEffect, useRef, useState } from 'react';
import {
  useCreateConversationBeforeUploadDocument,
  useGetFileIcon,
  useSelectDerivedConversationList,
  useSendButtonDisabled,
  useSendNextMessage,
} from '../hooks';
import { buildMessageItemReference } from '../utils';
import styles from './index.less';

const { Title } = Typography;

interface IProps {
  controller: AbortController;
  fontSize: number;
}

const ChatContainer = ({ controller, fontSize = 20 }: IProps) => {
  const { conversationId, dialogId } = useGetChatSearchParams();
  const { data: conversation } = useFetchNextConversation();
  const { addTemporaryConversation } = useSelectDerivedConversationList();

  const {
    value,
    ref,
    loading,
    sendLoading,
    derivedMessages,
    handleInputChange,
    handlePressEnter,
    regenerateMessage,
    removeMessageById,
    stopOutputMessage,
  } = useSendNextMessage(controller);

  const { visible, hideModal, documentId, selectedChunk, clickDocumentButton } =
    useClickDrawer();
  // 初始状态下不禁用发送（只检查dialogId）
  const disabled = !dialogId;
  const sendDisabled = useSendButtonDisabled(value);
  useGetFileIcon();
  const { data: userInfo } = useFetchUserInfo();
  const { createConversationBeforeUploadDocument } =
    useCreateConversationBeforeUploadDocument();

  // 判断是否为初始状态（没有消息且没有选中对话）
  const isInitialState =
    (!derivedMessages || derivedMessages.length === 0) && !conversationId;

  // 动画状态
  const [isTransitioning, setIsTransitioning] = useState(false);

  // 用于保存待发送的消息参数
  const pendingSendRef = useRef<{
    documentIds: string[];
    tempFileIds?: string[];
    tempFileInfos?: any[];
  } | null>(null);

  // 监听 conversationId 变化，当对话创建成功后发送消息
  useEffect(() => {
    if (conversationId && pendingSendRef.current) {
      const { documentIds, tempFileIds, tempFileInfos } =
        pendingSendRef.current;
      pendingSendRef.current = null;
      // 对话已创建，发送消息
      handlePressEnter(documentIds, tempFileIds, tempFileInfos);
    }
  }, [conversationId, handlePressEnter]);

  // 初始状态下的发送处理：先创建临时对话，等待对话创建后再发送
  const handleInitialPressEnter = useCallback(
    (
      documentIds: string[],
      tempFileIds: string[] | undefined,
      tempFileInfos: any[] | undefined,
    ) => {
      if (!value.trim()) return;

      // 开始过渡动画
      setIsTransitioning(true);

      // 保存待发送的参数
      pendingSendRef.current = { documentIds, tempFileIds, tempFileInfos };

      // 创建临时对话（会设置 conversationId 和 isNew 参数）
      addTemporaryConversation();
    },
    [addTemporaryConversation, value],
  );

  // 当不再是初始状态时，重置过渡状态
  useEffect(() => {
    if (!isInitialState) {
      setIsTransitioning(false);
    }
  }, [isInitialState]);

  return (
    <>
      <Flex flex={1} className={styles.chatContainer} vertical>
        {isInitialState && !isTransitioning ? (
          // 初始状态：居中显示标题和输入框
          <Flex
            flex={1}
            vertical
            justify="center"
            align="center"
            className={styles.initialContainer}
          >
            <div className={styles.initialContent}>
              <Title level={1} className={styles.appTitle}>
                浙机电校园百事通
              </Title>
              <div className={styles.initialInputWrapper}>
                <MessageInput
                  disabled={disabled}
                  sendDisabled={sendDisabled}
                  sendLoading={sendLoading}
                  value={value}
                  onInputChange={handleInputChange}
                  onPressEnter={handleInitialPressEnter}
                  conversationId={conversationId}
                  useTempUpload={true}
                  createConversationBeforeUploadDocument={
                    createConversationBeforeUploadDocument
                  }
                  stopOutputMessage={stopOutputMessage}
                ></MessageInput>
              </div>
            </div>
          </Flex>
        ) : (
          // 有消息时或过渡中：正常布局
          <>
            <Flex
              flex={1}
              vertical
              className={styles.messageContainer}
              style={{ fontSize: `${fontSize}px` }}
            >
              <div>
                <Spin spinning={loading}>
                  {derivedMessages?.map((message, i) => {
                    return (
                      <MessageItem
                        loading={
                          message.role === MessageType.Assistant &&
                          sendLoading &&
                          derivedMessages.length - 1 === i
                        }
                        key={buildMessageUuidWithRole(message)}
                        item={message}
                        nickname={userInfo.nickname}
                        avatar={userInfo.avatar}
                        avatarDialog={conversation.avatar}
                        reference={buildMessageItemReference(
                          {
                            message: derivedMessages,
                            reference: conversation.reference,
                          },
                          message,
                        )}
                        clickDocumentButton={clickDocumentButton}
                        index={i}
                        removeMessageById={removeMessageById}
                        regenerateMessage={regenerateMessage}
                        sendLoading={sendLoading}
                      ></MessageItem>
                    );
                  })}
                </Spin>
              </div>
              <div ref={ref} />
            </Flex>
            <div className={styles.bottomInputWrapper}>
              <MessageInput
                disabled={disabled}
                sendDisabled={sendDisabled}
                sendLoading={sendLoading}
                value={value}
                onInputChange={handleInputChange}
                onPressEnter={(
                  documentIds: string[],
                  tempFileIds: string[] | undefined,
                  tempFileInfos: any[] | undefined,
                ) => handlePressEnter(documentIds, tempFileIds, tempFileInfos)}
                conversationId={conversationId}
                useTempUpload={true}
                createConversationBeforeUploadDocument={
                  createConversationBeforeUploadDocument
                }
                stopOutputMessage={stopOutputMessage}
              ></MessageInput>
            </div>
          </>
        )}
      </Flex>
      <PdfDrawer
        visible={visible}
        hideModal={hideModal}
        documentId={documentId}
        chunk={selectedChunk}
      ></PdfDrawer>
    </>
  );
};

export default memo(ChatContainer);
