"""AMFI (Association of Mutual Funds of India) source connector.

Provides: Monthly SIP flow data, total AUM, equity fund flows.
AMFI publishes monthly mutual fund statistics which are important
for understanding retail investor sentiment and flow dynamics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from imti.core.logger import get_logger
from imti.core.validation import safe_float
from imti.sources.base import BaseSource
from imti.sources.http import HttpClient

logger = get_logger("source.amfi")

AMFI_MONTHLY_URL = "https://www.amfiindia.com/research-data/aum-data"
AMFI_SIP_URL = "https://www.amfiindia.com/research-data/sip-statistics"


class AMFISIPSource(BaseSource):
    """AMFI source — provides SIP flow and mutual fund statistics.

    SIP (Systematic Investment Plan) flows are a key indicator of
    retail investor conviction. Rising SIP flows indicate strong
    retail participation (often contrarian sell signal in our system).
    """

    name = "amfi_sip"
    priority = 25
    timeout_seconds = 25.0
    max_retries = 2

    provides = [
        "sip_monthly_flow",
        "total_aum",
        "equity_fund_net_flow",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._http = HttpClient(timeout=self.timeout_seconds)

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch AMFI SIP and mutual fund flow data."""
        result: dict[str, Any] = {}

        try:
            from bs4 import BeautifulSoup

            response = self._http.get(AMFI_SIP_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            # Parse SIP statistics table
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    cell_texts = [c.get_text(strip=True) for c in cells]

                    if len(cell_texts) >= 2:
                        label = cell_texts[0].lower()

                        if "sip" in label and ("contribution" in label or "flow" in label):
                            result["sip_monthly_flow"] = safe_float(
                                cell_texts[-1].replace("₹", "").replace(",", "").replace("Cr", "").strip(),
                                default=0.0,
                            )
                        elif "aum" in label and "total" in label:
                            result["total_aum"] = safe_float(
                                cell_texts[-1].replace("₹", "").replace(",", "").replace("Cr", "").strip(),
                                default=0.0,
                            )
                        elif "equity" in label and "net" in label:
                            result["equity_fund_net_flow"] = safe_float(
                                cell_texts[-1].replace("₹", "").replace(",", "").replace("Cr", "").strip(),
                                default=0.0,
                            )

        except Exception as e:
            logger.error(f"Failed to fetch AMFI data: {e}")
            raise

        result["_metadata"] = {
            "source": self.name,
            "fetched_at": datetime.now().isoformat(),
        }
        return result
