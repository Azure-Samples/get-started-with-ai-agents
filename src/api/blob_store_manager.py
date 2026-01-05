from typing import Optional
from enum import Enum
import logging
import os

from azure.core.credentials_async import AsyncTokenCredential
from azure.storage.blob.aio import BlobServiceClient
from azure.core.exceptions import HttpResponseError

logger = logging.getLogger(__name__)


class ResourceStatus(Enum):
    """Status of a resource operation."""
    CREATED = "created"
    EXISTING = "existing"
    FAILED = "failed"


class BlobStoreManager:
    """Manager for Azure Blob Storage operations."""

    def __init__(
        self,
        account_url: str,
        credential: AsyncTokenCredential,
    ) -> None:
        """
        Constructor.
        
        :param account_url: The blob storage account URL
        :param credential: The credential to use for authentication
        """
        self._account_url = account_url
        self._credential = credential

    async def create_blob_container_maybe(
        self,
        container_name: str,
    ) -> ResourceStatus:
        """
        Create a blob container if it doesn't exist.

        :param container_name: Name of the container to create
        :return: ResourceStatus.CREATED, ResourceStatus.EXISTING, or ResourceStatus.FAILED
        """
        try:
            async with BlobServiceClient(account_url=self._account_url, credential=self._credential) as blob_service_client:
                container_client = blob_service_client.get_container_client(container_name)
                
                try:
                    await container_client.create_container()
                    logger.info(f"Blob container '{container_name}' created successfully.")
                    return ResourceStatus.CREATED
                except HttpResponseError as e:
                    if e.status_code == 409:  # Already exists
                        logger.info(f"Blob container '{container_name}' already exists. Using existing container.")
                        return ResourceStatus.EXISTING
                    else:
                        logger.error(f"Failed to create blob container '{container_name}': {e}")
                        return ResourceStatus.FAILED
        except Exception as e:
            logger.error(f"Unexpected error creating blob container '{container_name}': {e}")
            return ResourceStatus.FAILED

    async def upload_to_blob_store_maybe(
        self,
        container_name: str,
        files_directory: str,
    ) -> ResourceStatus:
        """
        Upload files from local directory to blob container if container is empty.

        :param container_name: Name of the blob container
        :param files_directory: Local directory containing files to upload
        :return: ResourceStatus.CREATED (files uploaded), ResourceStatus.EXISTING (already has files), or ResourceStatus.FAILED
        """
        try:
            async with BlobServiceClient(account_url=self._account_url, credential=self._credential) as blob_service_client:
                container_client = blob_service_client.get_container_client(container_name)
                
                # Check if container has any blobs
                blobs = []
                async for blob in container_client.list_blobs():
                    blobs.append(blob.name)
                
                if blobs:
                    logger.info(f"Blob container '{container_name}' already contains {len(blobs)} file(s). Skipping upload.")
                    return ResourceStatus.EXISTING
                
                # Upload files
                upload_count = 0
                if os.path.exists(files_directory):
                    for filename in os.listdir(files_directory):
                        filepath = os.path.join(files_directory, filename)
                        if os.path.isfile(filepath):
                            try:
                                blob_client = container_client.get_blob_client(filename)
                                with open(filepath, 'rb') as data:
                                    await blob_client.upload_blob(data, overwrite=True)
                                    upload_count += 1
                                    logger.info(f"Uploaded '{filename}' to blob container '{container_name}'")
                            except Exception as e:
                                logger.error(f"Failed to upload '{filename}': {e}")
                                return ResourceStatus.FAILED
                    
                    if upload_count > 0:
                        logger.info(f"Successfully uploaded {upload_count} file(s) to blob container '{container_name}'.")
                        return ResourceStatus.CREATED
                    else:
                        logger.warning(f"No files found in directory '{files_directory}' to upload.")
                        return ResourceStatus.EXISTING
                else:
                    logger.error(f"Files directory does not exist: {files_directory}")
                    return ResourceStatus.FAILED
        except Exception as e:
            logger.error(f"Failed to upload files to blob container '{container_name}': {e}")
            return ResourceStatus.FAILED
