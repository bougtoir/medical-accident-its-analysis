"""
Three-body gravitational scattering simulator.

Implements a symplectic (leapfrog) integrator with adaptive time-stepping
and regularisation for close encounters. Classifies scattering outcomes
(which body escapes, binary energy, etc.) and records the full sequence of
intermediate "binary configurations" visited during resonant encounters.

This intermediate-state sequence is the raw data that the compartmental
PK model will be fitted to.

References
----------
Ginat & Perets, Nature 593 395 (2021)
Hut & Bahcall, ApJ 268 319 (1983)
Stone & Leigh, Nature 576 406 (2019)
"""

from __future__ import annotations

import dataclasses
import itertools
from typing import Literal

import numpy as np
from numpy.typing import NDArray


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ThreeBodyState:
    """Instantaneous state of a three-body system (3D)."""
    masses: NDArray       # (3,)
    positions: NDArray    # (3, 3)  — x, y, z for each body
    velocities: NDArray   # (3, 3)

    def total_energy(self) -> float:
        ke = 0.5 * np.sum(self.masses[:, None] * self.velocities ** 2)
        pe = 0.0
        for i, j in itertools.combinations(range(3), 2):
            rij = np.linalg.norm(self.positions[i] - self.positions[j])
            pe -= self.masses[i] * self.masses[j] / rij
        return float(ke + pe)

    def angular_momentum(self) -> NDArray:
        L = np.zeros(3)
        for i in range(3):
            L += self.masses[i] * np.cross(self.positions[i], self.velocities[i])
        return L

    def centre_of_mass(self) -> NDArray:
        return np.sum(self.masses[:, None] * self.positions, axis=0) / np.sum(self.masses)

    def to_com_frame(self) -> "ThreeBodyState":
        """Return a copy in the centre-of-mass rest frame."""
        M = np.sum(self.masses)
        r_com = self.centre_of_mass()
        v_com = np.sum(self.masses[:, None] * self.velocities, axis=0) / M
        return ThreeBodyState(
            masses=self.masses.copy(),
            positions=self.positions - r_com,
            velocities=self.velocities - v_com,
        )


@dataclasses.dataclass
class BinaryConfig:
    """A snapshot of the system when one body is temporarily far away."""
    binary_pair: tuple[int, int]   # indices of the two bound bodies
    single_idx: int                # index of the distant body
    binary_energy: float           # specific binding energy of the binary (<0 if bound)
    binary_sma: float              # semi-major axis (>0 if bound)
    r_single: float                # distance of single body from binary COM
    t: float                       # simulation time


@dataclasses.dataclass
class ScatteringOutcome:
    """Final result of a three-body scattering event."""
    status: Literal["escape", "collision", "timeout"]
    escaper_idx: int | None        # which body escaped (0, 1, 2)
    binary_pair: tuple[int, int] | None
    binary_energy: float | None
    binary_sma: float | None
    escape_velocity: float | None
    n_excursions: int              # number of intermediate excursions
    config_sequence: list[BinaryConfig]  # full sequence of visited configs
    lifetime: float                # total duration of the resonant interaction
    initial_energy: float
    final_energy: float


# ---------------------------------------------------------------------------
# Integrator
# ---------------------------------------------------------------------------

def _accelerations(masses: NDArray, positions: NDArray,
                   softening: float = 0.0) -> NDArray:
    """Gravitational accelerations for 3 bodies."""
    acc = np.zeros_like(positions)
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            rij = positions[j] - positions[i]
            r = np.sqrt(np.dot(rij, rij) + softening ** 2)
            acc[i] += masses[j] * rij / r ** 3
    return acc


def _closest_pair(positions: NDArray) -> tuple[int, int, float]:
    """Return the indices and distance of the closest pair."""
    dmin = np.inf
    pair = (0, 1)
    for i, j in itertools.combinations(range(3), 2):
        d = np.linalg.norm(positions[i] - positions[j])
        if d < dmin:
            dmin = d
            pair = (i, j)
    return pair[0], pair[1], dmin


def _identify_config(state: ThreeBodyState, t: float) -> BinaryConfig | None:
    """
    Try to identify a binary+single configuration.

    Criterion: the closest pair has negative relative energy (bound),
    and the third body is at least 3× the binary separation away from
    the binary centre of mass.
    """
    i, j, d_bin = _closest_pair(state.positions)
    k = 3 - i - j  # the other body

    # Relative energy of the (i,j) pair
    mu_ij = state.masses[i] * state.masses[j] / (state.masses[i] + state.masses[j])
    v_rel = state.velocities[i] - state.velocities[j]
    ke_rel = 0.5 * mu_ij * np.dot(v_rel, v_rel)
    pe_rel = -state.masses[i] * state.masses[j] / d_bin
    E_bin = ke_rel + pe_rel

    if E_bin >= 0:
        return None  # not bound

    sma = -state.masses[i] * state.masses[j] / (2 * E_bin)

    # Distance of single body from binary COM
    m_bin = state.masses[i] + state.masses[j]
    r_com_bin = (state.masses[i] * state.positions[i]
                 + state.masses[j] * state.positions[j]) / m_bin
    r_single = np.linalg.norm(state.positions[k] - r_com_bin)

    if r_single < 3.0 * d_bin:
        return None  # still in a three-body encounter

    return BinaryConfig(
        binary_pair=(min(i, j), max(i, j)),
        single_idx=k,
        binary_energy=float(E_bin),
        binary_sma=float(sma),
        r_single=float(r_single),
        t=t,
    )


def _check_escape(state: ThreeBodyState, escape_radius: float) -> int | None:
    """Check if any body has escaped (unbound + far away)."""
    com = state.centre_of_mass()
    M = np.sum(state.masses)
    v_com = np.sum(state.masses[:, None] * state.velocities, axis=0) / M

    for k in range(3):
        r_k = np.linalg.norm(state.positions[k] - com)
        if r_k < escape_radius:
            continue
        # Check if body k is unbound from the other two
        i, j = [x for x in range(3) if x != k]
        m_bin = state.masses[i] + state.masses[j]
        r_com_bin = (state.masses[i] * state.positions[i]
                     + state.masses[j] * state.positions[j]) / m_bin
        v_com_bin = (state.masses[i] * state.velocities[i]
                     + state.masses[j] * state.velocities[j]) / m_bin

        r_rel = state.positions[k] - r_com_bin
        v_rel = state.velocities[k] - v_com_bin
        mu = state.masses[k] * m_bin / (state.masses[k] + m_bin)

        E_rel = 0.5 * mu * np.dot(v_rel, v_rel) - state.masses[k] * m_bin / np.linalg.norm(r_rel)
        if E_rel > 0:
            return k
    return None


def simulate_scattering(
    state: ThreeBodyState,
    *,
    dt_initial: float = 1e-3,
    t_max: float = 1e5,
    escape_radius: float = 100.0,
    collision_radius: float = 1e-4,
    softening: float = 0.0,
    eta: float = 0.02,
) -> ScatteringOutcome:
    """
    Run one three-body scattering simulation.

    Uses leapfrog integration with adaptive time-stepping based on the
    minimum pairwise distance (Aarseth criterion).

    Parameters
    ----------
    state : ThreeBodyState
        Initial conditions (will be converted to COM frame).
    dt_initial : float
        Starting time step.
    t_max : float
        Maximum integration time before declaring timeout.
    escape_radius : float
        Distance from COM beyond which escape is checked.
    collision_radius : float
        Minimum pairwise distance to declare a collision.
    softening : float
        Gravitational softening length.
    eta : float
        Time-step accuracy parameter (Aarseth).

    Returns
    -------
    ScatteringOutcome
    """
    s = state.to_com_frame()
    masses = s.masses
    pos = s.positions.copy()
    vel = s.velocities.copy()

    E0 = s.total_energy()
    t = 0.0
    dt = dt_initial

    config_sequence: list[BinaryConfig] = []
    prev_config: BinaryConfig | None = None

    # Leapfrog kick-drift-kick
    acc = _accelerations(masses, pos, softening)

    while t < t_max:
        # Adaptive time step (Aarseth)
        _, _, d_min = _closest_pair(pos)
        if d_min < collision_radius:
            # Collision
            s_now = ThreeBodyState(masses, pos.copy(), vel.copy())
            return ScatteringOutcome(
                status="collision",
                escaper_idx=None,
                binary_pair=None,
                binary_energy=None,
                binary_sma=None,
                escape_velocity=None,
                n_excursions=len(config_sequence),
                config_sequence=config_sequence,
                lifetime=t,
                initial_energy=E0,
                final_energy=s_now.total_energy(),
            )

        dt = min(eta * np.sqrt(d_min / (np.max(np.linalg.norm(acc, axis=1)) + 1e-30)),
                 dt_initial * 10)
        dt = max(dt, 1e-8)

        # Kick (half)
        vel += 0.5 * dt * acc
        # Drift
        pos += dt * vel
        # New acceleration
        acc = _accelerations(masses, pos, softening)
        # Kick (half)
        vel += 0.5 * dt * acc

        t += dt

        # Identify current binary configuration
        s_now = ThreeBodyState(masses, pos.copy(), vel.copy())
        cfg = _identify_config(s_now, t)
        if cfg is not None:
            if (prev_config is None
                    or cfg.binary_pair != prev_config.binary_pair):
                config_sequence.append(cfg)
                prev_config = cfg

        # Check escape
        esc = _check_escape(s_now, escape_radius)
        if esc is not None:
            i, j = [x for x in range(3) if x != esc]
            # Final binary properties
            d_bin = np.linalg.norm(pos[i] - pos[j])
            mu_ij = masses[i] * masses[j] / (masses[i] + masses[j])
            v_rel = vel[i] - vel[j]
            E_bin = 0.5 * mu_ij * np.dot(v_rel, v_rel) - masses[i] * masses[j] / d_bin
            sma = -masses[i] * masses[j] / (2 * E_bin) if E_bin < 0 else float('inf')

            # Escape velocity
            M = np.sum(masses)
            com = np.sum(masses[:, None] * pos, axis=0) / M
            v_com = np.sum(masses[:, None] * vel, axis=0) / M
            v_esc = np.linalg.norm(vel[esc] - v_com)

            return ScatteringOutcome(
                status="escape",
                escaper_idx=esc,
                binary_pair=(min(i, j), max(i, j)),
                binary_energy=float(E_bin),
                binary_sma=float(sma),
                escape_velocity=float(v_esc),
                n_excursions=len(config_sequence),
                config_sequence=config_sequence,
                lifetime=t,
                initial_energy=E0,
                final_energy=s_now.total_energy(),
            )

    # Timeout
    s_now = ThreeBodyState(masses, pos.copy(), vel.copy())
    return ScatteringOutcome(
        status="timeout",
        escaper_idx=None,
        binary_pair=None,
        binary_energy=None,
        binary_sma=None,
        escape_velocity=None,
        n_excursions=len(config_sequence),
        config_sequence=config_sequence,
        lifetime=t,
        initial_energy=E0,
        final_energy=s_now.total_energy(),
    )


# ---------------------------------------------------------------------------
# Initial condition generators
# ---------------------------------------------------------------------------

def generate_binary_single_ic(
    m1: float = 1.0,
    m2: float = 1.0,
    m3: float = 1.0,
    sma_binary: float = 1.0,
    ecc_binary: float = 0.0,
    v_inf: float = 0.5,
    b_max: float = 5.0,
    rng: np.random.Generator | None = None,
) -> ThreeBodyState:
    """
    Generate initial conditions for a binary-single scattering encounter.

    Bodies 0 and 1 form the initial binary; body 2 is the incoming single star.

    Parameters
    ----------
    m1, m2 : float
        Masses of the binary components.
    m3 : float
        Mass of the incoming single star.
    sma_binary : float
        Semi-major axis of the initial binary.
    ecc_binary : float
        Eccentricity of the initial binary.
    v_inf : float
        Velocity at infinity of the incoming star.
    b_max : float
        Maximum impact parameter (uniform sampling in b²).
    rng : Generator, optional
        Random number generator.
    """
    if rng is None:
        rng = np.random.default_rng()

    # Binary at periapsis, in x-y plane
    r_peri = sma_binary * (1 - ecc_binary)
    v_peri = np.sqrt((m1 + m2) * (1 + ecc_binary) / r_peri)

    # Place binary COM at origin
    pos = np.zeros((3, 3))
    vel = np.zeros((3, 3))

    pos[0] = np.array([r_peri * m2 / (m1 + m2), 0.0, 0.0])
    pos[1] = np.array([-r_peri * m1 / (m1 + m2), 0.0, 0.0])
    vel[0] = np.array([0.0, v_peri * m2 / (m1 + m2), 0.0])
    vel[1] = np.array([0.0, -v_peri * m1 / (m1 + m2), 0.0])

    # Incoming star: random impact parameter, random phase
    b = np.sqrt(rng.uniform(0, b_max ** 2))          # uniform in b²
    phi = rng.uniform(0, 2 * np.pi)                   # azimuthal angle
    theta = np.arccos(rng.uniform(-1, 1))              # inclination (3D)

    # Start far away
    d_start = 50.0 * sma_binary

    # Velocity direction towards the binary COM
    pos[2] = np.array([
        d_start,
        b * np.cos(phi),
        b * np.sin(phi),
    ])

    # Rotate by random inclination
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    rot = np.array([
        [cos_t, 0, sin_t],
        [0, 1, 0],
        [-sin_t, 0, cos_t],
    ])
    pos[2] = rot @ pos[2]

    vel[2] = -v_inf * pos[2] / np.linalg.norm(pos[2])

    return ThreeBodyState(
        masses=np.array([m1, m2, m3]),
        positions=pos,
        velocities=vel,
    )


def generate_democratic_ic(
    m1: float = 1.0,
    m2: float = 1.0,
    m3: float = 1.0,
    E_total: float = -0.5,
    L_total: float = 0.0,
    rng: np.random.Generator | None = None,
) -> ThreeBodyState:
    """
    Generate 'democratic' initial conditions where no clear hierarchy exists.

    Places three bodies at the vertices of a triangle with random perturbations
    and assigns velocities consistent with the desired total energy.
    """
    if rng is None:
        rng = np.random.default_rng()

    masses = np.array([m1, m2, m3])

    # Equilateral triangle with random perturbation
    angles = np.array([0, 2 * np.pi / 3, 4 * np.pi / 3]) + rng.uniform(-0.3, 0.3, 3)
    r_scale = 1.0 + rng.uniform(-0.3, 0.3, 3)

    pos = np.zeros((3, 3))
    for i in range(3):
        pos[i, 0] = r_scale[i] * np.cos(angles[i])
        pos[i, 1] = r_scale[i] * np.sin(angles[i])
        pos[i, 2] = rng.uniform(-0.1, 0.1)

    # Centre on COM
    com = np.sum(masses[:, None] * pos, axis=0) / np.sum(masses)
    pos -= com

    # Potential energy
    pe = 0.0
    for i, j in itertools.combinations(range(3), 2):
        pe -= masses[i] * masses[j] / np.linalg.norm(pos[i] - pos[j])

    # Assign random velocities, then rescale to get desired energy
    vel = rng.standard_normal((3, 3)) * 0.1
    # Remove COM velocity
    v_com = np.sum(masses[:, None] * vel, axis=0) / np.sum(masses)
    vel -= v_com

    ke = 0.5 * np.sum(masses[:, None] * vel ** 2)
    desired_ke = E_total - pe
    if desired_ke <= 0:
        # Reduce kinetic energy to near zero and let gravity do the work
        vel *= 0.01
    else:
        vel *= np.sqrt(desired_ke / ke) if ke > 0 else 0.0

    return ThreeBodyState(masses=masses, positions=pos, velocities=vel)


# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------

def run_scattering_ensemble(
    n_runs: int,
    *,
    masses: tuple[float, float, float] = (1.0, 1.0, 1.0),
    mode: Literal["binary_single", "democratic"] = "binary_single",
    seed: int = 42,
    **kwargs,
) -> list[ScatteringOutcome]:
    """Run an ensemble of scattering experiments."""
    rng = np.random.default_rng(seed)
    results = []

    for i in range(n_runs):
        if mode == "binary_single":
            ic = generate_binary_single_ic(*masses, rng=rng, **kwargs)
        else:
            ic = generate_democratic_ic(*masses, rng=rng, **kwargs)

        outcome = simulate_scattering(ic)
        results.append(outcome)

        if (i + 1) % max(1, n_runs // 10) == 0:
            print(f"  [{i + 1}/{n_runs}] completed — "
                  f"escapes: {sum(1 for r in results if r.status == 'escape')}, "
                  f"timeouts: {sum(1 for r in results if r.status == 'timeout')}")

    return results


if __name__ == "__main__":
    print("Running test ensemble (100 binary-single scatterings, equal mass)...")
    results = run_scattering_ensemble(100, mode="binary_single", seed=123)

    n_esc = sum(1 for r in results if r.status == "escape")
    n_col = sum(1 for r in results if r.status == "collision")
    n_to = sum(1 for r in results if r.status == "timeout")
    print(f"\nResults: {n_esc} escapes, {n_col} collisions, {n_to} timeouts")

    lifetimes = [r.lifetime for r in results if r.status == "escape"]
    if lifetimes:
        print(f"Escape lifetime: median={np.median(lifetimes):.2f}, "
              f"mean={np.mean(lifetimes):.2f}, max={np.max(lifetimes):.2f}")

    excursions = [r.n_excursions for r in results if r.status == "escape"]
    if excursions:
        print(f"Excursions: median={np.median(excursions):.0f}, "
              f"mean={np.mean(excursions):.1f}, max={np.max(excursions)}")

    # Check energy conservation
    dE = [abs((r.final_energy - r.initial_energy) / r.initial_energy)
          for r in results if r.status == "escape"]
    if dE:
        print(f"Energy conservation: max |dE/E| = {max(dE):.2e}")
