import chatService from '@/services/chat-service';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

// 存储 key
const STORAGE_KEY_MODEL = 'chat_selected_model';
const STORAGE_KEY_KBS = 'chat_selected_kbs';
const STORAGE_KEY_ENABLE_KB = 'chat_enable_knowledge';

// 模型类型
export interface AvailableModel {
  llm_name: string;
  llm_factory: string;
  model_type: string;
}

// 知识库类型
export interface AvailableKnowledgebase {
  id: string;
  name: string;
  description: string;
  doc_num: number;
}

/**
 * 获取可用模型列表
 */
export const useFetchAvailableModels = () => {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['availableModels'],
    queryFn: async () => {
      const { data: res } = await chatService.availableModels();
      return res?.data ?? [];
    },
    staleTime: 5 * 60 * 1000, // 5分钟内不重新请求
  });

  return {
    models: data as AvailableModel[] | undefined,
    loading: isLoading,
    refetch,
  };
};

/**
 * 获取可用知识库列表
 */
export const useFetchAvailableKnowledgebases = () => {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['availableKbs'],
    queryFn: async () => {
      const { data: res } = await chatService.availableKbs();
      return res?.data ?? [];
    },
    staleTime: 5 * 60 * 1000, // 5分钟内不重新请求
  });

  return {
    knowledgebases: data as AvailableKnowledgebase[] | undefined,
    loading: isLoading,
    refetch,
  };
};

/**
 * 管理聊天选项状态（模型和知识库选择）
 */
export const useChatSelections = () => {
  // 初始化时从 localStorage 读取
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(STORAGE_KEY_MODEL) || '';
    }
    return '';
  });

  const [selectedKbs, setSelectedKbs] = useState<string[]>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY_KBS);
      if (stored) {
        try {
          return JSON.parse(stored);
        } catch {
          return [];
        }
      }
    }
    return [];
  });

  // 知识库启用开关状态
  const [enableKnowledge, setEnableKnowledge] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY_ENABLE_KB);
      return stored === 'true';
    }
    return false;
  });

  // 保存模型选择到 localStorage
  const handleSelectModel = useCallback((modelName: string) => {
    setSelectedModel(modelName);
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY_MODEL, modelName);
    }
  }, []);

  // 保存知识库选择到 localStorage
  const handleSelectKbs = useCallback((kbIds: string[]) => {
    setSelectedKbs(kbIds);
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY_KBS, JSON.stringify(kbIds));
    }
  }, []);

  // 保存知识库启用状态到 localStorage
  const handleEnableKnowledge = useCallback((enabled: boolean) => {
    setEnableKnowledge(enabled);
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY_ENABLE_KB, String(enabled));
    }
  }, []);

  return {
    selectedModel,
    selectedKbs,
    enableKnowledge,
    setSelectedModel: handleSelectModel,
    setSelectedKbs: handleSelectKbs,
    setEnableKnowledge: handleEnableKnowledge,
  };
};
