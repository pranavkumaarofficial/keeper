#!/usr/bin/env python3
"""
The Siege Curve
===============
A toy model for why goalkeepers are having a monster 2026 World Cup.

Thesis (a causal chain, not a claim of proof):
    bigger field  ->  more mismatched games  ->  more "siege" games
    (one keeper peppered with shots)  ->  more huge single-match save counts.

This script does two things:
  1. Defines "The Siege Curve": expected saves for the underdog keeper as a
     function of the favourite's win probability, calibrated to real anchors.
  2. Runs a Monte Carlo comparing a 32-team and a 48-team group stage, and
     decomposes the rise in siege games into a VOLUME effect (more matches)
     and a MISMATCH effect (a higher siege rate *per* match).

Everything is a stated-assumption model. It is calibrated to a handful of real
2026 data points; it is NOT a regression on a full match dataset. Read the
ASSUMPTIONS block, disagree with the numbers, and re-run — that's the point.

Anchors used for calibration (all sourced: FIFA / Opta / ESPN / FOX):
  * Vozinha (Cape Verde #67) vs Spain (#2): faced 7 shots on target, 7 saves.
  * Baseline World Cup keeper faces ~3.3 shots on target per game.
  * Elite tournament save rate ~0.70 (Vozinha's was .782).

Author: Pranav Kumaar  |  MIT License
"""

import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(42)

# ----------------------------- ASSUMPTIONS -----------------------------------
SAVE_PROB      = 0.70    # prob a shot on target is saved (elite ~0.70-0.78)
BASE_SOT       = 3.3     # shots on target the underdog keeper faces in an EVEN game
STEEPNESS_K    = 2.16    # how fast shot volume grows with mismatch (calibrated below)
ELO_TOP        = 2050.0  # strongest nation in the pool
ELO_BOT        = 1500.0  # weakest nation once the field is expanded
N_SIMS         = 20000   # simulated tournaments per format

SIEGE   = 8    # a "siege game": one keeper makes >= 8 saves
RECORD  = 16   # the all-time single-match record (Howard '14, Room '26)


# ----------------------------- THE MODEL -------------------------------------
def win_prob(elo_fav, elo_dog):
    """Standard Elo win probability for the favourite."""
    return 1.0 / (1.0 + 10 ** (-(elo_fav - elo_dog) / 400.0))

def expected_sot(w):
    """
    The Siege Curve core: expected shots on target faced by the UNDERDOG keeper
    as a function of the favourite's win probability w.
    Exponential in the mismatch, calibrated so an even game -> BASE_SOT and a
    heavy favourite (w ~ 0.88) -> ~7.5 SoT (the Vozinha-vs-Spain anchor).
    """
    return BASE_SOT * np.exp(STEEPNESS_K * (w - 0.5))

def expected_saves(w):
    """Expected saves = save rate x expected shots on target faced."""
    return SAVE_PROB * expected_sot(w)


def calibrate():
    """Print how the model maps mismatch -> expected saves, vs the real anchor."""
    print("=== CALIBRATION: The Siege Curve ===")
    print(f"{'fav win prob':>12} | {'exp. SoT faced':>14} | {'exp. saves':>10}")
    for w in (0.50, 0.60, 0.70, 0.80, 0.88, 0.92, 0.95):
        print(f"{w:>12.2f} | {expected_sot(w):>14.1f} | {expected_saves(w):>10.1f}")
    # where did Vozinha vs Spain sit?
    w_spain = win_prob(2050, 2050 - 550 * (67 - 2) / 65)  # rough: map rank gap onto elo span
    print(f"\nVozinha vs Spain: model expected ~{expected_saves(0.88):.1f} saves; "
          f"he made 7 (a positive-variance night on top of an already-high mean).")


# --------------------------- MONTE CARLO -------------------------------------
def make_field(n_teams):
    """Assign Elo ratings. The 48-team field extends the WEAK tail downward."""
    # full 48-pool spans ELO_TOP..ELO_BOT; a 32-team field = the top 32 of it.
    pool = np.linspace(ELO_TOP, ELO_BOT, 48)
    return pool[:n_teams].copy()

def group_matches(ratings):
    """Random draw into groups of 4; return every group-stage pairing (i<j)."""
    idx = rng.permutation(len(ratings))
    matches = []
    for g in range(0, len(idx), 4):
        grp = idx[g:g + 4]
        for a in range(len(grp)):
            for b in range(a + 1, len(grp)):
                matches.append((ratings[grp[a]], ratings[grp[b]]))
    return matches

def simulate_tournament(n_teams):
    """One group stage. Return (n_matches, siege_count, record_hit)."""
    ratings = make_field(n_teams)
    matches = group_matches(ratings)
    siege = 0
    record_hit = False
    for r1, r2 in matches:
        fav, dog = max(r1, r2), min(r1, r2)
        w = win_prob(fav, dog)
        # underdog keeper (busy) and favourite keeper (quiet)
        sot_dog = rng.poisson(expected_sot(w))
        sot_fav = rng.poisson(expected_sot(1 - w))
        saves_dog = rng.binomial(sot_dog, SAVE_PROB)
        saves_fav = rng.binomial(sot_fav, SAVE_PROB)
        busiest = max(saves_dog, saves_fav)
        if busiest >= SIEGE:
            siege += 1
        if busiest >= RECORD:
            record_hit = True
    return len(matches), siege, record_hit

def run(n_teams, label):
    matches0 = None
    sieges = np.empty(N_SIMS)
    records = 0
    for i in range(N_SIMS):
        m, s, rec = simulate_tournament(n_teams)
        matches0 = m
        sieges[i] = s
        records += rec
    out = {
        "label": label,
        "teams": n_teams,
        "matches": matches0,
        "mean_sieges": sieges.mean(),
        "siege_rate_per_match": sieges.mean() / matches0,
        "siege_rate_per_100": 100 * sieges.mean() / matches0,
        "p_record": records / N_SIMS,
        "sieges_dist": sieges,
    }
    return out


def main():
    calibrate()

    print("\n=== MONTE CARLO: 32-team vs 48-team group stage ===")
    print(f"(assumptions: save rate {SAVE_PROB}, base SoT {BASE_SOT}, "
          f"steepness {STEEPNESS_K}, {N_SIMS:,} sims each)\n")

    a = run(32, "32-team (2022 format)")
    b = run(48, "48-team (2026 format)")

    for r in (a, b):
        print(f"{r['label']}")
        print(f"   group matches ............ {r['matches']}")
        print(f"   avg siege games (>=8 sv) . {r['mean_sieges']:.2f}")
        print(f"   siege games per 100 games  {r['siege_rate_per_100']:.2f}")
        print(f"   P(a record-tying >=16 game){r['p_record']*100:.1f}%")
        print()

    # ---- THE DECOMPOSITION (the novel bit) ----
    total_ratio  = b["mean_sieges"] / a["mean_sieges"]
    volume_ratio = b["matches"] / a["matches"]
    rate_ratio   = b["siege_rate_per_match"] / a["siege_rate_per_match"]
    print("=== DECOMPOSITION: why sieges rise faster than the field ===")
    print(f"   total siege-game increase .. x{total_ratio:.2f}")
    print(f"   = VOLUME effect (more games) x{volume_ratio:.2f}")
    print(f"   x MISMATCH effect (per game) x{rate_ratio:.2f}")
    print(f"   field grew only ............ x{48/32:.2f}")
    print(f"   record-tying game { b['p_record']/max(a['p_record'],1e-9):.1f}x "
          f"more likely in the 48-team field")

    # ---- FIGURES ----
    _fig_curve()
    _fig_montecarlo(a, b)
    print("\nsaved: siege_curve.png, siege_montecarlo.png")
    return a, b


# ------------------------------- PLOTS ---------------------------------------
GREEN, GREY, DARK, LIGHT = "#1a8917", "#b8b8b8", "#242424", "#eeeeee"

def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(color=LIGHT, zorder=0)

def _fig_curve():
    w = np.linspace(0.5, 0.96, 200)
    plt.figure(figsize=(8.4, 5.2), dpi=200)
    ax = plt.gca()
    ax.plot(w, expected_saves(w), color=GREEN, lw=3, zorder=3)
    ax.axhline(SIEGE, color=DARK, ls=":", lw=1.3)
    ax.text(0.505, SIEGE + 0.15, "siege line (8 saves)", fontsize=9.5, style="italic")
    ax.scatter([0.88], [7], color=DARK, zorder=5, s=45)
    ax.annotate("Vozinha vs Spain\n(real: 7 saves)", xy=(0.88, 7),
                xytext=(0.72, 8.6), fontsize=10, color=DARK,
                arrowprops=dict(arrowstyle="->", color=DARK))
    ax.set_xlabel("favourite's win probability  (bigger = bigger mismatch)")
    ax.set_ylabel("expected saves, underdog keeper")
    ax.set_title("The Siege Curve: mismatch drives save volume",
                 fontsize=15, fontweight="bold", loc="left")
    _style(ax)
    plt.tight_layout()
    plt.savefig("siege_curve.png", facecolor="white", bbox_inches="tight")
    plt.close()

def _fig_montecarlo(a, b):
    plt.figure(figsize=(8.4, 5.2), dpi=200)
    ax = plt.gca()
    lo = int(min(a["sieges_dist"].min(), b["sieges_dist"].min()))
    hi = int(max(a["sieges_dist"].max(), b["sieges_dist"].max()))
    bins = np.arange(lo, hi + 2) - 0.5
    ax.hist(a["sieges_dist"], bins=bins, color=GREY, alpha=0.8,
            label=f"32-team  (avg {a['mean_sieges']:.1f})", density=True, zorder=3)
    ax.hist(b["sieges_dist"], bins=bins, color=GREEN, alpha=0.7,
            label=f"48-team  (avg {b['mean_sieges']:.1f})", density=True, zorder=3)
    ax.axvline(a["mean_sieges"], color=GREY, ls="--", lw=1.5)
    ax.axvline(b["mean_sieges"], color=GREEN, ls="--", lw=1.5)
    ax.set_xlabel("siege games (>= 8 saves) per group stage")
    ax.set_ylabel("probability")
    ax.set_title("More field, more sieges — and not just from more games",
                 fontsize=15, fontweight="bold", loc="left")
    ax.legend(frameon=False, fontsize=11)
    _style(ax)
    plt.tight_layout()
    plt.savefig("siege_montecarlo.png", facecolor="white", bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
