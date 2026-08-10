import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { AssistantMessage } from "./AssistantMessage";
import { UserMessage } from "./UserMessage";
import { ChatInput } from "./chatbot/ChatInput";
import { AgentPreviewChatBotProps } from "./chatbot/types";

import styles from "./AgentPreviewChatBot.module.css";
import clsx from "clsx";

// Distance from bottom (in px) that still counts as "at the bottom".
const AT_BOTTOM_THRESHOLD_PX = 40;

export function AgentPreviewChatBot({
  agentName,
  agentLogo,
  chatContext,
}: AgentPreviewChatBotProps): React.JSX.Element {
  const [currentUserMessage, setCurrentUserMessage] = useState<
    string | undefined
  >();

  const messageListFromChatContext = useMemo(
    () => chatContext.messageList ?? [],
    [chatContext.messageList]
  );

  const onEditMessage = (messageId: string) => {
    const selectedMessage = messageListFromChatContext.find(
      (message) => !message.isAnswer && message.id === messageId
    )?.content;
    setCurrentUserMessage(selectedMessage);
  };

  const isEmpty = messageListFromChatContext.length === 0;

  // Ref to the scrollable messages container.
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Whether we should auto-follow the bottom. Starts pinned so the initial
  // history load lands at the newest message. Flips to false when the user
  // scrolls up, and back to true when they scroll near the bottom again.
  const stickToBottomRef = useRef(true);

  const scrollToBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, []);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    stickToBottomRef.current = distanceFromBottom <= AT_BOTTOM_THRESHOLD_PX;
  }, []);

  // React-driven auto-scroll: fires on every message list mutation (history
  // load, new message, streaming delta) before the browser paints.
  useLayoutEffect(() => {
    if (stickToBottomRef.current) {
      scrollToBottom();
    }
  }, [messageListFromChatContext, scrollToBottom]);

  // Safety net: observe content size changes (async renders, images, code
  // blocks, markdown reflow) and keep pinned to bottom while sticking.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const onResize = () => {
      if (stickToBottomRef.current) {
        scrollToBottom();
      }
    };

    const ro = new ResizeObserver(onResize);
    ro.observe(el);
    for (const child of Array.from(el.children)) {
      ro.observe(child);
    }
    // Ensure initial pin after mount.
    scrollToBottom();

    return () => ro.disconnect();
  }, [isEmpty, scrollToBottom]);

  return (
    <div
      className={clsx(
        styles.chatContainer,
        isEmpty ? styles.emptyChatContainer : undefined
      )}
    >
      {!isEmpty ? (
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className={styles.copilotChatContainer}
        >
          {messageListFromChatContext.map((message, index, messageList) =>
            message.isAnswer ? (
              <AssistantMessage
                key={message.id}
                agentLogo={agentLogo}
                agentName={agentName}
                loadingState={
                  index === messageList.length - 1 && chatContext.isResponding
                    ? "loading"
                    : "none"
                }
                message={message}
              />
            ) : (
              <UserMessage
                key={message.id}
                message={message}
                onEditMessage={onEditMessage}
              />
            )
          )}
        </div>
      ) : (
        // Empty div needed for proper animation when transitioning to non-empty state
        <div />
      )}
      <div className={styles.inputContainer}>
        <ChatInput
          currentUserMessage={currentUserMessage}
          isGenerating={chatContext.isResponding}
          onSubmit={chatContext.onSend}
        />
      </div>
    </div>
  );
}
