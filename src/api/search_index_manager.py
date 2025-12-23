from typing import Any, Dict, Literal, Optional
from enum import Enum
import logging

from azure.core.credentials_async import AsyncTokenCredential
from azure.search.documents.indexes.aio import SearchIndexClient, SearchIndexerClient
from azure.core.exceptions import HttpResponseError
from azure.search.documents.indexes.models import (
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticSearch,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
    SearchIndexerDataSourceConnection,
    SearchIndexerDataContainer,
    SearchIndexer,
    FieldMapping,
    IndexingParameters,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    SearchIndexerSkillset,
    AzureOpenAIEmbeddingSkill,
    SplitSkill,
    IndexingParametersConfiguration,
    SearchIndexerIndexProjection,
    SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjectionsParameters,
    IndexProjectionMode,
)


logger = logging.getLogger(__name__)


class ResourceStatus(Enum):
    """Status of a resource operation."""
    CREATED = "created"
    EXISTING = "existing"
    FAILED = "failed"


class SearchIndexManager:
    """
    The class for searching of context for user queries.

    :param endpoint: The search endpoint to be used.
    :param credential: The credential to be used for the search.
    :param index_name: The name of an index to get or to create.
    :param dimensions: The number of dimensions in the embedding. Set this parameter only if
                       embedding model accepts dimensions parameter.
    :param model: The embedding model to be used,
                  must be the same as one use to build the file with embeddings.
    :param deployment_name: The name of the embedding deployment.
    :param embeddings_endpoint: The the endpoint used for embedding.
    :param embed_api_key: The api key used by the embedding resource.
    :param embedding_client: The embedding client, used t build the embedding. Needed only
                             to create embedding file. Not used in inference time.
    """
    
    MIN_DIFF_CHARACTERS_IN_LINE = 5
    MIN_LINE_LENGTH = 5
    
    _SEMANTIC_CONFIG = "semantic_search"
    _EMBEDDING_CONFIG = "embedding_config"
    _VECTORIZER = "search_vectorizer"


    def __init__(
            self,
            endpoint: str,
            credential: AsyncTokenCredential,
            index_name: str,
            dimensions: Optional[int],
            model: str,
            deployment_name: str,
            embedding_endpoint: str, 
            embed_api_key: Optional[str],
            embedding_client: Optional[Any] = None
        ) -> None:
        """Constructor."""
        self._dimensions = dimensions
        self._index_name = index_name
        self._embeddings_endpoint = embedding_endpoint
        self._endpoint = endpoint
        self._credential = credential
        self._index = None
        self._embedding_model = model
        self._embedding_deployment = deployment_name
        self._embed_api_key = embed_api_key
        self._client = None
        self._embedding_client = embedding_client


    def _check_dimensions(self, vector_index_dimensions: Optional[int] = None) -> int:
        """
        Check that the dimensions are set correctly.

        :return: the correct vector index dimensions.
        :raises: Value error if both dimensions of embedding model and vector_index_dimensions are not set
                 or both of them set and they do not equal each other.
        """
        if vector_index_dimensions is None:
            if self._dimensions is None:
                raise ValueError(
                    "No embedding dimensions were provided in neither dimensions in the constructor nor in vector_index_dimensions"
                    "Dimensions are needed to build the search index, please provide the vector_index_dimensions.")
            vector_index_dimensions = self._dimensions
        if self._dimensions is not None and vector_index_dimensions != self._dimensions:
            raise ValueError("vector_index_dimensions is different from dimensions provided to constructor.")
        return vector_index_dimensions
    
    async def create_index_maybe(self, vector_index_dimensions: Optional[int] = None) -> ResourceStatus:
        """
        Create index if not exists.

        :param vector_index_dimensions: The number of dimensions in the vector index.
        :return: ResourceStatus.CREATED, ResourceStatus.EXISTING, or ResourceStatus.FAILED
        """
        vector_index_dimensions = self._check_dimensions(vector_index_dimensions)
        try:
            self._index = await self._index_create(vector_index_dimensions)
            logger.info(f"Search index '{self._index_name}' created successfully with {vector_index_dimensions} embedding dimensions.")
            return ResourceStatus.CREATED
        except HttpResponseError:
            try:
                async with SearchIndexClient(endpoint=self._endpoint, credential=self._credential) as ix_client:
                    self._index = await ix_client.get_index(self._index_name)
                    logger.info(f"Search index '{self._index_name}' already exists. Using existing index with {vector_index_dimensions} embedding dimensions.")
                    return ResourceStatus.EXISTING
            except Exception as e:
                logger.error(f"Failed to create or retrieve index '{self._index_name}': {e}")
                return ResourceStatus.FAILED
        
    async def _index_create(self, vector_index_dimensions: int) -> SearchIndex:
        """
        Create the index.

        :param vector_index_dimensions: The number of dimensions in the vector index. This parameter is
               needed if the embedding parameter cannot be set for the given model.
               See the embedding model documentation:
               https://platform.openai.com/docs/models#embeddings
        :return: The newly created search index.
        """
        async with SearchIndexClient(endpoint=self._endpoint, credential=self._credential) as ix_client:
            fields = [
                SearchField(
                    name="chunk_id",
                    type=SearchFieldDataType.String,
                    key=True,
                    searchable=True,
                    analyzer_name="keyword"
                ),
                SimpleField(name="parent_id", type=SearchFieldDataType.String, filterable=True),
                SearchField(name="chunk", searchable=True, type=SearchFieldDataType.String, hidden=False),
                SearchField(name="title", type=SearchFieldDataType.String, hidden=False),
                SearchField(
                    name="text_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    vector_search_dimensions=vector_index_dimensions,
                    searchable=True,
                    vector_search_profile_name=SearchIndexManager._EMBEDDING_CONFIG
                ),
            ]
            vector_search = VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name=SearchIndexManager._EMBEDDING_CONFIG,
                        algorithm_configuration_name="embed-algorithms-config",
                        vectorizer_name=SearchIndexManager._VECTORIZER
                    )
                ],
                algorithms=[HnswAlgorithmConfiguration(name="embed-algorithms-config")],
                vectorizers=[
                    AzureOpenAIVectorizer(
                        vectorizer_name=SearchIndexManager._VECTORIZER,
                        parameters=AzureOpenAIVectorizerParameters(
                            resource_url=self._embeddings_endpoint,
                            deployment_name=self._embedding_deployment,
                            api_key=self._embed_api_key,
                            model_name=self._embedding_model
                        )
                    )
                ]
            )
            semantic_search = SemanticSearch(
                default_configuration_name=SearchIndexManager._SEMANTIC_CONFIG,
                configurations=[
                    SemanticConfiguration(
                        name=SearchIndexManager._SEMANTIC_CONFIG,
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="title"),
                            content_fields=[
                                SemanticField(field_name="chunk"),
                            ]
                        )
                    )
                ] 
            )
            search_index = SearchIndex(
                name=self._index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search)
            new_index = await ix_client.create_index(search_index)
        return new_index

    async def create_datasource_maybe(
        self,
        datasource_name: str,
        container_name: str,
        connection_string: str,
    ) -> ResourceStatus:
        """
        Create or get data source for blob storage.

        :param datasource_name: Name of the datasource to create or retrieve
        :param storage_account_endpoint: Azure Storage account endpoint
        :param container_name: Name of blob container
        :param connection_string: Connection string for blob storage
        :return: ResourceStatus.CREATED, ResourceStatus.EXISTING, or ResourceStatus.FAILED
        """
        if not self._endpoint:
            logger.error("Search endpoint is required.")
            return ResourceStatus.FAILED

        data_source = SearchIndexerDataSourceConnection(
            name=datasource_name,
            type="azureblob",
            connection_string=connection_string,
            container=SearchIndexerDataContainer(name=container_name),
        )

        async with SearchIndexerClient(endpoint=self._endpoint, credential=self._credential) as indexer_client:
            try:
                await indexer_client.get_data_source_connection(datasource_name)
                logger.info(f"Data source '{datasource_name}' already exists. Using existing data source.")
                return ResourceStatus.EXISTING
            except HttpResponseError:
                try:
                    await indexer_client.create_data_source_connection(data_source)
                    logger.info(f"Data source '{datasource_name}' created successfully.")
                    return ResourceStatus.CREATED
                except Exception as e:
                    logger.error(f"Failed to create data source '{datasource_name}': {e}")
                    return ResourceStatus.FAILED

    async def create_skillset_maybe(
        self,
        skillset_name: str,
        target_index_name: str,
        split_mode: Literal["pages"] = "pages",
        max_page_length: int = 2000,
        page_overlap_length: int = 500,
    ) -> ResourceStatus:
        """
        Create skillset with split and embedding skills.

        :param skillset_name: Name of the skillset
        :param target_index_name: Target index for projections
        :param split_mode: Text split mode (pages)
        :param max_page_length: Maximum page length for splitting
        :param page_overlap_length: Page overlap length for splitting
        :return: ResourceStatus.CREATED, ResourceStatus.EXISTING, or ResourceStatus.FAILED
        """
        if not self._endpoint:
            logger.error("Search endpoint is required.")
            return ResourceStatus.FAILED

        split_skill = SplitSkill(
            name="document_chunking_skill",
            description="Chunks documents into overlapping text segments for embedding and indexing",
            context="/document",
            text_split_mode=split_mode,
            maximum_page_length=max_page_length,
            page_overlap_length=page_overlap_length,
            inputs=[InputFieldMappingEntry(name="text", source="/document/content")],
            outputs=[OutputFieldMappingEntry(name="textItems", target_name="pages")],
        )

        embedding_skill = AzureOpenAIEmbeddingSkill(
            name="embedding_generation_skill",
            description="Generates vector embeddings for document chunks using Azure OpenAI",
            context="/document/pages/*",
            resource_url=self._embeddings_endpoint,
            deployment_name=self._embedding_deployment,
            model_name=self._embedding_model,
            inputs=[InputFieldMappingEntry(name="text", source="/document/pages/*")],
            outputs=[OutputFieldMappingEntry(name="embedding", target_name="text_vector")],
            dimensions=self._dimensions
        )

        index_projection = SearchIndexerIndexProjection(
            selectors=[
                SearchIndexerIndexProjectionSelector(
                    target_index_name=target_index_name,
                    parent_key_field_name="parent_id",
                    source_context="/document/pages/*",
                    mappings=[
                        InputFieldMappingEntry(name="text_vector", source="/document/pages/*/text_vector"),
                        InputFieldMappingEntry(name="chunk", source="/document/pages/*"),
                        InputFieldMappingEntry(name="title", source="/document/title"),
                    ]
                )
            ],
            parameters=SearchIndexerIndexProjectionsParameters(
                projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS
            )
        )

        skillset = SearchIndexerSkillset(
            name=skillset_name,
            description="Skillset to chunk documents and generate embeddings",
            skills=[split_skill, embedding_skill],
            index_projection=index_projection,
        )

        async with SearchIndexerClient(endpoint=self._endpoint, credential=self._credential) as indexer_client:
            try:
                await indexer_client.get_skillset(skillset_name)
                logger.info(f"Skillset '{skillset_name}' already exists. Using existing skillset.")
                return ResourceStatus.EXISTING
            except HttpResponseError:
                try:
                    await indexer_client.create_or_update_skillset(skillset)
                    logger.info(f"Skillset '{skillset_name}' created successfully with Split + Embedding skills and {self._dimensions} dimensions.")
                    return ResourceStatus.CREATED
                except Exception as e:
                    logger.error(f"Failed to create skillset '{skillset_name}': {e}")
                    return ResourceStatus.FAILED

    async def create_indexer_maybe(
        self,
        indexer_name: str,
        datasource_name: str,
        target_index_name: str,
        skillset_name: str,
        file_extensions: str,
        parsing_mode: str,
    ) -> ResourceStatus:
        """
        Create a single indexer for specific file types.

        :param indexer_name: Name of the indexer
        :param datasource_name: Name of the datasource to use
        :param target_index_name: Target index name
        :param skillset_name: Skillset name to use
        :param file_extensions: Comma-separated file extensions to index (e.g., '.pdf,.docx')
        :param parsing_mode: Parsing mode (json, markdown, default)
        :return: ResourceStatus.CREATED, ResourceStatus.EXISTING, or ResourceStatus.FAILED
        """
        if not self._endpoint:
            logger.error("Search endpoint is required.")
            return ResourceStatus.FAILED

        async with SearchIndexerClient(endpoint=self._endpoint, credential=self._credential) as indexer_client:
            try:
                await indexer_client.get_indexer(indexer_name)
                logger.info(f"Indexer '{indexer_name}' already exists. Using existing indexer.")
                return ResourceStatus.EXISTING
            except HttpResponseError:
                pass

            indexer_params = IndexingParameters(
                batch_size=10,
                max_failed_items_per_batch=5,
                configuration=IndexingParametersConfiguration(
                    parsing_mode=parsing_mode,
                    indexed_file_name_extensions=file_extensions,
                    allow_skillset_to_read_file_data=parsing_mode == "default",
                    query_timeout=None
                )
            )

            indexer = SearchIndexer(
                name=indexer_name,
                data_source_name=datasource_name,
                target_index_name=target_index_name,
                skillset_name=skillset_name,
                field_mappings=[
                    FieldMapping(source_field_name="metadata_storage_name", target_field_name="title"),
                ],
                output_field_mappings=[
                    FieldMapping(source_field_name="/document/pages/*/text_vector", target_field_name="text_vector"),
                ],
                parameters=indexer_params,
            )

            try:
                await indexer_client.create_indexer(indexer)
                logger.info(f"Indexer '{indexer_name}' created for {file_extensions} files (parsing_mode: {parsing_mode}).")
                return ResourceStatus.CREATED
            except Exception as e:
                logger.error(f"Failed to create indexer '{indexer_name}': {e}")
                return ResourceStatus.FAILED


    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit, ensures resources are cleaned up."""
        await self.close()
        return False

    async def close(self):
        """Close the closeable resources, associated with SearchIndexManager."""
        if self._client:
            await self._client.close()
