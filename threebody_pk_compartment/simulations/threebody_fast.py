"""
Numba-accelerated three-body scattering core for the MNRAS extensions.

Reproduces the physics of ``threebody_scattering.py`` (Newtonian leapfrog
with Aarseth adaptive time-stepping, binary/single configuration tracking,
escape/collision classification) and adds:

  * pairwise 1PN acceleration  -> periastron precession        (mode PN1)
  * phenomenological tidal drag -> stellar-triple dissipation  (mode TIDAL)
  * final-binary eccentricity and ejection velocity per event  (A-4)

All heavy loops are JIT-compiled with numba so that thousands of events with
t_max ~ 1e5 dynamical times run in minutes rather than days.

Compartment convention (0-indexed pairs): (0,1)->0, (0,2)->1, (1,2)->2,
matching PAIR_TO_COMP = {(1,2):0,(1,3):1,(2,3):2} used in the analysis code.

modes: 0 = Newtonian, 1 = +1PN, 2 = +tidal, 3 = +1PN+tidal
"""

from __future__ import annotations

import numpy as np
from numba import njit

MAX_CFG = 4000  # max recorded configuration changes per event


@njit(cache=True, fastmath=True)
def _pair_comp(i, j):
    a = i if i < j else j
    b = j if i < j else i
    if a == 0 and b == 1:
        return 0
    if a == 0 and b == 2:
        return 1
    return 2  # (1,2)


@njit(cache=True, fastmath=True)
def _accel(masses, pos, vel, softening, mode, c2, k_tidal, r_tidal):
    acc = np.zeros((3, 3))
    # Newtonian
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            dx = pos[j, 0] - pos[i, 0]
            dy = pos[j, 1] - pos[i, 1]
            dz = pos[j, 2] - pos[i, 2]
            r2 = dx * dx + dy * dy + dz * dz + softening * softening
            r = np.sqrt(r2)
            inv = masses[j] / (r * r * r)
            acc[i, 0] += inv * dx
            acc[i, 1] += inv * dy
            acc[i, 2] += inv * dz
    # velocity-dependent pairwise terms
    if mode == 1 or mode == 3 or mode == 2:
        for i in range(3):
            for j in range(i + 1, 3):
                dx = pos[j, 0] - pos[i, 0]
                dy = pos[j, 1] - pos[i, 1]
                dz = pos[j, 2] - pos[i, 2]
                r = np.sqrt(dx * dx + dy * dy + dz * dz)
                if r <= 0.0:
                    continue
                nx = dx / r
                ny = dy / r
                nz = dz / r
                vx = vel[j, 0] - vel[i, 0]
                vy = vel[j, 1] - vel[i, 1]
                vz = vel[j, 2] - vel[i, 2]
                M = masses[i] + masses[j]
                if mode == 1 or mode == 3:
                    eta = masses[i] * masses[j] / (M * M)
                    v2 = vx * vx + vy * vy + vz * vz
                    rdot = nx * vx + ny * vy + nz * vz
                    coef = (M / (r * r)) / c2
                    fn = (2.0 * (2.0 + eta) * M / r
                          - (1.0 + 3.0 * eta) * v2
                          + 1.5 * eta * rdot * rdot)
                    fv = 2.0 * (2.0 - eta) * rdot
                    arx = coef * (fn * nx + fv * vx)
                    ary = coef * (fn * ny + fv * vy)
                    arz = coef * (fn * nz + fv * vz)
                    acc[j, 0] += (masses[i] / M) * arx
                    acc[j, 1] += (masses[i] / M) * ary
                    acc[j, 2] += (masses[i] / M) * arz
                    acc[i, 0] -= (masses[j] / M) * arx
                    acc[i, 1] -= (masses[j] / M) * ary
                    acc[i, 2] -= (masses[j] / M) * arz
                if (mode == 2 or mode == 3) and r < r_tidal:
                    fac = -k_tidal * (r_tidal / r) ** 5
                    arx = fac * vx
                    ary = fac * vy
                    arz = fac * vz
                    acc[j, 0] += (masses[i] / M) * arx
                    acc[j, 1] += (masses[i] / M) * ary
                    acc[j, 2] += (masses[i] / M) * arz
                    acc[i, 0] -= (masses[j] / M) * arx
                    acc[i, 1] -= (masses[j] / M) * ary
                    acc[i, 2] -= (masses[j] / M) * arz
    return acc


@njit(cache=True, fastmath=True)
def _total_energy(masses, pos, vel):
    ke = 0.0
    for i in range(3):
        ke += 0.5 * masses[i] * (vel[i, 0] ** 2 + vel[i, 1] ** 2 + vel[i, 2] ** 2)
    pe = 0.0
    for i in range(3):
        for j in range(i + 1, 3):
            dx = pos[j, 0] - pos[i, 0]
            dy = pos[j, 1] - pos[i, 1]
            dz = pos[j, 2] - pos[i, 2]
            pe -= masses[i] * masses[j] / np.sqrt(dx * dx + dy * dy + dz * dz)
    return ke + pe


@njit(cache=True, fastmath=True)
def _closest(pos):
    dmin = 1e30
    ci = 0
    cj = 1
    for i in range(3):
        for j in range(i + 1, 3):
            dx = pos[j, 0] - pos[i, 0]
            dy = pos[j, 1] - pos[i, 1]
            dz = pos[j, 2] - pos[i, 2]
            d = np.sqrt(dx * dx + dy * dy + dz * dz)
            if d < dmin:
                dmin = d
                ci = i
                cj = j
    return ci, cj, dmin


@njit(cache=True, fastmath=True)
def _identify_comp(masses, pos, vel):
    """Return compartment index (0/1/2) or -1 if no clear binary+single."""
    i, j, d_bin = _closest(pos)
    k = 3 - i - j
    mu = masses[i] * masses[j] / (masses[i] + masses[j])
    vx = vel[i, 0] - vel[j, 0]
    vy = vel[i, 1] - vel[j, 1]
    vz = vel[i, 2] - vel[j, 2]
    ke = 0.5 * mu * (vx * vx + vy * vy + vz * vz)
    pe = -masses[i] * masses[j] / d_bin
    E_bin = ke + pe
    if E_bin >= 0.0:
        return -1
    mb = masses[i] + masses[j]
    cx = (masses[i] * pos[i, 0] + masses[j] * pos[j, 0]) / mb
    cy = (masses[i] * pos[i, 1] + masses[j] * pos[j, 1]) / mb
    cz = (masses[i] * pos[i, 2] + masses[j] * pos[j, 2]) / mb
    rs = np.sqrt((pos[k, 0] - cx) ** 2 + (pos[k, 1] - cy) ** 2 + (pos[k, 2] - cz) ** 2)
    if rs < 3.0 * d_bin:
        return -1
    return _pair_comp(i, j)


@njit(cache=True, fastmath=True)
def _check_escape(masses, pos, vel, escape_radius):
    M = masses[0] + masses[1] + masses[2]
    cx = (masses[0] * pos[0, 0] + masses[1] * pos[1, 0] + masses[2] * pos[2, 0]) / M
    cy = (masses[0] * pos[0, 1] + masses[1] * pos[1, 1] + masses[2] * pos[2, 1]) / M
    cz = (masses[0] * pos[0, 2] + masses[1] * pos[1, 2] + masses[2] * pos[2, 2]) / M
    for k in range(3):
        rk = np.sqrt((pos[k, 0] - cx) ** 2 + (pos[k, 1] - cy) ** 2 + (pos[k, 2] - cz) ** 2)
        if rk < escape_radius:
            continue
        i = -1
        j = -1
        for m in range(3):
            if m != k:
                if i < 0:
                    i = m
                else:
                    j = m
        mb = masses[i] + masses[j]
        bx = (masses[i] * pos[i, 0] + masses[j] * pos[j, 0]) / mb
        by = (masses[i] * pos[i, 1] + masses[j] * pos[j, 1]) / mb
        bz = (masses[i] * pos[i, 2] + masses[j] * pos[j, 2]) / mb
        bvx = (masses[i] * vel[i, 0] + masses[j] * vel[j, 0]) / mb
        bvy = (masses[i] * vel[i, 1] + masses[j] * vel[j, 1]) / mb
        bvz = (masses[i] * vel[i, 2] + masses[j] * vel[j, 2]) / mb
        rrx = pos[k, 0] - bx
        rry = pos[k, 1] - by
        rrz = pos[k, 2] - bz
        vrx = vel[k, 0] - bvx
        vry = vel[k, 1] - bvy
        vrz = vel[k, 2] - bvz
        mu = masses[k] * mb / (masses[k] + mb)
        rr = np.sqrt(rrx * rrx + rry * rry + rrz * rrz)
        Erel = 0.5 * mu * (vrx * vrx + vry * vry + vrz * vrz) - masses[k] * mb / rr
        if Erel > 0.0:
            return k
    return -1


@njit(cache=True, fastmath=True)
def _elements(masses, pos, vel, i, j):
    mb = masses[i] + masses[j]
    mu = masses[i] * masses[j] / mb
    rx = pos[i, 0] - pos[j, 0]
    ry = pos[i, 1] - pos[j, 1]
    rz = pos[i, 2] - pos[j, 2]
    vx = vel[i, 0] - vel[j, 0]
    vy = vel[i, 1] - vel[j, 1]
    vz = vel[i, 2] - vel[j, 2]
    r = np.sqrt(rx * rx + ry * ry + rz * rz)
    v2 = vx * vx + vy * vy + vz * vz
    eps = 0.5 * v2 - mb / r
    hx = ry * vz - rz * vy
    hy = rz * vx - rx * vz
    hz = rx * vy - ry * vx
    h2 = hx * hx + hy * hy + hz * hz
    if eps >= 0.0:
        return 1e30, np.nan, mu * eps
    sma = -mb / (2.0 * eps)
    e2 = 1.0 + 2.0 * eps * h2 / (mb * mb)
    if e2 < 0.0:
        e2 = 0.0
    return sma, np.sqrt(e2), mu * eps


@njit(cache=True, fastmath=True)
def simulate(masses, pos0, vel0, mode, c_light, k_tidal, r_tidal,
             dt_initial, t_max, escape_radius, collision_radius,
             softening, eta):
    """Run one event. Returns a results tuple + config arrays."""
    pos = pos0.copy()
    vel = vel0.copy()
    c2 = c_light * c_light
    E0 = _total_energy(masses, pos, vel)
    t = 0.0

    comp_seq = np.full(MAX_CFG, -1, dtype=np.int64)
    t_seq = np.zeros(MAX_CFG)
    ncfg = 0
    prev_comp = -1

    acc = _accel(masses, pos, vel, softening, mode, c2, k_tidal, r_tidal)

    status = 2  # timeout
    nstep = 0
    max_steps = 20_000_000
    escaper = -1
    bpi = -1
    bpj = -1
    sma = 1e30
    ecc = np.nan
    E_bin = 0.0
    v_esc = np.nan

    while t < t_max:
        nstep += 1
        if nstep > max_steps:
            # dissipatively hardened / captured binary: treat as merger
            status = 1
            break
        _, _, d_min = _closest(pos)
        if d_min < collision_radius:
            status = 1
            break
        amax = 0.0
        for a in range(3):
            an = np.sqrt(acc[a, 0] ** 2 + acc[a, 1] ** 2 + acc[a, 2] ** 2)
            if an > amax:
                amax = an
        dt = eta * np.sqrt(d_min / (amax + 1e-30))
        if dt > dt_initial * 10.0:
            dt = dt_initial * 10.0
        if dt < 1e-8:
            dt = 1e-8

        vel_half = vel + 0.5 * dt * acc
        pos = pos + dt * vel_half
        acc_new = _accel(masses, pos, vel_half, softening, mode, c2, k_tidal, r_tidal)
        vel = vel_half + 0.5 * dt * acc_new
        acc = _accel(masses, pos, vel, softening, mode, c2, k_tidal, r_tidal)
        t += dt

        comp = _identify_comp(masses, pos, vel)
        if comp >= 0 and comp != prev_comp:
            if ncfg < MAX_CFG:
                comp_seq[ncfg] = comp
                t_seq[ncfg] = t
                ncfg += 1
            prev_comp = comp

        esc = _check_escape(masses, pos, vel, escape_radius)
        if esc >= 0:
            status = 0
            escaper = esc
            i = -1
            j = -1
            for m in range(3):
                if m != esc:
                    if i < 0:
                        i = m
                    else:
                        j = m
            bpi = i
            bpj = j
            sma, ecc, E_bin = _elements(masses, pos, vel, i, j)
            M = masses[0] + masses[1] + masses[2]
            vcx = (masses[0] * vel[0, 0] + masses[1] * vel[1, 0] + masses[2] * vel[2, 0]) / M
            vcy = (masses[0] * vel[0, 1] + masses[1] * vel[1, 1] + masses[2] * vel[2, 1]) / M
            vcz = (masses[0] * vel[0, 2] + masses[1] * vel[1, 2] + masses[2] * vel[2, 2]) / M
            v_esc = np.sqrt((vel[esc, 0] - vcx) ** 2 + (vel[esc, 1] - vcy) ** 2
                            + (vel[esc, 2] - vcz) ** 2)
            break

    Ef = _total_energy(masses, pos, vel)
    return (status, escaper, bpi, bpj, sma, ecc, E_bin, v_esc, t, E0, Ef,
            ncfg, comp_seq, t_seq)
