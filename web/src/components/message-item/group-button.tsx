import { PromptIcon } from '@/assets/icon/Icon';
import CopyToClipboard from '@/components/copy-to-clipboard';
import { useSetModalState } from '@/hooks/common-hooks';
import { IRemoveMessageById } from '@/hooks/logic-hooks';
import {
  DatabaseOutlined,
  DeleteOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { Radio, Tooltip } from 'antd';
import { useTranslation } from 'react-i18next';
import FeedbackModal from './feedback-modal';
import { useRemoveMessage, useSendFeedback, useSpeech } from './hooks';
import PromptModal from './prompt-modal';

import { IReference } from '@/interfaces/database/chat';
import ReferenceModal from './reference-modal';

interface IProps {
  messageId: string;
  content: string;
  prompt?: string;
  showLikeButton: boolean;
  audioBinary?: string;
  showLoudspeaker?: boolean;
  reference?: IReference;
}

export const AssistantGroupButton = ({
  messageId,
  content,
  prompt,
  audioBinary,
  reference,
}: IProps) => {
  const { visible, hideModal, onFeedbackOk, loading } =
    useSendFeedback(messageId);
  const {
    visible: promptVisible,
    hideModal: hidePromptModal,
    showModal: showPromptModal,
  } = useSetModalState();
  const {
    visible: referenceVisible,
    hideModal: hideReferenceModal,
    showModal: showReferenceModal,
  } = useSetModalState();

  useTranslation();
  useSpeech(content, audioBinary);

  const hasReference = reference?.chunks && reference.chunks.length > 0;

  return (
    <>
      <Radio.Group size="small">
        <Radio.Button value="a">
          <CopyToClipboard text={content}></CopyToClipboard>
        </Radio.Button>
        {prompt && (
          <Radio.Button value="e" onClick={showPromptModal}>
            <PromptIcon style={{ fontSize: '16px' }} />
          </Radio.Button>
        )}
        {hasReference && (
          <Radio.Button value="r" onClick={showReferenceModal}>
            <Tooltip title="知识库详细信息">
              <DatabaseOutlined />
            </Tooltip>
          </Radio.Button>
        )}
      </Radio.Group>
      {visible && (
        <FeedbackModal
          visible={visible}
          hideModal={hideModal}
          onOk={onFeedbackOk}
          loading={loading}
        ></FeedbackModal>
      )}
      {promptVisible && (
        <PromptModal
          visible={promptVisible}
          hideModal={hidePromptModal}
          prompt={prompt}
        ></PromptModal>
      )}
      {referenceVisible && (
        <ReferenceModal
          visible={referenceVisible}
          hideModal={hideReferenceModal}
          reference={reference}
        ></ReferenceModal>
      )}
    </>
  );
};

interface UserGroupButtonProps extends Partial<IRemoveMessageById> {
  messageId: string;
  content: string;
  regenerateMessage?: () => void;
  sendLoading: boolean;
}

export const UserGroupButton = ({
  content,
  messageId,
  sendLoading,
  removeMessageById,
  regenerateMessage,
}: UserGroupButtonProps) => {
  const { onRemoveMessage, loading } = useRemoveMessage(
    messageId,
    removeMessageById,
  );
  const { t } = useTranslation();

  return (
    <Radio.Group size="small">
      <Radio.Button value="a">
        <CopyToClipboard text={content}></CopyToClipboard>
      </Radio.Button>
      {regenerateMessage && (
        <Radio.Button
          value="b"
          onClick={regenerateMessage}
          disabled={sendLoading}
        >
          <Tooltip title={t('chat.regenerate')}>
            <SyncOutlined spin={sendLoading} />
          </Tooltip>
        </Radio.Button>
      )}
      {removeMessageById && (
        <Radio.Button value="c" onClick={onRemoveMessage} disabled={loading}>
          <Tooltip title={t('common.delete')}>
            <DeleteOutlined spin={loading} />
          </Tooltip>
        </Radio.Button>
      )}
    </Radio.Group>
  );
};
