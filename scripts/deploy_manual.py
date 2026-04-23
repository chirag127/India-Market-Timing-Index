"""Manual deployment script for Cloudflare Pages.

Usage:
    python scripts/deploy_manual.py

This script:
1. Builds the Astro website
2. Deploys to Cloudflare Pages using Wrangler CLI
3. Sets up DNS records if Cloudflare API token is available

Requirements:
    - CLOUDFLARE_API_TOKEN env var
    - CLOUDFLARE_ACCOUNT_ID env var
    - CLOUDFLARE_PROJECT_NAME env var
    - wrangler CLI installed (npm install -g wrangler)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(cmd: str, cwd: Path | None = None) -> None:
    """Run a shell command and exit on failure."""
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, check=False)
    if result.returncode != 0:
        print(f"FAILED: {cmd}")
        sys.exit(1)


def main() -> None:
    """Main deployment flow."""
    token = os.getenv("CLOUDFLARE_API_TOKEN", "")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    project_name = os.getenv("CLOUDFLARE_PROJECT_NAME", "imti")

    if not token or not account_id:
        print("ERROR: CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID required.")
        sys.exit(1)

    root = Path(__file__).parent.parent
    website_dir = root / "website"

    # Build website
    print("=" * 60)
    print("Building Astro website...")
    print("=" * 60)
    run("npm install", cwd=website_dir)
    run("npm run build", cwd=website_dir)

    # Deploy
    print("=" * 60)
    print("Deploying to Cloudflare Pages...")
    print("=" * 60)
    deploy_cmd = (
        f"npx wrangler pages deploy dist "
        f"--project-name={project_name} "
        f"--branch=main"
    )
    run(deploy_cmd, cwd=website_dir)

    print("=" * 60)
    print("DEPLOYMENT COMPLETE")
    print(f"Site: https://{project_name}.pages.dev")
    print("=" * 60)


if __name__ == "__main__":
    main()
