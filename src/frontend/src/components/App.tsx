import React, { useEffect, useState } from "react";
import { AgentPreview } from "./agents/AgentPreview";
import { ThemeProvider } from "./core/theme/ThemeProvider";

const App: React.FC = () => {
  // State to store the agent details
  const [agentDetails, setAgentDetails] = useState({
    id: "loading",
    object: "agent",
    created_at: Date.now(),
    name: "Loading...",
    description: "Loading agent details...",
    model: "default",
    metadata: {
      logo: "robot",
    },
    agentPlaygroundUrl: "",
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
          setAgentDetails(data);
        } else {
          console.error("Failed to fetch agent details");
          // Set fallback data if fetch fails
          setAgentDetails({
            id: "fallback",
            object: "agent",
            created_at: Date.now(),
            name: "AI Agent",
            description: "Could not load agent details",
            model: "default",
            metadata: {
              logo: "robot",
            },
            agentPlaygroundUrl: "",
          });
        }
      } catch (error) {
        console.error("Error fetching agent details:", error);
        // Set fallback data if fetch fails
        setAgentDetails({
          id: "error",
          object: "agent",
          created_at: Date.now(),
          name: "AI Agent",
          description: "Error loading agent details",
          model: "default",
          metadata: {
            logo: "robot",
          },
          agentPlaygroundUrl: "",
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
