"""NSDL source connector for FII/DII cash market flow data.

Provides: FII cash net buy/sell, DII cash net buy/sell, FII futures OI.
NSDL publishes daily FII/DII activity data which is the authoritative source
for institutional flow data in Indian markets.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Any

from imti.core.logger import get_logger
from imti.core.validation import safe_float
from imti.sources.base import BaseSource
from imti.sources.http import HttpClient

logger = get_logger("source.nsdl")

# NSDL FII/DII data endpoints
NSDL_FII_DII_URL = "https://www.fpi.nsdl.co.in/web/Reports/FIIDIIReport.aspx"
NSDL_DAILY_URL = "https://www.fpi.nsdl.co.in/web/Reports/FIIDIIReport.aspx?RptType=Daily"


class NSDLFlowsSource(BaseSource):
    """NSDL FII/DII flow source — authoritative institutional flow data.

    Provides daily FII and DII cash market net buy/sell figures in crores.
    This is the gold standard for institutional flow data in India.
    """

    name = "nsdl_flows"
    priority = 3  # Very high priority — official source for FII/DII
    timeout_seconds = 30.0
    max_retries = 3

    provides = [
        "fii_cash_net",
        "dii_cash_net",
        "fii_derivative_net",
        "dii_derivative_net",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._http = HttpClient(timeout=self.timeout_seconds)

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch FII/DII flow data from NSDL."""
        result: dict[str, Any] = {}

        try:
            from bs4 import BeautifulSoup

            response = self._http.get(NSDL_FII_DII_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            # Parse the FII/DII table
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    cell_texts = [c.get_text(strip=True) for c in cells]

                    # Look for FII/DII rows
                    if len(cell_texts) >= 3:
                        label = cell_texts[0].lower()

                        if "fii" in label and "cash" in label:
                            result["fii_cash_net"] = safe_float(
                                cell_texts[-1].replace(",", "").replace("(", "-").replace(")", ""),
                                default=0.0,
                            )
                        elif "dii" in label and "cash" in label:
                            result["dii_cash_net"] = safe_float(
                                cell_texts[-1].replace(",", "").replace("(", "-").replace(")", ""),
                                default=0.0,
                            )
                        elif "fii" in label and "deriv" in label:
                            result["fii_derivative_net"] = safe_float(
                                cell_texts[-1].replace(",", "").replace("(", "-").replace(")", ""),
                                default=0.0,
                            )
                        elif "dii" in label and "deriv" in label:
                            result["dii_derivative_net"] = safe_float(
                                cell_texts[-1].replace(",", "").replace("(", "-").replace(")", ""),
                                default=0.0,
                            )

        except Exception as e:
            logger.error(f"Failed to fetch NSDL FII/DII data: {e}")
            raise

        result["_metadata"] = {
            "source": self.name,
            "fetched_at": datetime.now().isoformat(),
        }
        return result
