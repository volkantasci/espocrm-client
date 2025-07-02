"""
EspoCRM Python Client CLI Tool

Command line interface for EspoCRM operations.
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

from . import EspoCRMClient, __version__
from .auth import APIKeyAuth, BasicAuth, HMACAuth
from .config import create_config_from_env
from .exceptions import EspoCRMError
from .logging import get_logger

logger = get_logger(__name__)


def create_client_from_args(args: argparse.Namespace) -> EspoCRMClient:
    """Create EspoCRM client from command line arguments."""
    # Try to get config from environment first
    try:
        config = create_config_from_env()
        if config.base_url and args.url is None:
            args.url = config.base_url
    except Exception:
        pass
    
    if not args.url:
        raise ValueError("EspoCRM URL is required. Use --url or set ESPOCRM_URL environment variable.")
    
    # Create authentication
    if args.api_key:
        auth = APIKeyAuth(args.api_key)
    elif args.username and args.password:
        auth = BasicAuth(args.username, args.password)
    elif args.hmac_key and args.hmac_secret:
        auth = HMACAuth(args.hmac_key, args.hmac_secret)
    else:
        raise ValueError("Authentication is required. Use --api-key, --username/--password, or --hmac-key/--hmac-secret")
    
    return EspoCRMClient(args.url, auth)


def cmd_list_entities(args: argparse.Namespace) -> None:
    """List entities command."""
    client = create_client_from_args(args)
    
    try:
        records = client.crud.list(
            args.entity_type,
            limit=args.limit,
            offset=args.offset
        )
        
        if args.format == 'json':
            print(json.dumps(records.model_dump(), indent=2, ensure_ascii=False))
        else:
            print(f"Found {records.total} {args.entity_type} records:")
            for record in records.records:
                print(f"  ID: {record.id}")
                if hasattr(record, 'name') and record.name:
                    print(f"    Name: {record.name}")
                print()
                
    except EspoCRMError as e:
        logger.error("Failed to list entities", error=str(e))
        sys.exit(1)


def cmd_get_entity(args: argparse.Namespace) -> None:
    """Get entity command."""
    client = create_client_from_args(args)
    
    try:
        record = client.crud.get(args.entity_type, args.entity_id)
        
        if args.format == 'json':
            print(json.dumps(record.model_dump(), indent=2, ensure_ascii=False))
        else:
            print(f"{args.entity_type} (ID: {record.id}):")
            for key, value in record.model_dump().items():
                if value is not None:
                    print(f"  {key}: {value}")
                    
    except EspoCRMError as e:
        logger.error("Failed to get entity", error=str(e))
        sys.exit(1)


def cmd_create_entity(args: argparse.Namespace) -> None:
    """Create entity command."""
    client = create_client_from_args(args)
    
    try:
        # Parse data from JSON string or file
        if args.data.startswith('@'):
            # Read from file
            filename = args.data[1:]
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Parse as JSON string
            data = json.loads(args.data)
        
        record = client.crud.create(args.entity_type, data)
        
        if args.format == 'json':
            print(json.dumps(record.model_dump(), indent=2, ensure_ascii=False))
        else:
            print(f"Created {args.entity_type} with ID: {record.id}")
            
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error("Failed to parse data", error=str(e))
        sys.exit(1)
    except EspoCRMError as e:
        logger.error("Failed to create entity", error=str(e))
        sys.exit(1)


def cmd_update_entity(args: argparse.Namespace) -> None:
    """Update entity command."""
    client = create_client_from_args(args)
    
    try:
        # Parse data from JSON string or file
        if args.data.startswith('@'):
            # Read from file
            filename = args.data[1:]
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Parse as JSON string
            data = json.loads(args.data)
        
        success = client.crud.update(args.entity_type, args.entity_id, data)
        
        if args.format == 'json':
            print(json.dumps({"success": success}, indent=2))
        else:
            if success:
                print(f"Successfully updated {args.entity_type} (ID: {args.entity_id})")
            else:
                print(f"Failed to update {args.entity_type} (ID: {args.entity_id})")
                sys.exit(1)
                
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error("Failed to parse data", error=str(e))
        sys.exit(1)
    except EspoCRMError as e:
        logger.error("Failed to update entity", error=str(e))
        sys.exit(1)


def cmd_delete_entity(args: argparse.Namespace) -> None:
    """Delete entity command."""
    client = create_client_from_args(args)
    
    try:
        success = client.crud.delete(args.entity_type, args.entity_id)
        
        if args.format == 'json':
            print(json.dumps({"success": success}, indent=2))
        else:
            if success:
                print(f"Successfully deleted {args.entity_type} (ID: {args.entity_id})")
            else:
                print(f"Failed to delete {args.entity_type} (ID: {args.entity_id})")
                sys.exit(1)
                
    except EspoCRMError as e:
        logger.error("Failed to delete entity", error=str(e))
        sys.exit(1)


def cmd_metadata(args: argparse.Namespace) -> None:
    """Get metadata command."""
    client = create_client_from_args(args)
    
    try:
        if args.entity_type:
            metadata = client.metadata.get_entity_metadata(args.entity_type)
        else:
            metadata = client.metadata.get_app_metadata()
        
        if args.format == 'json':
            print(json.dumps(metadata.model_dump(), indent=2, ensure_ascii=False))
        else:
            print("Metadata:")
            print(json.dumps(metadata.model_dump(), indent=2, ensure_ascii=False))
            
    except EspoCRMError as e:
        logger.error("Failed to get metadata", error=str(e))
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog='espocrm-cli',
        description='EspoCRM Python Client CLI Tool'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'espocrm-python-client {__version__}'
    )
    
    # Global options
    parser.add_argument(
        '--url',
        help='EspoCRM base URL (can also use ESPOCRM_URL env var)'
    )
    
    parser.add_argument(
        '--api-key',
        help='API key for authentication (can also use ESPOCRM_API_KEY env var)'
    )
    
    parser.add_argument(
        '--username',
        help='Username for basic authentication'
    )
    
    parser.add_argument(
        '--password',
        help='Password for basic authentication'
    )
    
    parser.add_argument(
        '--hmac-key',
        help='HMAC key for HMAC authentication'
    )
    
    parser.add_argument(
        '--hmac-secret',
        help='HMAC secret for HMAC authentication'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'table'],
        default='table',
        help='Output format (default: table)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List entities')
    list_parser.add_argument('entity_type', help='Entity type (e.g., Lead, Account)')
    list_parser.add_argument('--limit', type=int, default=20, help='Number of records to fetch')
    list_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    list_parser.set_defaults(func=cmd_list_entities)
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get entity by ID')
    get_parser.add_argument('entity_type', help='Entity type (e.g., Lead, Account)')
    get_parser.add_argument('entity_id', help='Entity ID')
    get_parser.set_defaults(func=cmd_get_entity)
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new entity')
    create_parser.add_argument('entity_type', help='Entity type (e.g., Lead, Account)')
    create_parser.add_argument('data', help='JSON data or @filename')
    create_parser.set_defaults(func=cmd_create_entity)
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update entity')
    update_parser.add_argument('entity_type', help='Entity type (e.g., Lead, Account)')
    update_parser.add_argument('entity_id', help='Entity ID')
    update_parser.add_argument('data', help='JSON data or @filename')
    update_parser.set_defaults(func=cmd_update_entity)
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete entity')
    delete_parser.add_argument('entity_type', help='Entity type (e.g., Lead, Account)')
    delete_parser.add_argument('entity_id', help='Entity ID')
    delete_parser.set_defaults(func=cmd_delete_entity)
    
    # Metadata command
    metadata_parser = subparsers.add_parser('metadata', help='Get metadata')
    metadata_parser.add_argument('--entity-type', help='Specific entity type metadata')
    metadata_parser.set_defaults(func=cmd_metadata)
    
    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()