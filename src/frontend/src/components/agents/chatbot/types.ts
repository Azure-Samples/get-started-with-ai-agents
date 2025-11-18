/**
 * Common type definitions for chat components
 */

export interface IFileEntity {
  id: string;
  name: string;
  size: number;
  status?:
    | "pending"
    | "uploading"
    | "uploaded"
    | "error"
    | "deleting"
    | "processed";
  type: string;
  progress?: boolean;
  supportFileType?: string;
  createdDate?: number;
  originalFile?: File;
  uploadedId?: string;
  base64Url?: string;
  url?: string;
  error?: string;
  isRemote?: boolean;
}

export interface IChatItem {
  id: string;
  role?: string;
  content: string;
  isAnswer?: boolean;
  annotations?: any[];
  fileReferences?: Map<string, any>;
  duration?: number;
  message_files?: IFileEntity[];
  usageInfo?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  more?: {
    time?: string;
  };
}

export interface ChatInputProps {
  onSubmit: (message: string) => void;
  isGenerating: boolean;
  currentUserMessage?: string;
}

export interface IAssistantMessageProps {
  message: IChatItem;
  agentLogo?: string;
  agentName?: string;
  loadingState?: "loading" | "streaming" | "none";
  showUsageInfo?: boolean;
  onDelete?: (messageId: string) => Promise<void>;
}

export interface IUserMessageProps {
  message: IChatItem;
  onEditMessage: (messageId: string) => void;
}

export interface ChatContextType {
  messageList: IChatItem[];
  isResponding: boolean;
  onSend: (message: string) => void;
}

export interface AgentPreviewChatBotProps {
  agentName?: string;
  agentLogo?: string;
  chatContext: ChatContextType;
}
