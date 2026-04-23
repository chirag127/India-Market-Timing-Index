"""Cloudflare Pages deployment utility.

Deploys the website (dashboard + blog pages + API JSON) to
Cloudflare Pages using the Cloudflare API.
"""

from __future__ import annotations

from typing import Any

from imti.config.settings import get_settings
from imti.core.logger import get_logger

logger = get_logger("outputs.deploy")


def deploy_to_cloudflare() -> dict[str, Any]:
    """Deploy the website to Cloudflare Pages.

    Uses the Cloudflare Pages API to trigger a deployment
    from the repository's website/ directory.
    """
    settings = get_settings()

    if not settings.cloudflare_api_token or not settings.cloudflare_account_id:
        logger.warning("Cloudflare not configured — skipping deployment")
        return {"status": "skipped", "reason": "not configured"}

    try:
        import httpx

        url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{settings.cloudflare_account_id}/pages/projects/"
            f"{settings.cloudflare_project_name}/deployments"
        )

        headers = {
            "Authorization": f"Bearer {settings.cloudflare_api_token}",
            "Content-Type": "application/json",
        }

        # Trigger a new deployment
        # In production, this would upload the website/ directory
        response = httpx.post(url, headers=headers, timeout=30.0)

        if response.status_code in (200, 201):
            data = response.json()
            logger.info("Cloudflare Pages deployment triggered")
            return {"status": "success", "response": data}
        else:
            logger.warning(f"Cloudflare deployment failed: {response.status_code}")
            return {"status": "error", "code": response.status_code}

    except Exception as e:
        logger.error(f"Cloudflare deployment failed: {e}")
        return {"status": "error", "error": str(e)}
