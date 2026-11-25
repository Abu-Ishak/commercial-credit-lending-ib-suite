"""Bangladesh Bank CAMELS Supervisory Rating Scorecard for DSE Tier-1 Banks.

Evaluates the four covered Dhaka Stock Exchange (DSE) commercial banks:
  - BRAC Bank PLC (BRACBANK)
  - The City Bank PLC (CITYBANK)
  - Eastern Bank PLC (EBL)
  - Prime Bank PLC (PRIMEBANK)

Anchors CRAR, NPL, and ROE verbatim to the audited FY2025/2026 baseline used
in `dse_banking_dcf_engine.py`, alongside prudential Liquidity (ADR, LCR),
Cost-to-Income efficiency, and Market/Interest-Rate Sensitivity (S) metrics.

Supervisory Weights:
  C (20%) + A (25%) + M (15%) + E (20%) + L (10%) + S (10%) = 100%
Scale: 1.00 (Strong) -> 5.00 (Unsatisfactory); lower score = stronger bank.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


CAMELS_WEIGHTS: Dict[str, float] = {
    "C": 0.20,  # Capital Adequacy
    "A": 0.25,  # Asset Quality
    "M": 0.15,  # Management Capability
    "E": 0.20,  # Earnings & Profitability
    "L": 0.10,  # Liquidity Profile
    "S": 0.10,  # Sensitivity to Market & Interest-Rate Risk
}


@dataclass(frozen=True)
class BankCamelsProfile:
    """Grounded FY2025/2026 prudential indicators for DSE Tier-1 Banks."""

    ticker: str
    bank_name: str
    crar_pct: float                 # Basel III CRAR (exact match to dse_banking_dcf_engine.py)
    tier1_ratio_pct: float          # CET1 / Tier-1 adequacy
    npl_pct: float                  # Gross NPL ratio (exact match to dse_banking_dcf_engine.py)
    provision_coverage_pct: float   # Specific + general coverage vs NPL
    cost_to_income_pct: float       # Operating Cost-to-Income ratio
    roe_pct: float                  # Return on Equity (exact match to dse_banking_dcf_engine.py)
    nim_pct: float                  # Net Interest Margin
    adr_pct: float                  # Advance-to-Deposit Ratio (BB ceiling ~87%)
    lcr_pct: float                  # Basel III Liquidity Coverage Ratio (min 100%)
    rate_sensitivity_note: str
    # Component scores (1.00 = Strongest, 5.00 = Unsatisfactory)
    c_score: float
    a_score: float
    m_score: float
    e_score: float
    l_score: float
    s_score: float


CAMELS_BANKS: List[BankCamelsProfile] = [
    BankCamelsProfile(
        ticker="BRACBANK",
        bank_name="BRAC Bank PLC",
        crar_pct=15.80,
        tier1_ratio_pct=13.45,
        npl_pct=2.27,
        provision_coverage_pct=132.0,
        cost_to_income_pct=44.2,
        roe_pct=19.70,
        nim_pct=4.85,
        adr_pct=81.4,
        lcr_pct=142.0,
        rate_sensitivity_note="Balanced SME re-pricing + low-cost CASA & bKash float shield",
        c_score=1.45,
        a_score=1.25,
        m_score=1.35,
        e_score=1.35,
        l_score=1.55,
        s_score=1.70,
    ),
    BankCamelsProfile(
        ticker="PRIMEBANK",
        bank_name="Prime Bank PLC",
        crar_pct=18.07,
        tier1_ratio_pct=14.90,
        npl_pct=2.73,
        provision_coverage_pct=118.5,
        cost_to_income_pct=41.8,
        roe_pct=20.85,
        nim_pct=4.40,
        adr_pct=79.8,
        lcr_pct=148.0,
        rate_sensitivity_note="Sector-highest 18.07% CRAR (+557 bps buffer) absorbs yield shifts",
        c_score=1.15,
        a_score=1.55,
        m_score=1.55,
        e_score=1.30,
        l_score=1.50,
        s_score=1.60,
    ),
    BankCamelsProfile(
        ticker="CITYBANK",
        bank_name="The City Bank PLC",
        crar_pct=16.05,
        tier1_ratio_pct=12.60,
        npl_pct=2.79,
        provision_coverage_pct=116.0,
        cost_to_income_pct=46.5,
        roe_pct=19.50,
        nim_pct=4.65,
        adr_pct=82.2,
        lcr_pct=136.0,
        rate_sensitivity_note="Card fee & retail float diversify NII sensitivity vs deposit repricing",
        c_score=1.40,
        a_score=1.60,
        m_score=1.50,
        e_score=1.45,
        l_score=1.65,
        s_score=1.75,
    ),
    BankCamelsProfile(
        ticker="EBL",
        bank_name="Eastern Bank PLC",
        crar_pct=15.49,
        tier1_ratio_pct=12.25,
        npl_pct=2.80,
        provision_coverage_pct=121.0,
        cost_to_income_pct=39.6,
        roe_pct=16.70,
        nim_pct=4.15,
        adr_pct=80.6,
        lcr_pct=139.0,
        rate_sensitivity_note="Disciplined corporate duration matching & lean 39.6% Cost/Income",
        c_score=1.55,
        a_score=1.65,
        m_score=1.45,
        e_score=1.65,
        l_score=1.60,
        s_score=1.70,
    ),
]


def score_camels(bank: BankCamelsProfile) -> Dict[str, object]:
    """Compute weighted CAMELS composite score and supervisory classification."""
    composite = round(
        CAMELS_WEIGHTS["C"] * bank.c_score
        + CAMELS_WEIGHTS["A"] * bank.a_score
        + CAMELS_WEIGHTS["M"] * bank.m_score
        + CAMELS_WEIGHTS["E"] * bank.e_score
        + CAMELS_WEIGHTS["L"] * bank.l_score
        + CAMELS_WEIGHTS["S"] * bank.s_score,
        2,
    )
    if composite <= 1.50:
        rating_num = 1
        band = "1 - Strong (Top-Decile Prudential)"
    elif composite <= 2.50:
        rating_num = 2
        band = "2 - Satisfactory (Sound Tier-1)"
    elif composite <= 3.50:
        rating_num = 3
        band = "3 - Fair (Supervisory Watch)"
    else:
        rating_num = 4
        band = "4 - Marginal / Unsatisfactory"

    return {
        "ticker": bank.ticker,
        "bank_name": bank.bank_name,
        "crar_pct": bank.crar_pct,
        "crar_headroom_bps": int(round((bank.crar_pct - 12.50) * 100)),
        "tier1_ratio_pct": bank.tier1_ratio_pct,
        "npl_pct": bank.npl_pct,
        "provision_coverage_pct": bank.provision_coverage_pct,
        "cost_to_income_pct": bank.cost_to_income_pct,
        "roe_pct": bank.roe_pct,
        "nim_pct": bank.nim_pct,
        "adr_pct": bank.adr_pct,
        "lcr_pct": bank.lcr_pct,
        "c_score": bank.c_score,
        "a_score": bank.a_score,
        "m_score": bank.m_score,
        "e_score": bank.e_score,
        "l_score": bank.l_score,
        "s_score": bank.s_score,
        "composite": composite,
        "rating_num": rating_num,
        "supervisory_band": band,
        "rate_sensitivity_note": bank.rate_sensitivity_note,
    }


def evaluate_all_camels() -> List[Dict[str, object]]:
    """Return sorted CAMELS scorecard (strongest / lowest composite first)."""
    rows = [score_camels(b) for b in CAMELS_BANKS]
    return sorted(rows, key=lambda r: float(r["composite"]))


if __name__ == "__main__":
    print("=== BANGLADESH BANK CAMELS SUPERVISORY SCORECARD (DSE TIER-1 BANKS) ===")
    for r in evaluate_all_camels():
        print(
            f"{r['ticker']:10s} | Composite: {r['composite']:.2f} [{r['supervisory_band']:30s}] | "
            f"C:{r['c_score']:.2f} A:{r['a_score']:.2f} M:{r['m_score']:.2f} "
            f"E:{r['e_score']:.2f} L:{r['l_score']:.2f} S:{r['s_score']:.2f} | "
            f"CRAR:{r['crar_pct']:.2f}% NPL:{r['npl_pct']:.2f}% ROE:{r['roe_pct']:.2f}%"
        )
