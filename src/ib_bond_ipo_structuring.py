"""Investment Banking Structuring Engine: Basel III Tier-2 Bond (DCM) & BSEC IPO Book-Building (ECM).

Module A (DCM Advisory):
  Models an illustrative BDT 5,000 Million Non-Convertible, Fully Redeemable, Unsecured
  Subordinated Tier-2 Floating-Rate Bond for a Tier-1 Commercial Bank in Bangladesh:
    - 7-Year Tenor with 20% annual principal redemption in Years 3-7
    - Floating Coupon: 6M FDR Benchmark (9.75%) + 275 bps Margin = 12.50% Indicative
      (Floor 11.00% / Cap 14.50%), semi-annual payments
    - Basel III RBCA Tier-2 regulatory amortization (100% -> 80% -> 60% -> 40% -> 20% in last 5 yrs)
    - Pro-forma CRAR uplift on BDT 352,000M RWA (14.40% -> 15.82%, +142 bps)
    - Modified Duration, Macaulay Duration & DV01 sensitivity

Module B (ECM Advisory):
  Models a BSEC Book-Building IPO Valuation & Dutch-Auction Cut-Off Price Discovery
  for an illustrative healthcare issuer (`Delta Precision Healthcare PLC`, BDT 1,200M Issue):
    - Triangulated Valuation (40% FCFF DCF + 35% EV/EBITDA + 25% Peer P/E) -> BDT 48.0 Indicative
    - BSEC +-25% Price Band Enforcement (BDT 36.0 - BDT 60.0)
    - Deterministic simulation of 65 Eligible Institutional Investor (EI) bids on ESS
    - Statistical Quartiles (5th / 25th / Median / Mean / 75th / 95th) + Cut-Off Price
    - General Public Offer Price (10% discount) & Post-IPO EPS / NAV dilution check
"""

from __future__ import annotations

from typing import Dict, List
import numpy as np


def model_tier2_subordinated_bond(
    issue_size_m: float = 5000.0,
    tenor_years: int = 7,
    ref_rate_pct: float = 9.75,
    margin_bps: int = 275,
    floor_pct: float = 11.00,
    cap_pct: float = 14.50,
    rwa_m: float = 352000.0,
    pre_tier1_m: float = 42944.0,
    pre_existing_tier2_m: float = 7744.0,
) -> Dict[str, object]:
    """Model cash flows, duration, Basel III Tier-2 eligibility, and CRAR uplift."""
    raw_coupon_pct = ref_rate_pct + (margin_bps / 100.0)
    coupon_pct = min(cap_pct, max(floor_pct, raw_coupon_pct))
    semi_rate = (coupon_pct / 100.0) / 2.0

    # Principal amortization: grace Y1-Y2 (0%), then 20% (BDT 1,000M) at end of Y3..Y7
    annual_rows: List[Dict[str, object]] = []
    outstanding = issue_size_m
    semi_cfs: List[float] = []
    semi_times: List[float] = []

    for yr in range(1, tenor_years + 1):
        beg_out = outstanding
        # Semi-annual interest coupons (first half & second half prior to annual redemption)
        c1 = beg_out * semi_rate
        c2 = beg_out * semi_rate
        redemption = round(issue_size_m * 0.20, 2) if yr >= 3 else 0.0
        outstanding = round(max(0.0, beg_out - redemption), 2)

        semi_cfs.extend([c1, c2 + redemption])
        semi_times.extend([yr - 0.5, float(yr)])

        # Basel III Tier-2 recognition amortizes 20%/yr in the final 5 years prior to maturity
        rem_years = tenor_years - yr + 1
        basel_elig_pct = 100.0 if rem_years >= 5 else rem_years * 20.0
        basel_cap_m = round(min(beg_out, issue_size_m * (basel_elig_pct / 100.0)), 1)

        annual_rows.append({
            "year": yr,
            "beg_outstanding_m": round(beg_out, 1),
            "annual_coupon_m": round(c1 + c2, 2),
            "principal_redemption_m": redemption,
            "end_outstanding_m": round(outstanding, 1),
            "total_debt_service_m": round(c1 + c2 + redemption, 2),
            "basel_elig_pct": basel_elig_pct,
            "tier2_capital_credit_m": basel_cap_m,
        })

    # Compute Macaulay & Modified Duration at par YTM = coupon_pct
    ytm_semi = semi_rate
    pv_cfs = [cf / ((1.0 + ytm_semi) ** (t * 2.0)) for cf, t in zip(semi_cfs, semi_times)]
    price_pv = float(sum(pv_cfs))
    mac_duration = float(sum(t * pv for t, pv in zip(semi_times, pv_cfs)) / price_pv)
    mod_duration = mac_duration / (1.0 + ytm_semi)
    dv01_m = price_pv * mod_duration * 0.0001  # Value sensitivity per 1 bps move

    pre_total_cap_m = pre_tier1_m + pre_existing_tier2_m
    pre_crar_pct = round((pre_total_cap_m / rwa_m) * 100.0, 2)
    post_total_cap_m = pre_total_cap_m + issue_size_m
    post_crar_pct = round((post_total_cap_m / rwa_m) * 100.0, 2)
    crar_uplift_bps = int(round((post_crar_pct - pre_crar_pct) * 100))

    return {
        "instrument_name": "7-Yr Basel III Subordinated Tier-2 Floating-Rate Bond",
        "issue_size_m": issue_size_m,
        "tenor_years": tenor_years,
        "ref_rate_pct": ref_rate_pct,
        "margin_bps": margin_bps,
        "indicative_coupon_pct": round(coupon_pct, 2),
        "floor_pct": floor_pct,
        "cap_pct": cap_pct,
        "macaulay_duration_yrs": round(mac_duration, 2),
        "modified_duration_yrs": round(mod_duration, 2),
        "dv01_m": round(dv01_m, 3),
        "rwa_m": rwa_m,
        "pre_crar_pct": pre_crar_pct,
        "post_crar_pct": post_crar_pct,
        "crar_uplift_bps": crar_uplift_bps,
        "schedule": annual_rows,
    }


def model_bsec_ipo_book_building(
    target_raise_m: float = 1200.0,
    ei_quota_share: float = 0.25,
    pre_ipo_shares_m: float = 110.0,
    pre_ipo_net_profit_m: float = 418.0,
    pre_ipo_nav_m: float = 3465.0,
    fcff_dcf_val: float = 50.2,
    ev_ebitda_val: float = 47.4,
    peer_pe_val: float = 45.3,
) -> Dict[str, object]:
    """Model BSEC IPO Book-Building Fair Value, EI Bid Distribution & Cut-Off Price."""
    indicative_price = round(0.40 * fcff_dcf_val + 0.35 * ev_ebitda_val + 0.25 * peer_pe_val, 1)
    band_low = round(indicative_price * 0.75, 1)
    band_high = round(indicative_price * 1.25, 1)

    rng = np.random.default_rng(42)
    # Simulate 65 Eligible Institutional Investor (EI) bids inside BSEC +-25% band
    n_eis = 65
    raw_bids = rng.normal(loc=51.8, scale=4.9, size=n_eis)
    bid_prices = np.round(np.clip(raw_bids, band_low, band_high), 1)
    bid_alloc_m = np.round(rng.uniform(7.5, 18.5, size=n_eis), 1)

    ei_target_m = round(target_raise_m * ei_quota_share, 1)  # BDT 300.0M (25% institutional quota)

    # Sort highest-to-lowest bid price to establish Dutch-auction clearing Cut-Off Price
    order = np.argsort(-bid_prices)
    sorted_prices = bid_prices[order]
    sorted_amounts = bid_alloc_m[order]

    cum_demand = 0.0
    cutoff_price = float(sorted_prices[-1])
    total_demand_m = float(np.sum(sorted_amounts))
    for p, amt in zip(sorted_prices, sorted_amounts):
        cum_demand += float(amt)
        if cum_demand >= ei_target_m:
            cutoff_price = float(p)
            break

    # Round cut-off price to nearest 1.0 BDT tick for clean institutional offer
    cutoff_price = round(cutoff_price, 1)
    public_offer_price = round(cutoff_price * 0.90, 1)  # 10% BSEC discount for retail investors

    # BSEC Statistical Summary of EI Bids
    pcts = np.percentile(bid_prices, [5, 25, 50, 75, 95])
    bid_stats = {
        "num_ei_bidders": n_eis,
        "p05_outlier": round(float(pcts[0]), 2),
        "p25_q1": round(float(pcts[1]), 2),
        "p50_median": round(float(pcts[2]), 2),
        "mean_bid": round(float(np.mean(bid_prices)), 2),
        "p75_q3": round(float(pcts[3]), 2),
        "p95_outlier": round(float(pcts[4]), 2),
        "total_ei_demand_m": round(total_demand_m, 1),
        "oversubscription_x": round(total_demand_m / ei_target_m, 2),
    }

    # Build cumulative demand curve by BDT 2.0 price buckets inside band
    price_grid = [round(band_low + i * 3.0, 1) for i in range(9)]
    demand_curve: List[Dict[str, float]] = []
    for p_lvl in price_grid:
        dem = float(np.sum(bid_amounts_at_or_above := bid_alloc_m[bid_prices >= p_lvl]))
        _ = bid_amounts_at_or_above
        demand_curve.append({
            "bid_price_bdt": p_lvl,
            "cum_demand_m": round(dem, 1),
            "ei_target_m": ei_target_m,
            "coverage_x": round(dem / ei_target_m, 2),
        })

    # Post-IPO share count & EPS/NAV accretion-dilution
    blended_issue_price = (ei_quota_share * cutoff_price) + ((1.0 - ei_quota_share) * public_offer_price)
    new_shares_m = round(target_raise_m / blended_issue_price, 2)
    post_shares_m = round(pre_ipo_shares_m + new_shares_m, 2)

    pre_eps = round(pre_ipo_net_profit_m / pre_ipo_shares_m, 2)
    post_eps_proforma = round(pre_ipo_net_profit_m / post_shares_m, 2)
    pre_navps = round(pre_ipo_nav_m / pre_ipo_shares_m, 2)
    post_navps = round((pre_ipo_nav_m + target_raise_m) / post_shares_m, 2)

    return {
        "issuer_name": "Delta Precision Healthcare PLC (Illustrative ECM Mandate)",
        "target_raise_m": target_raise_m,
        "ei_target_m": ei_target_m,
        "fcff_dcf_val": fcff_dcf_val,
        "ev_ebitda_val": ev_ebitda_val,
        "peer_pe_val": peer_pe_val,
        "indicative_price": indicative_price,
        "band_low": band_low,
        "band_high": band_high,
        "cutoff_price": cutoff_price,
        "public_offer_price": public_offer_price,
        "new_shares_m": new_shares_m,
        "pre_ipo_shares_m": pre_ipo_shares_m,
        "post_ipo_shares_m": post_shares_m,
        "pre_eps": pre_eps,
        "post_eps_proforma": post_eps_proforma,
        "pre_navps": pre_navps,
        "post_navps": post_navps,
        "bid_stats": bid_stats,
        "demand_curve": demand_curve,
    }


if __name__ == "__main__":
    bond = model_tier2_subordinated_bond()
    ipo = model_bsec_ipo_book_building()
    print("=== DCM: BASEL III TIER-2 SUBORDINATED BOND ===")
    print(
        f"Issue: BDT {bond['issue_size_m']:.0f}M | Coupon: {bond['indicative_coupon_pct']:.2f}% | "
        f"Mod Duration: {bond['modified_duration_yrs']:.2f} yrs | CRAR: {bond['pre_crar_pct']:.2f}% -> "
        f"{bond['post_crar_pct']:.2f}% (+{bond['crar_uplift_bps']} bps)"
    )
    print("\n=== ECM: BSEC IPO BOOK-BUILDING ===")
    bs = ipo["bid_stats"]
    print(
        f"Indicative: BDT {ipo['indicative_price']:.1f} | Band: BDT {ipo['band_low']:.1f}-{ipo['band_high']:.1f} | "
        f"EI Demand: BDT {bs['total_ei_demand_m']:.1f}M ({bs['oversubscription_x']:.2f}x) | "
        f"Cut-Off: BDT {ipo['cutoff_price']:.1f} | Public (-10%): BDT {ipo['public_offer_price']:.1f}"
    )
    print(f"Pro-Forma EPS: BDT {ipo['pre_eps']:.2f} -> {ipo['post_eps_proforma']:.2f} | NAV/sh: BDT {ipo['pre_navps']:.2f} -> {ipo['post_navps']:.2f}")
