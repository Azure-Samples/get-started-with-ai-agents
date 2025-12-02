# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import os, json, base64
from enum import IntEnum
from typing import Dict
from dataclasses import dataclass, field
from urllib.parse import quote


def get_env_file_path():
    """
    Get the path to the environment file to load.
    
    For local development (RUNNING_IN_PRODUCTION not set):
      - Reads .azure/config.json to get defaultEnvironment
      - Returns path to .azure/{defaultEnvironment}/.env
    
    For production (RUNNING_IN_PRODUCTION set):
      - Returns None (will use default .env location)
    
    Returns:
        str: Absolute path to the environment file, or None to use default location.
    """
    # In production, use default location
    if os.getenv("RUNNING_IN_PRODUCTION"):
        return None
    
    # For local development, try to get path from .azure/{environment}/.env
    try:
        # Read the default environment from .azure/config.json
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.azure', 'config.json'))
        
        if not os.path.exists(config_path):
            return None
            
        with open(config_path, 'r') as f:
            config = json.load(f)
            default_env = config.get('defaultEnvironment')
            
            if not default_env:
                return None
                
            env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.azure', default_env, '.env'))
            
            if not os.path.exists(env_file):
                return None
                
            # Successfully found the azd environment file
            return env_file
        
    except Exception as e:
        # On any error, return None to use default
        return None
    

# Constants
DEFAULT_NS_TYPE = "Microsoft.CognitiveServices"
DELIM = ","


class _ProjectResourceIdKind(IntEnum):
    """Enum for resource ID kinds"""
    Invalid = 0
    Subscription = 1
    ResourceGroup = 2
    Provider = 3
    Resource = 4


class _ResourceIdOrders(IntEnum):
    """Enum for resource ID ordering"""
    Subscription = 1
    ResourceGroup = 3
    Provider = 5
    ResourceSegments = 7


class ResourceSegmentMap(Dict[str, str]):
    """Map for resource segments"""
    pass


@dataclass
class _ProjectResourceId:
    """Project Resource ID interface"""
    subscription: str = ""
    resource_group: str = ""
    provider: str = ""
    kind: _ProjectResourceIdKind = _ProjectResourceIdKind.Invalid
    is_valid: bool = False
    resource_segments: ResourceSegmentMap = field(default_factory=ResourceSegmentMap)


def get_default_resource_id() -> _ProjectResourceId:
    """Returns a default resource ID object"""
    return _ProjectResourceId()


def compare(str1: str, str2: str, ignore_case: bool = False) -> int:
    """
    Compare two strings
    Returns 0 if equal, -1 if str1 < str2, 1 if str1 > str2
    """
    if ignore_case:
        str1 = str1.lower()
        str2 = str2.lower()
    
    if str1 == str2:
        return 0
    elif str1 < str2:
        return -1
    else:
        return 1


def _parse_project_resource_id(resource_id: str) -> _ProjectResourceId:
    """
    Parses the specified project resource ID and returns an object which has subscription/resourceGroup/provider fields
    populated. If there are any resource segments exist in the id, resourceSegments field is also populated.

    Args:
        resource_id: Resource ID of the resource to parse.
    
    Returns:
        ResourceId object with parsed components
    """
    id_parts = (resource_id or '').split('/')
    first_part = id_parts[0] if id_parts else ''
    

    parsed_resource_id = get_default_resource_id()
    part_count = len(id_parts)
    
    for index in range(1, part_count, 2):
        token_name = id_parts[index]
        token_value = id_parts[index + 1] if index + 1 < len(id_parts) else ''
        
        if (
            compare(token_name, 'subscriptions', ignore_case=True) == 0 and
            index == _ResourceIdOrders.Subscription
        ):
            parsed_resource_id.subscription = token_value
            parsed_resource_id.kind = _ProjectResourceIdKind.Subscription
        elif (
            compare(token_name, 'resourceGroups', ignore_case=True) == 0 and
            index == _ResourceIdOrders.ResourceGroup
        ):
            parsed_resource_id.resource_group = token_value
            parsed_resource_id.kind = _ProjectResourceIdKind.ResourceGroup
        elif (
            compare(token_name, 'providers', ignore_case=True) == 0 and
            index == _ResourceIdOrders.Provider
        ):
            parsed_resource_id.provider = token_value
            parsed_resource_id.kind = _ProjectResourceIdKind.Provider
        elif (
            compare(token_name, 'providers', ignore_case=True) != 0 and
            index >= _ResourceIdOrders.Provider
        ):
            parsed_resource_id.kind = _ProjectResourceIdKind.Resource
            parsed_resource_id.resource_segments[token_name] = token_value

    # All kinds require a subscription
    if not parsed_resource_id.subscription:
        parsed_resource_id.kind = _ProjectResourceIdKind.Invalid

    # Enforce kinds that require a valid resource group
    if (
        parsed_resource_id.kind in [_ProjectResourceIdKind.ResourceGroup, _ProjectResourceIdKind.Provider, _ProjectResourceIdKind.Resource] and
        not parsed_resource_id.resource_group
    ):
        parsed_resource_id.kind = _ProjectResourceIdKind.Invalid

    # Enforce kinds that require a provider
    if (
        parsed_resource_id.kind in [_ProjectResourceIdKind.Provider, _ProjectResourceIdKind.Resource] and
        not parsed_resource_id.provider
    ):
        parsed_resource_id.kind = _ProjectResourceIdKind.Invalid

    parsed_resource_id.is_valid = parsed_resource_id.kind != _ProjectResourceIdKind.Invalid
    
    return parsed_resource_id


def _compress_guid(guid: str) -> str:
    """
    Compress a GUID by converting to base64url encoding.
    
    Args:
        guid: GUID string to compress (e.g., "12345678-1234-1234-1234-123456789abc")
    
    Returns:
        Base64url-encoded GUID string without padding
    
    Example:
        Input: "12345678-1234-5678-1234-567812345678"
        Output: "{base64url-encoded-string}"
    """
    # Remove hyphens from GUID
    hex_str = guid.replace('-', '')
    
    # Convert hex string to bytes
    binary_str = bytes.fromhex(hex_str)
    
    # Base64 encode
    base64_str = base64.b64encode(binary_str).decode('utf-8')
    
    # Convert to base64url format (replace +/= with -_)
    return base64_str.replace('+', '-').replace('/', '_').rstrip('=')


def encode_project_resource_id(project_resource_id: str) -> str:
    """
    Encode a project resource ID into a compressed format.
    
    This function parses a project resource ID and encodes it into a compact string format:
    - Compresses the subscription GUID to base64url encoding
    - URL-encodes the resource group name
    - Optionally includes the provider (if not the default)
    - URL-encodes the account name
    - Optionally includes the project name if present
    
    Args:
        project_resource_id: Project resource ID to encode
    
    Returns:
        Encoded resource ID string with segments separated by commas
    
    Raises:
        ValueError: If the project resource ID format is invalid or not an account resource
    
    Example:
        Input: /subscriptions/{subscription-id}/resourceGroups/{resource-group-name}/
               providers/Microsoft.CognitiveServices/accounts/{account-name}/projects/{project-name}
        Output: {compressed-subscription-id},{resource-group-name},,{account-name},{project-name}
    """
    parsed = _parse_project_resource_id(project_resource_id)
    
    if (
        not parsed.is_valid or
        parsed.kind != _ProjectResourceIdKind.Resource or
        'accounts' not in parsed.resource_segments
    ):
        raise ValueError('Invalid project resource ID format.')
    
    encoded_resource_id_segments = [
        _compress_guid(parsed.subscription),
        quote(parsed.resource_group),
        '' if parsed.provider == DEFAULT_NS_TYPE else quote(parsed.provider),
        quote(parsed.resource_segments.get('accounts', '')),
    ]
    
    project_name = parsed.resource_segments.get('projects', '')
    if project_name:
        encoded_resource_id_segments.append(quote(project_name))
    
    return DELIM.join(encoded_resource_id_segments)
