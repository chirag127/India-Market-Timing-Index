"""Automated script to push .env values to GitHub Secrets.

Usage:
    python scripts/push_secrets.py

Requirements:
    - GITHUB_TOKEN env var (PAT with repo scope)
    - .env file in project root

This script reads your .env file and uploads each non-empty value
as a GitHub Secret for the configured repository. It uses the
GitHub Actions API with libsodium encryption.
"""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

import requests


def load_env_file(path: Path) -> dict[str, str]:
    """Parse .env file into key-value pairs."""
    env_vars: dict[str, str] = {}
    if not path.exists():
        print(f"ERROR: .env file not found at {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value and not value.startswith("your_"):
                    env_vars[key] = value

    return env_vars


def get_public_key(token: str, owner: str, repo: str) -> dict[str, str]:
    """Fetch the repository's public key for secret encryption."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def encrypt_secret(public_key: str, secret_value: str) -> str:
    """Encrypt a secret using the repo's public key (libsodium)."""
    import nacl.encoding
    import nacl.public

    public_key_bytes = base64.b64decode(public_key)
    seal_box = nacl.public.SealedBox(nacl.public.PublicKey(public_key_bytes))
    encrypted = seal_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def set_secret(
    token: str,
    owner: str,
    repo: str,
    secret_name: str,
    encrypted_value: str,
    key_id: str,
) -> bool:
    """Upload an encrypted secret to GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id,
    }
    resp = requests.put(url, headers=headers, json=data, timeout=30)
    if resp.status_code in (201, 204):
        return True
    print(f"  FAILED: {resp.status_code} — {resp.text}")
    return False


def main() -> None:
    """Main entry point."""
    token = os.getenv("GITHUB_TOKEN", "")
    owner = os.getenv("GITHUB_REPO_OWNER", "chirag127")
    repo = os.getenv("GITHUB_REPO_NAME", "India-Market-Timing-Index")

    if not token:
        print("ERROR: GITHUB_TOKEN environment variable is required.")
        print("Create a Personal Access Token at: https://github.com/settings/tokens")
        print("Required scope: repo")
        sys.exit(1)

    env_path = Path(".env")
    env_vars = load_env_file(env_path)

    if not env_vars:
        print("No secrets to push (all values are empty or placeholders).")
        sys.exit(0)

    print(f"Pushing {len(env_vars)} secrets to {owner}/{repo}...")

    # Check if PyNaCl is available
    try:
        import nacl.public
    except ImportError:
        print("Installing PyNaCl...")
        os.system(f"{sys.executable} -m pip install pynacl -q")
        import nacl.public

    key_data = get_public_key(token, owner, repo)
    public_key = key_data["key"]
    key_id = key_data["key_id"]

    success = 0
    failed = 0

    for name, value in env_vars.items():
        # GitHub secret names can only contain A-Z, 0-9, _
        safe_name = name.replace("-", "_").upper()
        print(f"  Setting {safe_name}...", end=" ")

        try:
            encrypted = encrypt_secret(public_key, value)
            if set_secret(token, owner, repo, safe_name, encrypted, key_id):
                print("OK")
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1

    print(f"\nDone: {success} succeeded, {failed} failed.")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
