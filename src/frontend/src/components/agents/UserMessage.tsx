import { Spinner, ToolbarButton } from "@fluentui/react-components";
import { bundleIcon, EditFilled, EditRegular } from "@fluentui/react-icons";
import { UserMessageV2 as CopilotUserMessage } from "@fluentui-copilot/react-copilot-chat";
import { Suspense } from "react";

import { useFormatTimestamp } from "./hooks/useFormatTimestamp";
import { IUserMessageProps } from "./chatbot/types";

import { Markdown } from "../core/Markdown";

import styles from "./AgentPreviewChatBot.module.css";

const EditIcon = bundleIcon(EditFilled, EditRegular);

export function UserMessage({
  message,
  onEditMessage,
}: IUserMessageProps): JSX.Element {
  const formatTimestamp = useFormatTimestamp();

  return (
    <CopilotUserMessage
      key={message.id}
      actionBar={
        <ToolbarButton
          appearance="transparent"
          aria-label="Edit"
          icon={<EditIcon aria-hidden={true} />}
          onClick={() => {
            onEditMessage(message.id);
          }}
        />
      }
      className={styles.userMessage}
      timestamp={
        message.more?.time ? formatTimestamp(new Date(message.more.time)) : ""
      }
    >
      <Suspense fallback={<Spinner size="small" />}>
        <Markdown content={message.content} />
      </Suspense>
    </CopilotUserMessage>
  );
}
