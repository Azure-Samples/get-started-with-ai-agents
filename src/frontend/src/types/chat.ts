export interface IFileEntity {
  id: string;
  name: string;
  contentType: string;
  size?: number;
  url?: string;
}

export interface IMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  message_files?: IFileEntity[];
  annotations?: any[];
  fileReferences?: Map<string, any>;
  duration?: number;
  usageInfo?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  more?: {
    time?: string;
  };
}