

# Azure AI Search Setup Guide
## Overview
The Azure AI Search feature helps improve the responses from your application by combining the power of large language models (LLMs) with extra context retrieved from an external data source. Simply put, when you ask a question, the agent first searches through a set of relevant documents (stored as embeddings) and then uses this context to provide a more accurate and relevant response. If no relevant context is found, the agent returns the LLM response directly and informs customer that there is no relevant information in the documents.
This AI Search feature is optional and is disabled by default. If you prefer to use it, simply set the environment variable `USE_AZURE_AI_SEARCH_SERVICE` to `true`. Doing so will also trigger the deployment of Azure AI Search resources.

## How does Azure AI Search works?
In our provided example, the application includes a sample dataset containing information about Contoso products. This data was split by 10 sentences, and each chunk of text was transformed into numerical representations called embeddings. These embeddings were created using OpenAI's `text-embedding-3-small` model with `dimensions=100`. The resulting embeddings file (`embeddings.csv`) is located in the `api/data` folder. The agent requires index, capable of both semantic and index search i.e. it can use LLM to search for context in the text fields as well as it can search by embedding vector similarity. The built index also must have the configured vectorizer, which will build the embedding when the agent will apply hybrid search. For search to provide the correct reference, the index must contain the field called "title" and optionally "url" to provide the link, however it is not shown in our sample as we have generated index using files located in `api/files` and there are no links available.


## If you want to use your own dataset
To create a custom embeddings file with your own data, you can use the provided helper class `SearchIndexManager`. Below is a straightforward way to build your own embeddings:
```python
from .api.search_index_manager import SearchIndexManager

search_index_manager = SearchIndexManager(
    endpoint=your_search_endpoint,
    credential=your_credentials,
    index_name=your_index_name,
    dimensions=100,
    model=your_embedding_model,
    deployment_name=your_embedding_model,
    embedding_endpoint=your_search_endpoint_url,
    embed_api_key=embed_api_key,
    embedding_client=embedding_client
)
search_index_manager.build_embeddings_file(
    input_directory=input_directory,
    output_file=output_directory,
    sentences_per_embedding=10
)
```
- Make sure to replace `your_search_endpoint`, `your_credentials`, `your_index_name`, and `embedding_client` with your own Azure service details.
- `your_embedding_model` is the model, used to build embeddings.
- `your_search_endpoint_url` is the url of emedding endpoint, which will be used to create the vectorizer, and `embed_api_key` is the API key to access it.
- Your input data should be placed in the folder specified by `input_directory`.
- `sentences_per_embedding`  parameter specifies the number of sentences used to construct the embedding. The larger this number, the broader the context that will be identified during the similarity search.

## Deploying the Application with AI index search enabled
To deploy your application using the AI index search feature, set the following environment variables locally:
In power shell:
```
$env:USE_AZURE_AI_SEARCH_SERVICE="true"
$env:AZURE_AI_SEARCH_INDEX_NAME="index_sample"
$env:AZURE_AI_EMBED_DEPLOYMENT_NAME="text-embedding-3-small"
```

In bash:
```
export USE_AZURE_AI_SEARCH_SERVICE="true"
export AZURE_AI_SEARCH_INDEX_NAME="index_sample"
export AZURE_AI_EMBED_DEPLOYMENT_NAME="text-embedding-3-small"
```

In cmd:
```
set USE_AZURE_AI_SEARCH_SERVICE=true
set AZURE_AI_SEARCH_INDEX_NAME=index_sample
set AZURE_AI_EMBED_DEPLOYMENT_NAME=text-embedding-3-small
```

- `USE_AZURE_AI_SEARCH_SERVICE`: Enables or disables (default) index search.
- `AZURE_AI_SEARCH_INDEX_NAME`: The Azure Search Index the application will use.
- `AZURE_AI_EMBED_DEPLOYMENT_NAME`: The Azure embedding deployment used to create embeddings.

## Creating the Azure Search Index
 
To utilize index search, you must have an Azure search index. By default, the application uses `index_sample` as the index name. You can create an index either by following these official Azure [instructions](https://learn.microsoft.com/azure/ai-services/agents/how-to/tools/azure-ai-search?tabs=azurecli%2Cpython&pivots=overview-azure-ai-search), or programmatically with the provided helper methods:
```python
# Create Azure Search Index (if it does not yet exist)
await search_index_manager.create_index(raise_on_error=True)

# Upload embeddings to the index
await search_index_manager.upload_documents(embeddings_path)
```
**Important:** If you have already created the index before deploying your application, the system will skip this step and directly use your existing Azure Search Index. The parameter `vector_index_dimensions` is only required if dimension information was not already provided when initially constructing the `SearchIndexManager` object.
