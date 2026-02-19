"""
Tiered token governance with daily spend caps.

Tracks per-user daily spend and provides per-run budget ceilings.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Dict, Optional
import os


class TokenTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class TierBudget:
    daily_cap_usd: float | None  # None == unlimited


DEFAULT_TIERS: Dict[TokenTier, TierBudget] = {
    TokenTier.FREE: TierBudget(daily_cap_usd=float(os.getenv("FREE_DAILY_CAP_USD", "1.0"))),
    TokenTier.PRO: TierBudget(daily_cap_usd=float(os.getenv("PRO_DAILY_CAP_USD", "25.0"))),
    TokenTier.ENTERPRISE: TierBudget(daily_cap_usd=None),
}


class TokenGovernance:
    """Persists daily spend and enforces per-tier caps."""

    def __init__(self, path: Path | None = None):
        self.path = path or Path("run_logs") / "token_governance.json"
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _today(self) -> str:
        return date.today().isoformat()

    def _read(self) -> Dict[str, Dict[str, Dict[str, float | str]]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write(self, payload: Dict[str, Dict[str, Dict[str, float | str]]]) -> None:
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _normalize_tier(self, tier: str | TokenTier | None) -> TokenTier:
        if isinstance(tier, TokenTier):
            return tier
        value = (tier or TokenTier.FREE.value).strip().lower()
        return TokenTier(value) if value in {t.value for t in TokenTier} else TokenTier.FREE

    def get_remaining_budget(
        self,
        user_id: str,
        tier: str | TokenTier | None,
        day: str | None = None,
    ) -> float | None:
        """Return remaining USD for the user today. None means unlimited."""
        normalized_tier = self._normalize_tier(tier)
        cap = DEFAULT_TIERS[normalized_tier].daily_cap_usd
        if cap is None:
            return None

        key_date = day or self._today()
        with self._lock:
            data = self._read()
            spent = float(data.get(key_date, {}).get(user_id, {}).get("spent_usd", 0.0))

        return max(0.0, cap - spent)

    def apply_spend(
        self,
        user_id: str,
        tier: str | TokenTier | None,
        spend_usd: float,
        day: str | None = None,
    ) -> None:
        """Record post-run spend."""
        normalized_tier = self._normalize_tier(tier)
        key_date = day or self._today()

        with self._lock:
            data = self._read()
            day_bucket = data.setdefault(key_date, {})
            entry = day_bucket.setdefault(
                user_id,
                {"tier": normalized_tier.value, "spent_usd": 0.0},
            )
            entry["tier"] = normalized_tier.value
            entry["spent_usd"] = round(float(entry.get("spent_usd", 0.0)) + max(0.0, spend_usd), 6)
            self._write(data)

    def get_summary(
        self,
        user_id: str,
        tier: str | TokenTier | None,
        day: str | None = None,
    ) -> Dict[str, float | str | None]:
        normalized_tier = self._normalize_tier(tier)
        cap = DEFAULT_TIERS[normalized_tier].daily_cap_usd
        key_date = day or self._today()
        with self._lock:
            data = self._read()
            spent = float(data.get(key_date, {}).get(user_id, {}).get("spent_usd", 0.0))

        remaining = None if cap is None else max(0.0, cap - spent)
        return {
            "date": key_date,
            "user_id": user_id,
            "tier": normalized_tier.value,
            "daily_cap_usd": cap,
            "spent_usd": round(spent, 6),
            "remaining_usd": None if remaining is None else round(remaining, 6),
        }


_governance: TokenGovernance | None = None


def get_token_governance() -> TokenGovernance:
    global _governance
    if _governance is None:
        _governance = TokenGovernance()
    return _governance
