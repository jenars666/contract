import os
import requests
import base64
from dotenv import load_dotenv
from utils.logger import get_logger

from typing import Optional, Dict

load_dotenv()
logger = get_logger("utils.git_handler")

def get_headers():
    token = os.getenv("GITHUB_TOKEN", "").strip()
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

def push_to_github(filename: str, content: str, commit_message: Optional[str] = None, target_branch: Optional[str] = None) -> Dict:
    """
    Pushes a file to a GitHub repository using the REST API.
    """
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repo = os.getenv("GITHUB_REPO", "").strip()  # format: username/repo
    if not target_branch:
        target_branch = os.getenv("GITHUB_BRANCH", "main").strip()

    if not token or not repo:
        logger.error("GITHUB_TOKEN or GITHUB_REPO not set in .env")
        return {"success": False, "error": "GitHub credentials not configured."}

    if commit_message is None:
        commit_message = f"SmartPatch: Automated security fix for {filename}"

    if token:
        logger.info(f"Using GitHub token starting with: {token[:8]}...")

    # GitHub API URL for file contents
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = get_headers()

    # 1. Check if the file already exists to get its SHA (needed for updates)
    sha = None
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            sha = response.json().get("sha")
            logger.info(f"File {filename} exists, SHA: {sha}")
        elif response.status_code == 403:
            perm_needed = response.headers.get("X-Accepted-GitHub-Permissions")
            logger.error(f"GitHub Permission Error (403). Permissions needed: {perm_needed}")
    except Exception as e:
        logger.warning(f"Error checking file existence: {e}")

    # 2. Prepare the payload
    # Content must be base64 encoded
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": commit_message,
        "content": content_b64,
        "branch": target_branch
    }
    if sha:
        payload["sha"] = sha

    # 3. Create or Update the file
    try:
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            logger.info(f"Successfully pushed {filename} to {repo} on branch {target_branch}")
            return {
                "success": True, 
                "url": response.json().get("content", {}).get("html_url"),
                "commit": response.json().get("commit", {}).get("sha")
            }
        else:
            error_detail = response.json().get("message", "Unknown error")
            status_code = response.status_code
            perm_needed = response.headers.get("X-Accepted-GitHub-Permissions")
            
            error_msg = f"GitHub API Error ({status_code}): {error_detail}"
            if perm_needed:
                error_msg += f" | Required permissions: {perm_needed}"
                
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    except Exception as e:
        logger.error(f"Failed to push to GitHub: {e}")
        return {"success": False, "error": str(e)}

def get_branch_sha(branch: Optional[str] = None) -> Optional[str]:
    """Gets the latest commit SHA of a branch."""
    repo = os.getenv("GITHUB_REPO", "").strip()
    if not branch:
        branch = os.getenv("GITHUB_BRANCH", "main").strip()
    
    url = f"https://api.github.com/repos/{repo}/git/refs/heads/{branch}"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            return response.json().get("object", {}).get("sha")
    except Exception as e:
        logger.error(f"Error getting branch SHA: {e}")
    return None

def create_branch(new_branch: str, base_branch: Optional[str] = None) -> bool:
    """Creates a new branch from a base branch."""
    repo = os.getenv("GITHUB_REPO", "").strip()
    base_sha = get_branch_sha(base_branch)
    if not base_sha:
        return False
    
    url = f"https://api.github.com/repos/{repo}/git/refs"
    payload = {
        "ref": f"refs/heads/{new_branch}",
        "sha": base_sha
    }
    
    try:
        response = requests.post(url, headers=get_headers(), json=payload)
        return response.status_code == 201
    except Exception as e:
        logger.error(f"Error creating branch: {e}")
        return False

def create_pull_request(title: str, body: str, head_branch: str, base_branch: Optional[str] = None) -> Dict:
    """Creates a Pull Request."""
    repo = os.getenv("GITHUB_REPO", "").strip()
    if not base_branch:
        base_branch = os.getenv("GITHUB_BRANCH", "main").strip()
        
    url = f"https://api.github.com/repos/{repo}/pulls"
    payload = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch
    }
    
    try:
        response = requests.post(url, headers=get_headers(), json=payload)
        if response.status_code == 201:
            return {"success": True, "url": response.json().get("html_url")}
        else:
            return {"success": False, "error": response.json().get("message", "PR creation failed")}
    except Exception as e:
        logger.error(f"Error creating PR: {e}")
        return {"success": False, "error": str(e)}
