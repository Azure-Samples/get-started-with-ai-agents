# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import os
import json
from dotenv import load_dotenv


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
            print(f"Config file not found: {config_path}")
            return None
            
        with open(config_path, 'r') as f:
            config = json.load(f)
            default_env = config.get('defaultEnvironment')
            
            if not default_env:
                print(f"No defaultEnvironment found in {config_path}")
                return None
                
            env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.azure', default_env, '.env'))
            
            if not os.path.exists(env_file):
                print(f"Environment file not found: {env_file}")
                return None
                
            # Successfully found the azd environment file
            return env_file
        
    except Exception as e:
        # On any error, return None to use default
        print(f"Warning: Error getting azd environment path: {e}")
        return None