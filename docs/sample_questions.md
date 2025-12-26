# Sample Questions

By default, agents use OpenAI's file search capability with the documents in the `src/files` folder. To enable Azure AI Search instead, set the environment variable before the first time of provision and deployment:

```shell
azd env set USE_AZURE_AI_SEARCH_SERVICE true
```

When Azure AI Search is enabled, the same files in `src/files` are uploaded to your Storage Account blob container and indexed by Azure AI Search.

To help you get started for search, here are some **Sample Prompts**:

- What's the best tent under $200 for two people, and what features does it include?
- Compare hiking boots from different brands in your inventory - which ones offer the best value for durability and comfort?
- How do I set up the Alpine Explorer Tent, and what should I know about its weather protection features?
- I'm planning a 3-day camping trip for my family. What complete setup would you recommend under $500, and why?
