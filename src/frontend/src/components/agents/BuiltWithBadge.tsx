import { ReactNode } from "react";
import { Caption1Strong } from "@fluentui/react-components";
import { ArrowRight16Filled } from "@fluentui/react-icons";
import clsx from "clsx";

import { AIFoundryLogo } from "../icons/AIFoundryLogo";
import styles from "./BuiltWithBadge.module.css";

export function BuiltWithBadge({
  className,
  agentPlaygroundUrl
}: {
  className?: string;
  agentPlaygroundUrl?: string;
}): ReactNode {

  const handleClick = () => {
    window.open(agentPlaygroundUrl, "_blank");
  };
  return (
    <button
      className={clsx(styles.badge, className)}
      onClick={handleClick}
      type="button"
    >
      {" "}
      <span className={styles.logo}>
        {/* Microsoft Foundry logo */}
        <AIFoundryLogo />
      </span>
      <Caption1Strong className={styles.description}>
        Build & deploy AI agents with
      </Caption1Strong>
      <Caption1Strong className={styles.brand}>
        Microsoft Foundry <ArrowRight16Filled aria-hidden={true} />
      </Caption1Strong>
    </button>
  );
}
