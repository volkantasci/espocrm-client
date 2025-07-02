#!/usr/bin/env python3
"""
Version Management Script for EspoCRM Python Client

This script helps manage version bumping, changelog updates, and release preparation.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def get_current_version() -> str:
    """Get current version from __init__.py"""
    init_file = PROJECT_ROOT / "espocrm" / "__init__.py"
    
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not version_match:
        raise ValueError("Could not find version in __init__.py")
    
    return version_match.group(1)


def parse_version(version: str) -> Tuple[int, int, int, Optional[str]]:
    """Parse version string into components."""
    # Match semantic version pattern: major.minor.patch[-prerelease]
    pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$'
    match = re.match(pattern, version)
    
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    
    major, minor, patch, prerelease = match.groups()
    return int(major), int(minor), int(patch), prerelease


def format_version(major: int, minor: int, patch: int, prerelease: Optional[str] = None) -> str:
    """Format version components into version string."""
    version = f"{major}.{minor}.{patch}"
    if prerelease:
        version += f"-{prerelease}"
    return version


def bump_version(current_version: str, bump_type: str) -> str:
    """Bump version based on type."""
    major, minor, patch, prerelease = parse_version(current_version)
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
        prerelease = None
    elif bump_type == "minor":
        minor += 1
        patch = 0
        prerelease = None
    elif bump_type == "patch":
        patch += 1
        prerelease = None
    elif bump_type == "alpha":
        if prerelease and prerelease.startswith("alpha"):
            # Increment alpha version
            alpha_match = re.match(r'alpha\.?(\d+)?', prerelease)
            if alpha_match and alpha_match.group(1):
                alpha_num = int(alpha_match.group(1)) + 1
            else:
                alpha_num = 2
            prerelease = f"alpha.{alpha_num}"
        else:
            # First alpha release
            patch += 1
            prerelease = "alpha.1"
    elif bump_type == "beta":
        if prerelease and prerelease.startswith("beta"):
            # Increment beta version
            beta_match = re.match(r'beta\.?(\d+)?', prerelease)
            if beta_match and beta_match.group(1):
                beta_num = int(beta_match.group(1)) + 1
            else:
                beta_num = 2
            prerelease = f"beta.{beta_num}"
        else:
            # First beta release
            if not prerelease:
                patch += 1
            prerelease = "beta.1"
    elif bump_type == "rc":
        if prerelease and prerelease.startswith("rc"):
            # Increment RC version
            rc_match = re.match(r'rc\.?(\d+)?', prerelease)
            if rc_match and rc_match.group(1):
                rc_num = int(rc_match.group(1)) + 1
            else:
                rc_num = 2
            prerelease = f"rc.{rc_num}"
        else:
            # First RC release
            if not prerelease:
                patch += 1
            prerelease = "rc.1"
    elif bump_type == "release":
        # Remove prerelease suffix
        prerelease = None
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return format_version(major, minor, patch, prerelease)


def update_version_in_files(new_version: str) -> None:
    """Update version in all relevant files."""
    files_to_update = [
        (PROJECT_ROOT / "espocrm" / "__init__.py", r'__version__\s*=\s*["\'][^"\']+["\']', f'__version__ = "{new_version}"'),
        (PROJECT_ROOT / "pyproject.toml", r'version\s*=\s*["\'][^"\']+["\']', f'version = "{new_version}"'),
    ]
    
    for file_path, pattern, replacement in files_to_update:
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Updated version in {file_path.name}")
        else:
            print(f"⚠️  No version found to update in {file_path.name}")


def update_changelog(new_version: str, release_notes: Optional[str] = None) -> None:
    """Update CHANGELOG.md with new version."""
    changelog_path = PROJECT_ROOT / "CHANGELOG.md"
    
    if not changelog_path.exists():
        print("⚠️  CHANGELOG.md not found")
        return
    
    with open(changelog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the [Unreleased] section
    unreleased_pattern = r'## \[Unreleased\]'
    
    if not re.search(unreleased_pattern, content):
        print("⚠️  [Unreleased] section not found in CHANGELOG.md")
        return
    
    # Create new version section
    today = datetime.now().strftime("%Y-%m-%d")
    new_section = f"""## [Unreleased]

## [{new_version}] - {today}"""
    
    if release_notes:
        new_section += f"\n\n{release_notes}"
    
    # Replace [Unreleased] with new version section
    new_content = re.sub(unreleased_pattern, new_section, content)
    
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Updated CHANGELOG.md with version {new_version}")


def validate_version(version: str) -> bool:
    """Validate version format."""
    try:
        parse_version(version)
        return True
    except ValueError:
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Manage versions for EspoCRM Python Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/version_manager.py current
  python scripts/version_manager.py bump patch
  python scripts/version_manager.py bump minor --update-changelog
  python scripts/version_manager.py set 1.2.3 --update-changelog --notes "Bug fixes and improvements"
  python scripts/version_manager.py validate 1.2.3-alpha.1
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Current version command
    subparsers.add_parser('current', help='Show current version')
    
    # Bump version command
    bump_parser = subparsers.add_parser('bump', help='Bump version')
    bump_parser.add_argument(
        'type',
        choices=['major', 'minor', 'patch', 'alpha', 'beta', 'rc', 'release'],
        help='Type of version bump'
    )
    bump_parser.add_argument('--update-changelog', action='store_true', help='Update CHANGELOG.md')
    bump_parser.add_argument('--notes', help='Release notes for changelog')
    bump_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    # Set version command
    set_parser = subparsers.add_parser('set', help='Set specific version')
    set_parser.add_argument('version', help='Version to set (e.g., 1.2.3)')
    set_parser.add_argument('--update-changelog', action='store_true', help='Update CHANGELOG.md')
    set_parser.add_argument('--notes', help='Release notes for changelog')
    set_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    # Validate version command
    validate_parser = subparsers.add_parser('validate', help='Validate version format')
    validate_parser.add_argument('version', help='Version to validate')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'current':
            current = get_current_version()
            print(f"Current version: {current}")
        
        elif args.command == 'bump':
            current = get_current_version()
            new_version = bump_version(current, args.type)
            
            print(f"Current version: {current}")
            print(f"New version: {new_version}")
            
            if args.dry_run:
                print("🔍 Dry run - no changes made")
                if args.update_changelog:
                    print("Would update CHANGELOG.md")
                return
            
            # Confirm the change
            response = input(f"Update version from {current} to {new_version}? (y/N): ")
            if response.lower() != 'y':
                print("❌ Version update cancelled")
                return
            
            update_version_in_files(new_version)
            
            if args.update_changelog:
                update_changelog(new_version, args.notes)
            
            print(f"🎉 Version updated to {new_version}")
        
        elif args.command == 'set':
            if not validate_version(args.version):
                print(f"❌ Invalid version format: {args.version}")
                sys.exit(1)
            
            current = get_current_version()
            
            print(f"Current version: {current}")
            print(f"New version: {args.version}")
            
            if args.dry_run:
                print("🔍 Dry run - no changes made")
                if args.update_changelog:
                    print("Would update CHANGELOG.md")
                return
            
            # Confirm the change
            response = input(f"Update version from {current} to {args.version}? (y/N): ")
            if response.lower() != 'y':
                print("❌ Version update cancelled")
                return
            
            update_version_in_files(args.version)
            
            if args.update_changelog:
                update_changelog(args.version, args.notes)
            
            print(f"🎉 Version updated to {args.version}")
        
        elif args.command == 'validate':
            if validate_version(args.version):
                print(f"✅ Valid version format: {args.version}")
            else:
                print(f"❌ Invalid version format: {args.version}")
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()