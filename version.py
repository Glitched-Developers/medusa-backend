"""
Version management module for Medusa Backend

This module provides Git-based version tracking functionality.
It combines git tags with commit hashes to create meaningful version strings.
"""

import subprocess
import os
from typing import Optional


def get_git_version() -> str:
    """
    Get the current version based on Git information.
    
    Returns version in format:
    - If on tagged commit: "v1.0.0"  
    - If after tagged commit: "v1.0.0-dev+abc1234"
    - If no tags exist: "v0.0.0-dev+abc1234"
    
    Returns:
        str: Version string based on Git state
    """
    try:
        # Check if we're in a Git repository
        if not os.path.exists('.git') and not _find_git_repo():
            return "v1.0.0-unknown"
        
        # Try to get version with git describe
        try:
            # This will give us the most recent tag, or tag-commits-hash if we're ahead
            result = subprocess.check_output(
                ['git', 'describe', '--tags', '--dirty', '--always'], 
                stderr=subprocess.DEVNULL,
                cwd=_get_repo_root()
            ).decode('utf-8').strip()
            
            # If result doesn't start with 'v', it means no tags exist
            if not result.startswith('v'):
                # Get short commit hash and prepend v0.0.0
                return f"v0.0.0-dev+{result}"
            
            # If it contains a dash, we're ahead of the tag
            if '-' in result and not result.endswith('-dirty'):
                # Format: v1.0.0-3-gabc1234 -> v1.0.0-dev+abc1234
                parts = result.split('-')
                if len(parts) >= 3:
                    tag = parts[0]
                    commit_hash = parts[-1][1:] if parts[-1].startswith('g') else parts[-1]
                    return f"{tag}-dev+{commit_hash}"
            
            # Clean tag or dirty working directory
            return result
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: get commit hash only
            try:
                commit_hash = subprocess.check_output(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    stderr=subprocess.DEVNULL,
                    cwd=_get_repo_root()
                ).decode('utf-8').strip()
                return f"v0.0.0-dev+{commit_hash}"
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
                
    except Exception:
        pass
    
    return "v1.0.0-unknown"


def get_git_commit() -> Optional[str]:
    """
    Get the current Git commit hash.
    
    Returns:
        Optional[str]: Short commit hash or None if not available
    """
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL,
            cwd=_get_repo_root()
        ).decode('utf-8').strip()
    except Exception:
        return None


def get_git_branch() -> Optional[str]:
    """
    Get the current Git branch name.
    
    Returns:
        Optional[str]: Branch name or None if not available
    """
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL,
            cwd=_get_repo_root()
        ).decode('utf-8').strip()
    except Exception:
        return None


def _find_git_repo() -> bool:
    """
    Find if we're inside a Git repository by walking up the directory tree.
    
    Returns:
        bool: True if .git directory is found in any parent directory
    """
    current_dir = os.getcwd()
    while current_dir != os.path.dirname(current_dir):  # Not at root
        if os.path.exists(os.path.join(current_dir, '.git')):
            return True
        current_dir = os.path.dirname(current_dir)
    return False


def _get_repo_root() -> str:
    """
    Get the root directory of the Git repository.
    
    Returns:
        str: Repository root directory path
    """
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
    except Exception:
        return os.getcwd()


# Cache version to avoid multiple git calls
_cached_version: Optional[str] = None


def get_version() -> str:
    """
    Get the cached version or fetch it from Git.
    
    Returns:
        str: Application version string
    """
    global _cached_version
    if _cached_version is None:
        _cached_version = get_git_version()
    return _cached_version


if __name__ == "__main__":
    """Test the version functionality."""
    print(f"Version: {get_version()}")
    print(f"Commit: {get_git_commit()}")
    print(f"Branch: {get_git_branch()}")