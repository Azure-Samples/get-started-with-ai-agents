import React, { useState, useEffect, useRef } from "react";
import {
  ChatInput as ChatInputFluent,
  ImperativeControlPlugin,
  ImperativeControlPluginRef,
} from "@fluentui-copilot/react-copilot";
import { ChatInputProps } from "./types";

import styles from "./ChatInput.module.css";

export const ChatInput: React.FC<ChatInputProps> = ({
  onSubmit,
  isGenerating,
  currentUserMessage,
}) => {
  const [inputText, setInputText] = useState<string>("");
  const controlRef = useRef<ImperativeControlPluginRef>(null);

  useEffect(() => {
    if (currentUserMessage !== undefined) {
      controlRef.current?.setInputText(currentUserMessage ?? "");
    }
  }, [currentUserMessage]);
  const onMessageSend = (text: string): void => {
    if (text && text.trim() !== "") {
      onSubmit(text.trim());
      setInputText("");
      controlRef.current?.setInputText("");
    }
  };

  return (
    <div className={styles.chatInputContainer}>
      <ChatInputFluent
        aria-label="Chat Input"
        charactersRemainingMessage={(_value: number) => ``} // needed per fluentui-copilot API
        data-testid="chat-input"
        disableSend={isGenerating}
        history={true}
        isSending={isGenerating}
        onChange={(
          _: React.ChangeEvent<HTMLInputElement>,
          d: { value: string }
        ) => {
          setInputText(d.value);
        }}
        onSubmit={() => {
          onMessageSend(inputText ?? "");
        }}
        placeholderValue="Type your message here..."
      >
        <ImperativeControlPlugin ref={controlRef} />
      </ChatInputFluent>
    </div>
  );
};

export default ChatInput;
