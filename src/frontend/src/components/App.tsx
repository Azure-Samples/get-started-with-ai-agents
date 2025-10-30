import React, { useEffect, useState } from "react";
import { AgentPreview } from "./agents/AgentPreview";
import { ThemeProvider } from "./core/theme/ThemeProvider";

const App: React.FC = () => {
  // State to store the agent details
  const [agentDetails, setAgentDetails] = useState({
    id: "loading",
    object: "agent",
    created_at: Date.now(),
    name: "Concat AG",
    description: "Loading agent details...",
    model: "default",
    metadata: {
      logo: "ConcatAG_Logo_Black.svg",
    },
  });

  // Fetch agent details when component mounts
  useEffect(() => {
    const fetchAgentDetails = async () => {
      try {
        const response = await fetch("/agent", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
        });

        if (response.ok) {
          const data = await response.json();
          console.log(
            "Agent details fetched successfully:",
            JSON.stringify(data)
          );
          console.log(
            "Agent details fetched successfully 2:",
            JSON.stringify(response)
          );
          const updatedData = {
            ...data,
            name:
              data?.name && data.name !== "agent-template-assistant"
                ? data.name
                : "Concat AG",
            metadata: {
              ...data?.metadata,
              logo: "ConcatAG_Logo_Black.svg",
            },
          };
          setAgentDetails(updatedData);
        } else {
          console.error("Failed to fetch agent details");
          // Set fallback data if fetch fails
          setAgentDetails({
            id: "fallback",
            object: "agent",
            created_at: Date.now(),
            name: "Concat AG",
            description: "Could not load agent details",
            model: "default",
            metadata: {
              logo: "ConcatAG_Logo_Black.svg",
            },
          });
        }
      } catch (error) {
        console.error("Error fetching agent details:", error);
        // Set fallback data if fetch fails
        setAgentDetails({
          id: "error",
          object: "agent",
          created_at: Date.now(),
          name: "Concat AG",
          description: "Error loading agent details",
          model: "default",
          metadata: {
            logo: "ConcatAG_Logo_Black.svg",
          },
        });
      }
    };

    fetchAgentDetails();
  }, []);

  return (
    <ThemeProvider>
      <div className="app-container">
        <AgentPreview
          resourceId="sample-resource-id"
          agentDetails={agentDetails}
        />
      </div>
    </ThemeProvider>
  );
};

export default App;
