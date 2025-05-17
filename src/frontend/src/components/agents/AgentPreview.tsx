import { ReactNode, useState, useMemo, useEffect } from "react";
import {
  Body1,
  Button,
  Caption1,
  Spinner,
  Title2,
} from "@fluentui/react-components";
import { ChatRegular, MoreHorizontalRegular } from "@fluentui/react-icons";

import { AgentIcon } from "./AgentIcon";
import { SettingsPanel } from "../core/SettingsPanel";
import { AgentPreviewChatBot } from "./AgentPreviewChatBot";
import { MenuButton } from "../core/MenuButton/MenuButton";
import { IChatItem } from "./chatbot/types";

import styles from "./AgentPreview.module.css";

interface IAgent {
  id: string;
  object: string;
  created_at: number;
  name: string;
  description?: string | null;
  model: string;
  instructions?: string;
  tools?: Array<{ type: string }>;
  top_p?: number;
  temperature?: number;
  tool_resources?: {
    file_search?: {
      vector_store_ids?: string[];
    };
    [key: string]: any;
  };
  metadata?: Record<string, any>;
  response_format?: "auto" | string;
}

interface IAgentPreviewProps {
  resourceId: string;
  agentDetails: IAgent;
}

export function AgentPreview({ agentDetails }: IAgentPreviewProps): ReactNode {
  const [isSettingsPanelOpen, setIsSettingsPanelOpen] = useState(false);
  const [messageList, setMessageList] = useState<IChatItem[]>([]);
  const [isResponding, setIsResponding] = useState(false);
  const [isLoadingChatHistory, setIsLoadingChatHistory] = useState(true);

  const loadChatHistory = async () => {
    try {
      const response = await fetch("/chat/history", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      if (response.ok) {
        const json_response: Array<{
          role: string;
          content: string;
          created_at: string;
          annotations?: any[];
        }> = await response.json();

        // It's generally better to build the new list and set state once
        const historyMessages: IChatItem[] = [];
        const reversedResponse = [...json_response].reverse();

        for (const entry of reversedResponse) {
          if (entry.role === "user") {
            historyMessages.push({
              id: ``,
              content: entry.content,
              role: "user",
              more: { time: entry.created_at }, // Or use timestamp from history if available
            });
          } else {
            historyMessages.push({
              id: `assistant-hist-${Date.now()}-${Math.random()}`, // Ensure unique ID
              content: entry.content,
              role: "assistant", // Assuming 'assistant' role for non-user
              isAnswer: true, // Assuming this property for assistant messages
              more: { time: entry.created_at }, // Or use timestamp from history if available
              // annotations: entry.annotations, // If you plan to use annotations
            });
          }
        }
        setMessageList((prev) => [...historyMessages, ...prev]); // Prepend history
      } else {
        const errorChatItem = createAssistantMessageDiv(); // This will add an empty message first
        appendAssistantMessage(
          errorChatItem,
          "Error occurs while loading chat history!",
          false
        );
      }
      setIsLoadingChatHistory(false);
    } catch (error) {
      console.error("Failed to load chat history:", error);
      const errorChatItem = createAssistantMessageDiv();
      appendAssistantMessage(
        errorChatItem,
        "Error occurs while loading chat history!",
        false
      );
      setIsLoadingChatHistory(false);
    }
  };

  useEffect(() => {
    loadChatHistory();
  }, []);

  const handleSettingsPanelOpenChange = (isOpen: boolean) => {
    setIsSettingsPanelOpen(isOpen);
  };

  const newThread = () => {
    setMessageList([]);
    deleteAllCookies();
  };

  const deleteAllCookies = (): void => {
    document.cookie.split(";").forEach((cookieStr: string) => {
      const trimmedCookieStr = cookieStr.trim();
      const eqPos = trimmedCookieStr.indexOf("=");
      const name =
        eqPos > -1 ? trimmedCookieStr.substring(0, eqPos) : trimmedCookieStr;
      document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
    });
  };

  const onSend = async (message: string) => {
    const userMessage: IChatItem = {
      id: `user-${Date.now()}`,
      content: message,
      role: "user",
      more: { time: new Date().toISOString() },
    };

    setMessageList((prev) => [...prev, userMessage]);

    try {
      const postData = { message: message };
      // IMPORTANT: Add credentials: 'include' if server cookies are critical
      // and if your backend is on the same domain or properly configured for cross-site cookies.
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(postData),
        credentials: "include", // <--- allow cookies to be included
      });

      // Log out the response status in case there’s an error
      console.log(
        "[ChatClient] Response status:",
        response.status,
        response.statusText
      );

      // If server returned e.g. 400 or 500, that’s not an exception, but we can check manually:
      if (!response.ok) {
        console.error(
          "[ChatClient] Response not OK:",
          response.status,
          response.statusText
        );
        return;
      }

      if (!response.body) {
        throw new Error(
          "ReadableStream not supported or response.body is null"
        );
      }

      console.log("[ChatClient] Starting to handle streaming response...");
      handleMessages(response.body);
    } catch (error: any) {
      setIsResponding(false);
      if (error.name === "AbortError") {
        console.log("[ChatClient] Fetch request aborted by user.");
      } else {
        console.error("[ChatClient] Fetch failed:", error);
      }
    } finally {
      // Reset the controller once the request is finished or cancelled
      //TODO
      // this.abortController = null;
    }
  };

  const handleMessages = (
    stream: ReadableStream<Uint8Array<ArrayBufferLike>>
  ) => {
    let chatItem: IChatItem | null = null;
    let accumulatedContent = "";
    let isStreaming = true;
    let buffer = "";

    // Create a reader for the SSE stream
    const reader = stream.getReader();
    const decoder = new TextDecoder();

    const readStream = async () => {
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log("[ChatClient] SSE stream ended by server.");
          break;
        }

        // Convert the incoming Uint8Array to text
        const textChunk = decoder.decode(value, { stream: true });
        console.log("[ChatClient] Raw chunk from stream:", textChunk);

        buffer += textChunk;
        let boundary = buffer.indexOf("\n");

        // We process line-by-line.
        while (boundary !== -1) {
          const chunk = buffer.slice(0, boundary).trim();
          buffer = buffer.slice(boundary + 1);

          console.log("[ChatClient] SSE line:", chunk); // log each line we extract

          if (chunk.startsWith("data: ")) {
            // Attempt to parse JSON
            const jsonStr = chunk.slice(6);
            let data;
            try {
              data = JSON.parse(jsonStr);
            } catch (err) {
              console.error("[ChatClient] Failed to parse JSON:", jsonStr, err);
              boundary = buffer.indexOf("\n");
              continue;
            }

            console.log("[ChatClient] Parsed SSE event:", data);

            if (data.error) {
              if (!chatItem) {
                chatItem = createAssistantMessageDiv();
                console.log(
                  "[ChatClient] Created new messageDiv for assistant."
                );
              }

              setIsResponding(false);
              appendAssistantMessage(
                chatItem,
                data.error.message || "An error occurred.",
                false
              );
              return;
            }

            // Check the data type to decide how to update the UI
            if (data.type === "stream_end") {
              // End of the stream
              console.log("[ChatClient] Stream end marker received.");
              setIsResponding(false);
              break;
            } else if (data.type === "thread_run") {
              // Log the run status info
              console.log("[ChatClient] Run status info:", data.content);
            } else {
              // If we have no messageDiv yet, create one
              if (!chatItem) {
                // TODO
                chatItem = createAssistantMessageDiv();
                console.log(
                  "[ChatClient] Created new messageDiv for assistant."
                );
              }

              if (data.type === "completed_message") {
                clearAssistantMessage(chatItem);
                accumulatedContent = data.content;
                isStreaming = false;
                console.log(
                  "[ChatClient] Received completed message:",
                  accumulatedContent
                );

                // TODO: Hide spinner
                // document.getElementById("generating-message").style.display = "none";
                setIsResponding(false);
              } else {
                accumulatedContent += data.content;
                console.log(
                  "[ChatClient] Received streaming chunk:",
                  data.content
                );
              }

              // Update the UI with the accumulated content
              appendAssistantMessage(chatItem, accumulatedContent, isStreaming);
            }
          }

          boundary = buffer.indexOf("\n");
        }
      }
    };

    // Catch errors from the stream reading process
    readStream().catch((error) => {
      console.error("[ChatClient] Stream reading failed:", error);
    });
  };

  const createAssistantMessageDiv: () => IChatItem = () => {
    var item = { id: "unknown", content: "", isAnswer: true, more: { time: new Date().toISOString() } };
    setMessageList((prev) => [...prev, item]);
    return item;
  };

  const appendAssistantMessage = (
    chatItem: IChatItem,
    accumulatedContent: string,
    isStreaming: boolean
  ) => {
    try {
      // Preprocess content to convert citations to links using the updated annotation data
      const preprocessedContent = accumulatedContent;
      // Convert the accumulated content to HTML using markdown-it
      let htmlContent = preprocessedContent;
      if (!chatItem) {
        throw new Error("Message content div not found in the template.");
      }

      // Set the innerHTML of the message text div to the HTML content
      chatItem.content = htmlContent;
      setMessageList((prev) => {
        const before = prev;
        console.log("[ChatClient] Message list before update:", before);
        const after = [...prev.slice(0, -1), { ...chatItem }]; // Update the last message in the list
        console.log("[ChatClient] Message list after update:", after);
        return after;
      });

      // Use requestAnimationFrame to ensure the DOM has updated before scrolling
      // Only scroll if stop streaming
      if (!isStreaming) {
        requestAnimationFrame(() => {
          // TODO
          // this.scrollToBottom();
        });
      }
    } catch (error) {
      console.error("Error in appendAssistantMessage:", error);
    }
  };

  const clearAssistantMessage = (chatItem: IChatItem) => {
    if (chatItem) {
      chatItem.content = "";
    }
  };
  const menuItems = [
    {
      key: "settings",
      children: "Settings",
      onClick: () => {
        setIsSettingsPanelOpen(true);
      },
    },
    {
      key: "terms",
      children: (
        <a
          className={styles.externalLink}
          href="https://aka.ms/aistudio/terms"
          target="_blank"
          rel="noopener noreferrer"
        >
          Terms of Use
        </a>
      ),
    },
    {
      key: "privacy",
      children: (
        <a
          className={styles.externalLink}
          href="https://go.microsoft.com/fwlink/?linkid=521839"
          target="_blank"
          rel="noopener noreferrer"
        >
          Privacy
        </a>
      ),
    },
    {
      key: "feedback",
      children: "Send Feedback",
      onClick: () => {
        // Handle send feedback click
        alert("Thank you for your feedback!");
      },
    },
  ];

  const chatContext = useMemo(
    () => ({
      messageList,
      isResponding,
      onSend,
    }),
    [messageList, isResponding]
  );

  return (
    <div className={styles.container}>
      <div className={styles.topBar}>
        <div className={styles.leftSection}>
          {messageList.length > 0 && (
            <>
              <AgentIcon
                alt=""
                iconClassName={styles.agentIcon}
                iconName={agentDetails.metadata?.logo}
              />
              <Body1 className={styles.agentName}>{agentDetails.name}</Body1>
            </>
          )}
        </div>
        <div className={styles.rightSection}>
          {" "}
          <Button
            appearance="subtle"
            icon={<ChatRegular aria-hidden={true} />}
            onClick={newThread}
          >
            New Chat
          </Button>{" "}
          <MenuButton
            menuButtonText=""
            menuItems={menuItems}
            menuButtonProps={{
              appearance: "subtle",
              icon: <MoreHorizontalRegular />,
              "aria-label": "Settings",
            }}
          />
        </div>
      </div>
      <div className={styles.content}>
        {isLoadingChatHistory ? (
          <Spinner label={"Loading chat history..."} />
        ) : (
          <>
            {messageList.length === 0 && (
              <div className={styles.emptyChatContainer}>
                <AgentIcon
                  alt=""
                  iconClassName={styles.emptyStateAgentIcon}
                  iconName={agentDetails.metadata?.logo}
                />
                <Caption1 className={styles.agentName}>
                  {agentDetails.name}
                </Caption1>
                <Title2>How can I help you today?</Title2>
              </div>
            )}
            <AgentPreviewChatBot
              agentName={agentDetails.name}
              agentLogo={agentDetails.metadata?.logo}
              chatContext={chatContext}
            />
          </>
        )}
      </div>

      {/* Settings Panel */}
      <SettingsPanel
        isOpen={isSettingsPanelOpen}
        onOpenChange={handleSettingsPanelOpenChange}
      />
    </div>
  );
}
