import { IReference } from '@/interfaces/database/chat';
import { DatabaseOutlined, FileTextOutlined } from '@ant-design/icons';
import { Card, Empty, Modal, Space, Tag, Typography } from 'antd';
import { memo } from 'react';

const { Text, Paragraph } = Typography;

interface IProps {
  visible: boolean;
  hideModal: () => void;
  reference?: IReference;
}

const ReferenceModal = ({ visible, hideModal, reference }: IProps) => {
  const chunks = reference?.chunks ?? [];

  return (
    <Modal
      title={
        <Space>
          <DatabaseOutlined />
          <span>引用片段</span>
        </Space>
      }
      open={visible}
      onCancel={hideModal}
      footer={null}
      width={800}
      styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
    >
      {chunks.length > 0 ? (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {chunks.map((chunk) => (
            <Card
              key={chunk.id}
              size="small"
              title={
                <Space>
                  <FileTextOutlined />
                  <Text strong>{chunk.document_name}</Text>
                  {typeof chunk.similarity === 'number' &&
                    !isNaN(chunk.similarity) && (
                      <Tag color="blue">
                        相似度: {(chunk.similarity * 100).toFixed(1)}%
                      </Tag>
                    )}
                </Space>
              }
            >
              <Paragraph
                ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
                style={{ margin: 0 }}
              >
                {chunk.content}
              </Paragraph>
            </Card>
          ))}
        </Space>
      ) : (
        <Empty description="暂无引用信息" />
      )}
    </Modal>
  );
};

export default memo(ReferenceModal);
