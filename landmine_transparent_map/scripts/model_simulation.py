"""
Mathematical model for transparent minefield mapping with dummy positions.

Core framework:
- Defender places N_real mines across a barrier zone (W × D_depth)
- A map is published showing M = N_real * (1 + r) positions (real + dummy)
- Attacker cannot distinguish real from dummy on the map
- To breach, attacker must clear all marked positions in their lane
- Post-conflict: all M positions are cleared systematically → guaranteed safe

Key insight: dummy ratio r is a policy-tuneable parameter that controls
the trade-off between military effectiveness and post-conflict clearance cost.
"""

import numpy as np
from scipy.optimize import minimize_scalar
import json
from pathlib import Path


class MineFieldParams:
    """Parameters for a transparent minefield scenario."""

    def __init__(
        self,
        N_real: int = 200,           # Number of real mines
        W: float = 5000.0,           # Front width (metres)
        D_depth: float = 300.0,      # Minefield depth (metres)
        w_breach: float = 100.0,     # Breach lane width (metres)
        t_clear: float = 30.0,       # Time to clear one marked position (minutes)
        t_probe: float = 5.0,        # Time to probe one grid cell blindly (minutes)
        k_teams: int = 10,           # Number of parallel clearance teams
        grid_spacing: float = 5.0,   # Detection grid resolution for blind sweep (metres)
        p_detect_blind: float = 0.95,  # Detection probability per mine in blind sweep
        c_clear: float = 500.0,      # Cost per position clearance (USD)
        c_casualty: float = 1e6,     # Cost per casualty (USD)
        p_casualty: float = 0.15,    # Casualty probability if mine encountered
    ):
        self.N_real = N_real
        self.W = W
        self.D_depth = D_depth
        self.w_breach = w_breach
        self.t_clear = t_clear
        self.t_probe = t_probe
        self.k_teams = k_teams
        self.grid_spacing = grid_spacing
        self.p_detect_blind = p_detect_blind
        self.c_clear = c_clear
        self.c_casualty = c_casualty
        self.p_casualty = p_casualty

    @property
    def A_total(self) -> float:
        """Total minefield area (m^2)."""
        return self.W * self.D_depth

    @property
    def A_breach(self) -> float:
        """Breach lane area (m^2)."""
        return self.w_breach * self.D_depth

    @property
    def cells_in_breach(self) -> int:
        """Number of grid cells in a breach lane (for blind sweep)."""
        return int(self.A_breach / (self.grid_spacing ** 2))

    @property
    def cells_total(self) -> int:
        """Total grid cells in entire minefield (for post-conflict blind sweep)."""
        return int(self.A_total / (self.grid_spacing ** 2))


# ─── Breach Delay Model ──────────────────────────────────────────────────────

def positions_in_breach(params: MineFieldParams, r: float) -> float:
    """Number of marked positions (real + dummy) in a breach lane."""
    M = params.N_real * (1.0 + r)
    # Positions distributed over area; fraction in breach lane
    return M * (params.A_breach / params.A_total)


def delay_map(params: MineFieldParams, r: float) -> float:
    """
    Breach time (minutes) with published map at dummy ratio r.
    Attacker identifies and clears all marked positions in the breach lane.
    """
    n_pos = positions_in_breach(params, r)
    return n_pos * params.t_clear / params.k_teams


def delay_full_intel(params: MineFieldParams) -> float:
    """
    Breach time (minutes) with full intelligence (r=0, exact positions known).
    Only real mines in breach lane need clearing.
    """
    n_real_in_breach = params.N_real * (params.A_breach / params.A_total)
    return n_real_in_breach * params.t_clear / params.k_teams


def delay_blind(params: MineFieldParams) -> float:
    """
    Breach time (minutes) with no map (current regime).
    Attacker must sweep entire breach lane cell by cell using detection equipment.
    """
    return params.cells_in_breach * params.t_probe / params.k_teams


def delay_multiplier_vs_intel(params: MineFieldParams, r: float) -> float:
    """How much harder breaching is compared to full intelligence. = (1+r)."""
    return 1.0 + r


def delay_ratio_vs_blind(params: MineFieldParams, r: float) -> float:
    """Ratio: breach time with map / breach time blind sweep."""
    return delay_map(params, r) / delay_blind(params)


# ─── Post-Conflict Clearance Model ───────────────────────────────────────────

def postconflict_time_map(params: MineFieldParams, r: float) -> float:
    """
    Post-conflict clearance time (hours) with map.
    All M marked positions are systematically cleared. Guaranteed complete.
    """
    M = params.N_real * (1.0 + r)
    return M * params.t_clear / (params.k_teams * 60.0)


def postconflict_time_blind(params: MineFieldParams) -> float:
    """
    Post-conflict clearance time (hours) without map.
    Must sweep entire area cell by cell.
    """
    return params.cells_total * params.t_probe / (params.k_teams * 60.0)


def postconflict_residual_blind(params: MineFieldParams) -> float:
    """Expected residual (undetected) mines after blind sweep."""
    return params.N_real * (1.0 - params.p_detect_blind)


def postconflict_residual_map(params: MineFieldParams, r: float) -> float:
    """Residual mines after map-based clearance. Always 0."""
    return 0.0


def clearance_efficiency(params: MineFieldParams, r: float) -> float:
    """
    Efficiency gain: how many times faster is map-based clearance than blind.
    = time_blind / time_map
    """
    t_map = postconflict_time_map(params, r)
    if t_map == 0:
        return float('inf')
    return postconflict_time_blind(params) / t_map


# ─── Information-Theoretic Model ─────────────────────────────────────────────

def entropy_no_map(params: MineFieldParams) -> float:
    """
    Positional entropy (bits) with no map.
    Attacker must consider all possible placements of N_real mines in grid cells.
    H ≈ N_total * H_binary(N_real/N_total) using binary entropy approximation.
    """
    N = params.cells_total
    k = params.N_real
    p = k / N
    if p <= 0 or p >= 1:
        return 0.0
    return N * (-p * np.log2(p) - (1 - p) * np.log2(1 - p))


def entropy_with_map(params: MineFieldParams, r: float) -> float:
    """
    Positional entropy (bits) with map at dummy ratio r.
    Attacker knows N_real mines are among M = N_real*(1+r) marked positions.
    H ≈ M * H_binary(N_real/M)
    """
    M = params.N_real * (1.0 + r)
    k = params.N_real
    if M <= k:
        return 0.0
    p = k / M
    if p <= 0 or p >= 1:
        return 0.0
    return M * (-p * np.log2(p) - (1 - p) * np.log2(1 - p))


def entropy_reduction(params: MineFieldParams, r: float) -> float:
    """Fraction of entropy remaining: H(map)/H(no_map). Lower = more info given."""
    H_no = entropy_no_map(params)
    if H_no == 0:
        return 0.0
    return entropy_with_map(params, r) / H_no


# ─── Game-Theoretic: Attacker's Decision ─────────────────────────────────────

def attacker_marginal_benefit(params: MineFieldParams, r: float) -> float:
    """
    Marginal benefit of clearing one position:
    = P(position is real) × P(casualty|mine) × C(casualty)
    = [1/(1+r)] × p_casualty × c_casualty
    """
    return (1.0 / (1.0 + r)) * params.p_casualty * params.c_casualty


def attacker_clears_all(params: MineFieldParams, r: float) -> bool:
    """
    Does the attacker rationally clear all positions?
    Yes if marginal benefit > marginal cost (c_clear per position).
    """
    return attacker_marginal_benefit(params, r) > params.c_clear


def r_critical(params: MineFieldParams) -> float:
    """
    Critical r above which attacker may choose to NOT clear all positions.
    Solve: [1/(1+r*)] × p_casualty × c_casualty = c_clear
    → r* = (p_casualty × c_casualty / c_clear) - 1
    """
    return (params.p_casualty * params.c_casualty / params.c_clear) - 1.0


# ─── Social Welfare / Treaty Design ──────────────────────────────────────────

def delay_ratio(params: MineFieldParams, r: float) -> float:
    """
    Breach delay ratio: delay_map(r) / delay_blind.
    Values > 1 mean the map regime imposes MORE delay than blind breach.
    """
    return delay_map(params, r) / delay_blind(params)


def normalised_delay(params: MineFieldParams, r: float) -> float:
    """
    Military utility with diminishing marginal returns.
    Uses concave (square-root) function of delay ratio, capped at 1.0
    (blind-sweep equivalence — rational attacker switches to blind sweep
    if map-based clearance takes longer).

    sqrt scaling reflects that the first hours of delay have disproportionate
    military value (enabling mobilisation, NATO rapid reaction force
    deployment) compared to later hours.
    """
    raw = delay_map(params, r) / delay_blind(params)
    if raw >= 1.0:
        return 1.0
    return float(np.sqrt(raw))


def normalised_clearance_cost(params: MineFieldParams, r: float) -> float:
    """
    Humanitarian cost: post-conflict clearance time relative to blind sweep.
    = time_map(r) / time_blind
    Scales linearly with (1+r): each additional dummy position adds constant
    marginal clearance burden.
    """
    return postconflict_time_map(params, r) / postconflict_time_blind(params)


def welfare(params: MineFieldParams, r: float,
            alpha: float = 0.5, beta: float = 0.5) -> float:
    """
    Social welfare W(r) = α × sqrt(delay_ratio) - β × clearance_cost_ratio

    Military utility uses concave (sqrt) scaling to reflect diminishing
    marginal returns of delay. Humanitarian cost is linear. The asymmetry
    produces a genuine interior optimum: at low r, marginal military benefit
    per unit clearance cost is high; at high r, it diminishes.

    For balanced weights (α=β=0.5), optimum occurs at r where
    d(sqrt(x))/dx = β/α → r* ≈ 11.5 (baseline parameters).
    """
    mil = normalised_delay(params, r)
    hum = normalised_clearance_cost(params, r)
    return alpha * mil - beta * hum


def find_optimal_r(params: MineFieldParams, alpha: float = 0.5,
                   beta: float = 0.5, r_max: float = 50.0) -> dict:
    """Find r that maximises social welfare."""
    result = minimize_scalar(
        lambda r: -welfare(params, r, alpha, beta),
        bounds=(0, r_max),
        method='bounded'
    )
    r_opt = result.x
    return {
        "r_optimal": round(r_opt, 2),
        "welfare": round(-result.fun, 4),
        "delay_min": round(delay_map(params, r_opt), 1),
        "clearance_hours": round(postconflict_time_map(params, r_opt), 1),
    }


# ─── Scenario Comparison (Table for paper) ───────────────────────────────────

def scenario_table(params: MineFieldParams) -> list:
    """Generate comparison table for key dummy ratios."""
    rows = []
    for r in [0, 1, 2, 3, 5, 10, 20]:
        rows.append({
            "r": r,
            "M": int(params.N_real * (1 + r)),
            "positions_in_lane": round(positions_in_breach(params, r), 1),
            "breach_delay_min": round(delay_map(params, r), 1),
            "delay_vs_blind": round(delay_ratio_vs_blind(params, r), 2),
            "clearance_hours": round(postconflict_time_map(params, r), 1),
            "efficiency_vs_blind": round(clearance_efficiency(params, r), 1),
            "entropy_bits": round(entropy_with_map(params, r), 0),
            "residual_mines": 0,
            "attacker_clears": attacker_clears_all(params, r),
        })
    return rows


# ─── Run Full Simulation ─────────────────────────────────────────────────────

def run_full_simulation(params: MineFieldParams = None) -> dict:
    """Run the complete simulation and return all results."""
    if params is None:
        params = MineFieldParams()

    r_values = np.linspace(0, 20, 201)

    results = {
        "params": {
            "N_real": params.N_real,
            "W": params.W,
            "D_depth": params.D_depth,
            "w_breach": params.w_breach,
            "t_clear": params.t_clear,
            "t_probe": params.t_probe,
            "k_teams": params.k_teams,
            "grid_spacing": params.grid_spacing,
            "p_detect_blind": params.p_detect_blind,
        },
        "r_values": r_values.tolist(),
        "breach_delay": [delay_map(params, r) for r in r_values],
        "delay_ratio_vs_blind": [delay_ratio_vs_blind(params, r) for r in r_values],
        "clearance_hours": [postconflict_time_map(params, r) for r in r_values],
        "clearance_efficiency": [clearance_efficiency(params, r) for r in r_values],
        "entropy_map": [entropy_with_map(params, r) for r in r_values],
        "entropy_ratio": [entropy_reduction(params, r) for r in r_values],
        "welfare_balanced": [welfare(params, r, 0.5, 0.5) for r in r_values],
        "welfare_defence": [welfare(params, r, 0.7, 0.3) for r in r_values],
        "welfare_humanitarian": [welfare(params, r, 0.3, 0.7) for r in r_values],
    }

    # Key scalars
    results["delay_blind_min"] = round(delay_blind(params), 1)
    results["delay_full_intel_min"] = round(delay_full_intel(params), 1)
    results["clearance_blind_hours"] = round(postconflict_time_blind(params), 1)
    results["residual_blind"] = round(postconflict_residual_blind(params), 1)
    results["entropy_no_map"] = round(entropy_no_map(params), 0)
    results["r_critical"] = round(r_critical(params), 1)
    results["optimal_balanced"] = find_optimal_r(params, 0.5, 0.5)
    results["optimal_defence"] = find_optimal_r(params, 0.7, 0.3)
    results["optimal_humanitarian"] = find_optimal_r(params, 0.3, 0.7)
    results["scenario_table"] = scenario_table(params)

    return results


if __name__ == "__main__":
    params = MineFieldParams()
    results = run_full_simulation(params)

    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "simulation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("=" * 70)
    print("TRANSPARENT MINEFIELD MODEL — KEY RESULTS")
    print("=" * 70)
    print(f"\nScenario: N={params.N_real} mines, front={params.W}m, "
          f"depth={params.D_depth}m, breach lane={params.w_breach}m")
    print(f"Clearance: {params.t_clear} min/position, "
          f"{params.k_teams} teams, blind probe: {params.t_probe} min/cell")
    print(f"Grid: {params.grid_spacing}m → {params.cells_in_breach} cells "
          f"in breach, {params.cells_total} cells total")

    print(f"\n--- Breach Delay ---")
    print(f"Blind sweep (no map):     {results['delay_blind_min']} min")
    print(f"Full intelligence (r=0):  {results['delay_full_intel_min']} min")
    for r in [1, 3, 5, 10]:
        print(f"Map with r={r}:            {delay_map(params, r):.0f} min "
              f"({delay_ratio_vs_blind(params, r):.2f}× blind)")

    print(f"\n--- Post-Conflict Clearance ---")
    print(f"Blind sweep:  {results['clearance_blind_hours']} hours, "
          f"residual: {results['residual_blind']} mines")
    print(f"Map (r=0):    {postconflict_time_map(params, 0):.1f} hours, "
          f"residual: 0 mines")
    for r in [3, 5, 10]:
        print(f"Map (r={r}):   {postconflict_time_map(params, r):.1f} hours, "
              f"residual: 0 mines")

    print(f"\n--- Game Theory ---")
    print(f"r* (critical ratio): {results['r_critical']}")
    print(f"  Below r*: attacker always clears all positions")
    print(f"  Above r*: attacker may accept risk (irrational for modern armies)")

    print(f"\n--- Information Entropy ---")
    print(f"No map:  {results['entropy_no_map']:.0f} bits")
    for r in [1, 3, 5, 10]:
        print(f"Map r={r}: {entropy_with_map(params, r):.0f} bits "
              f"({entropy_reduction(params, r):.1%} of no-map)")

    print(f"\n--- Optimal Treaty Design ---")
    print(f"Balanced (α=0.5, β=0.5): r* = {results['optimal_balanced']}")
    print(f"Defence-priority (α=0.7): r* = {results['optimal_defence']}")
    print(f"Humanitarian (β=0.7):    r* = {results['optimal_humanitarian']}")

    print(f"\n--- Scenario Table ---")
    print(f"{'r':>3} | {'M':>5} | {'Breach':>8} | {'vs Blind':>8} | "
          f"{'Clear(h)':>8} | {'Effic':>6} | {'Entropy':>7} | {'Clears?':>7}")
    print("-" * 70)
    for row in results["scenario_table"]:
        print(f"{row['r']:>3} | {row['M']:>5} | {row['breach_delay_min']:>7.0f}m | "
              f"{row['delay_vs_blind']:>7.2f}× | "
              f"{row['clearance_hours']:>7.1f}h | {row['efficiency_vs_blind']:>5.1f}× | "
              f"{row['entropy_bits']:>6.0f}b | {'Yes' if row['attacker_clears'] else 'No':>7}")
