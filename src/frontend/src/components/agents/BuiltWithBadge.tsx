import { ReactNode, useEffect, useState } from "react";
import { Caption1Strong } from "@fluentui/react-components";
import { ArrowRight16Filled } from "@fluentui/react-icons";
import clsx from "clsx";

import { AIFoundryLogo } from "../icons/AIFoundryLogo";
import styles from "./BuiltWithBadge.module.css";

interface AzureConfig {
  subscriptionId: string;
  tenantId: string;
  resourceGroup: string;
  resourceName: string;
  projectName: string;
  wsid: string;
}

export function BuiltWithBadge({
  className,
}: {
  className?: string;
}): ReactNode {
  const [azureConfig, setAzureConfig] = useState<AzureConfig | null>(null);

  useEffect(() => {
    const fetchAzureConfig = async () => {
      try {
        const response = await fetch("/config/azure");
        if (response.ok) {
          const config = await response.json();
          setAzureConfig(config);
        } else {
          console.error("Failed to fetch Azure configuration");
        }
      } catch (error) {
        console.error("Error fetching Azure configuration:", error);
      }
    };

    fetchAzureConfig();
  }, []);

  const handleClick = () => {
    if (azureConfig) {
      const { wsid, tenantId } = azureConfig;
      const azureAiUrl = `https://ai.azure.com/resource/agentsList?wsid=${encodeURIComponent(
        wsid
      )}&tid=${tenantId}`;
      window.open(azureAiUrl, "_blank");
    } else {
      console.log("Azure configuration not available");
    }
  };
  return (
    <button
      className={clsx(styles.badge, className)}
      onClick={handleClick}
      type="button"
    >
      {" "}
      <span className={styles.logo}>
        {/* Azure AI Foundry logo */}
        <AIFoundryLogo />
      </span>
      <Caption1Strong className={styles.description}>
        Build & deploy AI agents with
      </Caption1Strong>
      <Caption1Strong className={styles.brand}>
        Azure AI Foundry <ArrowRight16Filled aria-hidden={true} />
      </Caption1Strong>
    </button>
  );
}
