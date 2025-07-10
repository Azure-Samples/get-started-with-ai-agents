# Sample Questions

By default, agents use OpenAI's file search capability with the documents in the `src/files` folder. To enable Azure AI Search instead, set the environment variable before the first time of provision and deployment:

```shell
azd env set USE_AZURE_AI_SEARCH_SERVICE true
```

When Azure AI Search is enabled, the system uses pre-computed embeddings from `src/data/embeddings.csv` rather than processing the individual files in the `src/files` folder.

## Samples for OpenAI's file search
To help you get started for OpenAI's file search, here are some **Sample Prompts**:

- What's the best tent under $200 for two people, and what features does it include?
- What has David Kim purchased in the past, and based on his buying patterns, what other products might interest him?
- Compare hiking boots from different brands in your inventory - which ones offer the best value for durability and comfort?
- How do I set up the Alpine Explorer Tent, and what should I know about its weather protection features?
- I'm planning a 3-day camping trip for my family. What complete setup would you recommend under $500, and why?

## Samples for Azure AI Search
To help you get started for Aure AI Search, here are some **Sample Prompts**:

- Which products have wireless charging capabilities and what are their battery life specifications?
- Find products designed for comfort and temperature control - what features do they offer?
- What care and maintenance instructions are available for electronic products with waterproof features?
- Show me products that integrate with smart home devices or have AI-powered features.
- What troubleshooting guides and warranty information are available for augmented reality products?

