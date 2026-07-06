"""
Three-body scattering: fully 3D + Post-Newtonian radiation reaction.

Extension with:
1. Fully randomized orbital plane (not restricted to x-y plane)
2. Eccentric initial binaries (thermal distribution f(e) = 2e)
3. 2.5PN gravitational-wave radiation reaction (energy dissipation)

Usage:
  julia threebody_3d_dissipative.jl [n_runs] [c_value]
  c_value: speed of light in code units (default: 100; smaller = stronger dissipation)
"""

using StaticArrays
using LinearAlgebra
using Random
using JSON
using Printf
using Statistics: median, mean

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

struct BinaryConfig3D
    pair::Tuple{Int,Int}
    single::Int
    E_bin::Float64
    sma::Float64
    r_single::Float64
    t::Float64
end

struct ScatteringOutcome3D
    status::Symbol
    escaper::Int
    binary_pair::Tuple{Int,Int}
    E_bin::Float64
    sma::Float64
    v_esc::Float64
    n_excursions::Int
    config_sequence::Vector{BinaryConfig3D}
    lifetime::Float64
    E_initial::Float64
    E_final::Float64
end

# ---------------------------------------------------------------------------
# Core physics
# ---------------------------------------------------------------------------

@inline function accelerations_3d(m::SVector{3,Float64}, r::SMatrix{3,3,Float64,9})
    a = @MMatrix zeros(3, 3)
    @inbounds for i in 1:3
        for j in 1:3
            i == j && continue
            dx = r[1,j] - r[1,i]
            dy = r[2,j] - r[2,i]
            dz = r[3,j] - r[3,i]
            r2 = dx*dx + dy*dy + dz*dz
            rinv3 = 1.0 / (r2 * sqrt(r2))
            a[1,i] += m[j] * dx * rinv3
            a[2,i] += m[j] * dy * rinv3
            a[3,i] += m[j] * dz * rinv3
        end
    end
    return SMatrix{3,3}(a)
end

@inline function closest_pair_dist_3d(r::SMatrix{3,3,Float64,9})
    d01 = @inbounds sqrt((r[1,1]-r[1,2])^2 + (r[2,1]-r[2,2])^2 + (r[3,1]-r[3,2])^2)
    d02 = @inbounds sqrt((r[1,1]-r[1,3])^2 + (r[2,1]-r[2,3])^2 + (r[3,1]-r[3,3])^2)
    d12 = @inbounds sqrt((r[1,2]-r[1,3])^2 + (r[2,2]-r[2,3])^2 + (r[3,2]-r[3,3])^2)
    dmin = min(d01, d02, d12)
    if dmin == d01
        return (1, 2, dmin)
    elseif dmin == d02
        return (1, 3, dmin)
    else
        return (2, 3, dmin)
    end
end

function total_energy_3d(m::SVector{3,Float64}, r::SMatrix{3,3,Float64,9},
                          v::SMatrix{3,3,Float64,9})
    ke = 0.0
    @inbounds for i in 1:3
        ke += 0.5 * m[i] * (v[1,i]^2 + v[2,i]^2 + v[3,i]^2)
    end
    pe = 0.0
    @inbounds for i in 1:3
        for j in (i+1):3
            dx = r[1,i]-r[1,j]; dy = r[2,i]-r[2,j]; dz = r[3,i]-r[3,j]
            pe -= m[i]*m[j] / sqrt(dx^2 + dy^2 + dz^2)
        end
    end
    return ke + pe
end

function identify_config_3d(m::SVector{3,Float64}, r::SMatrix{3,3,Float64,9},
                             v::SMatrix{3,3,Float64,9}, t::Float64)
    i, j, d_bin = closest_pair_dist_3d(r)
    k = 6 - i - j
    mu_ij = m[i]*m[j] / (m[i]+m[j])
    @inbounds vrel = SVector(v[1,i]-v[1,j], v[2,i]-v[2,j], v[3,i]-v[3,j])
    ke_rel = 0.5 * mu_ij * dot(vrel, vrel)
    pe_rel = -m[i]*m[j] / d_bin
    E_bin = ke_rel + pe_rel
    E_bin >= 0 && return nothing
    sma = -m[i]*m[j] / (2*E_bin)
    m_bin = m[i] + m[j]
    @inbounds rcom_bin = SVector(
        (m[i]*r[1,i] + m[j]*r[1,j]) / m_bin,
        (m[i]*r[2,i] + m[j]*r[2,j]) / m_bin,
        (m[i]*r[3,i] + m[j]*r[3,j]) / m_bin,
    )
    @inbounds dr = SVector(r[1,k]-rcom_bin[1], r[2,k]-rcom_bin[2], r[3,k]-rcom_bin[3])
    r_single = norm(dr)
    r_single < 3.0 * d_bin && return nothing
    return BinaryConfig3D((min(i,j), max(i,j)), k, E_bin, sma, r_single, t)
end

function check_escape_3d(m::SVector{3,Float64}, r::SMatrix{3,3,Float64,9},
                          v::SMatrix{3,3,Float64,9}, escape_radius::Float64)
    M = sum(m)
    @inbounds com = SVector(
        (m[1]*r[1,1]+m[2]*r[1,2]+m[3]*r[1,3])/M,
        (m[1]*r[2,1]+m[2]*r[2,2]+m[3]*r[2,3])/M,
        (m[1]*r[3,1]+m[2]*r[3,2]+m[3]*r[3,3])/M,
    )
    for k in 1:3
        @inbounds rk = SVector(r[1,k]-com[1], r[2,k]-com[2], r[3,k]-com[3])
        norm(rk) < escape_radius && continue
        others = filter(x -> x != k, 1:3)
        i, j = others[1], others[2]
        m_bin = m[i] + m[j]
        @inbounds rcom_bin = SVector(
            (m[i]*r[1,i]+m[j]*r[1,j])/m_bin,
            (m[i]*r[2,i]+m[j]*r[2,j])/m_bin,
            (m[i]*r[3,i]+m[j]*r[3,j])/m_bin,
        )
        @inbounds vcom_bin = SVector(
            (m[i]*v[1,i]+m[j]*v[1,j])/m_bin,
            (m[i]*v[2,i]+m[j]*v[2,j])/m_bin,
            (m[i]*v[3,i]+m[j]*v[3,j])/m_bin,
        )
        @inbounds dr = SVector(r[1,k]-rcom_bin[1], r[2,k]-rcom_bin[2], r[3,k]-rcom_bin[3])
        @inbounds dv = SVector(v[1,k]-vcom_bin[1], v[2,k]-vcom_bin[2], v[3,k]-vcom_bin[3])
        mu = m[k]*m_bin / (m[k]+m_bin)
        E_rel = 0.5*mu*dot(dv,dv) - m[k]*m_bin/norm(dr)
        E_rel > 0 && return k
    end
    return 0
end

# ---------------------------------------------------------------------------
# 2.5PN radiation reaction acceleration
# ---------------------------------------------------------------------------

@inline function pn25_acceleration(m::SVector{3,Float64},
                                     r::SMatrix{3,3,Float64,9},
                                     v::SMatrix{3,3,Float64,9},
                                     c::Float64)
    c5inv = 1.0 / (c * c * c * c * c)
    a = @MMatrix zeros(3, 3)

    @inbounds for i in 1:3
        for j in (i+1):3
            dx = r[1,j] - r[1,i]
            dy = r[2,j] - r[2,i]
            dz = r[3,j] - r[3,i]
            rr = sqrt(dx*dx + dy*dy + dz*dz)
            rr < 1e-10 && continue

            rinv = 1.0 / rr
            nx, ny, nz = dx*rinv, dy*rinv, dz*rinv

            dvx = v[1,j] - v[1,i]
            dvy = v[2,j] - v[2,i]
            dvz = v[3,j] - v[3,i]

            v2 = dvx*dvx + dvy*dvy + dvz*dvz
            vr = dvx*nx + dvy*ny + dvz*nz

            Mij = m[i] + m[j]
            mu = m[i] * m[j] / Mij

            coeff = (8.0/5.0) * mu * Mij * Mij * c5inv * rinv * rinv * rinv

            term1_coeff = coeff * (3.0*v2 + (17.0/3.0)*Mij*rinv) * vr
            term2_coeff = coeff * (v2 + 3.0*Mij*rinv)

            ax_rel = term1_coeff * nx - term2_coeff * dvx
            ay_rel = term1_coeff * ny - term2_coeff * dvy
            az_rel = term1_coeff * nz - term2_coeff * dvz

            fi = m[j] / Mij
            fj = m[i] / Mij

            a[1,i] += fi * ax_rel
            a[2,i] += fi * ay_rel
            a[3,i] += fi * az_rel
            a[1,j] -= fj * ax_rel
            a[2,j] -= fj * ay_rel
            a[3,j] -= fj * az_rel
        end
    end

    return SMatrix{3,3}(a)
end

# ---------------------------------------------------------------------------
# Integrators
# ---------------------------------------------------------------------------

function simulate_conservative(m::SVector{3,Float64},
                                r0::SMatrix{3,3,Float64,9},
                                v0::SMatrix{3,3,Float64,9};
                                dt_initial::Float64=1e-3,
                                t_max::Float64=1e5,
                                escape_radius::Float64=100.0,
                                collision_radius::Float64=1e-4,
                                eta::Float64=0.01)
    M = sum(m)
    com_r = SVector(
        (m[1]*r0[1,1]+m[2]*r0[1,2]+m[3]*r0[1,3])/M,
        (m[1]*r0[2,1]+m[2]*r0[2,2]+m[3]*r0[2,3])/M,
        (m[1]*r0[3,1]+m[2]*r0[3,2]+m[3]*r0[3,3])/M,
    )
    com_v = SVector(
        (m[1]*v0[1,1]+m[2]*v0[1,2]+m[3]*v0[1,3])/M,
        (m[1]*v0[2,1]+m[2]*v0[2,2]+m[3]*v0[2,3])/M,
        (m[1]*v0[3,1]+m[2]*v0[3,2]+m[3]*v0[3,3])/M,
    )

    r = MMatrix{3,3}(r0)
    vel = MMatrix{3,3}(v0)
    @inbounds for i in 1:3
        r[1,i] -= com_r[1]; r[2,i] -= com_r[2]; r[3,i] -= com_r[3]
        vel[1,i] -= com_v[1]; vel[2,i] -= com_v[2]; vel[3,i] -= com_v[3]
    end

    rs = SMatrix{3,3}(r)
    vs = SMatrix{3,3}(vel)
    E0 = total_energy_3d(m, rs, vs)

    config_seq = BinaryConfig3D[]
    prev_pair = (0, 0)
    t = 0.0
    dt = dt_initial
    acc = accelerations_3d(m, rs)
    check_interval = 0

    while t < t_max
        _, _, d_min = closest_pair_dist_3d(rs)

        if d_min < collision_radius
            return ScatteringOutcome3D(:collision, 0, (0,0), 0.0, 0.0, 0.0,
                                     length(config_seq), config_seq, t, E0,
                                     total_energy_3d(m, rs, vs))
        end

        max_acc = max(
            sqrt(acc[1,1]^2+acc[2,1]^2+acc[3,1]^2),
            sqrt(acc[1,2]^2+acc[2,2]^2+acc[3,2]^2),
            sqrt(acc[1,3]^2+acc[2,3]^2+acc[3,3]^2),
        )
        dt = min(eta * sqrt(d_min / (max_acc + 1e-30)), dt_initial * 10)
        dt = max(dt, 1e-8)

        # Leapfrog KDK
        vel_h = MMatrix{3,3}(vs)
        @inbounds for i in 1:3
            vel_h[1,i] = vs[1,i] + 0.5*dt*acc[1,i]
            vel_h[2,i] = vs[2,i] + 0.5*dt*acc[2,i]
            vel_h[3,i] = vs[3,i] + 0.5*dt*acc[3,i]
        end

        r_new = MMatrix{3,3}(rs)
        @inbounds for i in 1:3
            r_new[1,i] = rs[1,i] + dt*vel_h[1,i]
            r_new[2,i] = rs[2,i] + dt*vel_h[2,i]
            r_new[3,i] = rs[3,i] + dt*vel_h[3,i]
        end
        rs = SMatrix{3,3}(r_new)

        acc = accelerations_3d(m, rs)

        @inbounds for i in 1:3
            vel_h[1,i] += 0.5*dt*acc[1,i]
            vel_h[2,i] += 0.5*dt*acc[2,i]
            vel_h[3,i] += 0.5*dt*acc[3,i]
        end
        vs = SMatrix{3,3}(vel_h)

        t += dt
        check_interval += 1

        if check_interval >= 10
            check_interval = 0
            cfg = identify_config_3d(m, rs, vs, t)
            if cfg !== nothing && cfg.pair != prev_pair
                push!(config_seq, cfg)
                prev_pair = cfg.pair
            end
            esc = check_escape_3d(m, rs, vs, escape_radius)
            if esc > 0
                others = filter(x -> x != esc, 1:3)
                i, j = others[1], others[2]
                @inbounds d_bin = sqrt((rs[1,i]-rs[1,j])^2+(rs[2,i]-rs[2,j])^2+(rs[3,i]-rs[3,j])^2)
                mu_ij = m[i]*m[j]/(m[i]+m[j])
                @inbounds vrel = SVector(vs[1,i]-vs[1,j], vs[2,i]-vs[2,j], vs[3,i]-vs[3,j])
                E_bin = 0.5*mu_ij*dot(vrel,vrel) - m[i]*m[j]/d_bin
                sma_f = E_bin < 0 ? -m[i]*m[j]/(2*E_bin) : Inf
                @inbounds v_esc_vec = SVector(
                    vs[1,esc]-(m[1]*vs[1,1]+m[2]*vs[1,2]+m[3]*vs[1,3])/M,
                    vs[2,esc]-(m[1]*vs[2,1]+m[2]*vs[2,2]+m[3]*vs[2,3])/M,
                    vs[3,esc]-(m[1]*vs[3,1]+m[2]*vs[3,2]+m[3]*vs[3,3])/M,
                )
                return ScatteringOutcome3D(:escape, esc, (min(i,j),max(i,j)),
                                          E_bin, sma_f, norm(v_esc_vec),
                                          length(config_seq), config_seq, t,
                                          E0, total_energy_3d(m, rs, vs))
            end
        end
    end

    return ScatteringOutcome3D(:timeout, 0, (0,0), 0.0, 0.0, 0.0,
                              length(config_seq), config_seq, t, E0,
                              total_energy_3d(m, rs, vs))
end

function simulate_dissipative(m::SVector{3,Float64},
                               r0::SMatrix{3,3,Float64,9},
                               v0::SMatrix{3,3,Float64,9};
                               c::Float64=100.0,
                               dt_initial::Float64=1e-3,
                               t_max::Float64=1e5,
                               escape_radius::Float64=100.0,
                               collision_radius::Float64=1e-4,
                               eta::Float64=0.01)
    M = sum(m)
    com_r = SVector(
        (m[1]*r0[1,1]+m[2]*r0[1,2]+m[3]*r0[1,3])/M,
        (m[1]*r0[2,1]+m[2]*r0[2,2]+m[3]*r0[2,3])/M,
        (m[1]*r0[3,1]+m[2]*r0[3,2]+m[3]*r0[3,3])/M,
    )
    com_v = SVector(
        (m[1]*v0[1,1]+m[2]*v0[1,2]+m[3]*v0[1,3])/M,
        (m[1]*v0[2,1]+m[2]*v0[2,2]+m[3]*v0[2,3])/M,
        (m[1]*v0[3,1]+m[2]*v0[3,2]+m[3]*v0[3,3])/M,
    )

    r = MMatrix{3,3}(r0)
    vel = MMatrix{3,3}(v0)
    @inbounds for i in 1:3
        r[1,i] -= com_r[1]; r[2,i] -= com_r[2]; r[3,i] -= com_r[3]
        vel[1,i] -= com_v[1]; vel[2,i] -= com_v[2]; vel[3,i] -= com_v[3]
    end

    rs = SMatrix{3,3}(r)
    vs = SMatrix{3,3}(vel)
    E0 = total_energy_3d(m, rs, vs)

    config_seq = BinaryConfig3D[]
    prev_pair = (0, 0)
    t = 0.0
    dt = dt_initial

    acc_newt = accelerations_3d(m, rs)
    acc_pn = pn25_acceleration(m, rs, vs, c)
    acc_total = acc_newt + acc_pn
    check_interval = 0

    while t < t_max
        _, _, d_min = closest_pair_dist_3d(rs)

        if d_min < collision_radius
            return ScatteringOutcome3D(:collision, 0, (0,0), 0.0, 0.0, 0.0,
                                     length(config_seq), config_seq, t, E0,
                                     total_energy_3d(m, rs, vs))
        end

        max_acc = max(
            sqrt(acc_total[1,1]^2+acc_total[2,1]^2+acc_total[3,1]^2),
            sqrt(acc_total[1,2]^2+acc_total[2,2]^2+acc_total[3,2]^2),
            sqrt(acc_total[1,3]^2+acc_total[2,3]^2+acc_total[3,3]^2),
        )
        dt = min(eta * sqrt(d_min / (max_acc + 1e-30)), dt_initial * 10)
        dt = max(dt, 1e-8)

        # Velocity Verlet with PN
        vel_h = MMatrix{3,3}(vs)
        @inbounds for i in 1:3
            vel_h[1,i] = vs[1,i] + 0.5*dt*acc_total[1,i]
            vel_h[2,i] = vs[2,i] + 0.5*dt*acc_total[2,i]
            vel_h[3,i] = vs[3,i] + 0.5*dt*acc_total[3,i]
        end

        r_new = MMatrix{3,3}(rs)
        @inbounds for i in 1:3
            r_new[1,i] = rs[1,i] + dt*vel_h[1,i]
            r_new[2,i] = rs[2,i] + dt*vel_h[2,i]
            r_new[3,i] = rs[3,i] + dt*vel_h[3,i]
        end
        rs = SMatrix{3,3}(r_new)

        vs_half = SMatrix{3,3}(vel_h)
        acc_newt = accelerations_3d(m, rs)
        acc_pn = pn25_acceleration(m, rs, vs_half, c)
        acc_total = acc_newt + acc_pn

        @inbounds for i in 1:3
            vel_h[1,i] += 0.5*dt*acc_total[1,i]
            vel_h[2,i] += 0.5*dt*acc_total[2,i]
            vel_h[3,i] += 0.5*dt*acc_total[3,i]
        end
        vs = SMatrix{3,3}(vel_h)

        t += dt
        check_interval += 1

        if check_interval >= 10
            check_interval = 0
            cfg = identify_config_3d(m, rs, vs, t)
            if cfg !== nothing && cfg.pair != prev_pair
                push!(config_seq, cfg)
                prev_pair = cfg.pair
            end
            esc = check_escape_3d(m, rs, vs, escape_radius)
            if esc > 0
                others = filter(x -> x != esc, 1:3)
                i, j = others[1], others[2]
                @inbounds d_bin = sqrt((rs[1,i]-rs[1,j])^2+(rs[2,i]-rs[2,j])^2+(rs[3,i]-rs[3,j])^2)
                mu_ij = m[i]*m[j]/(m[i]+m[j])
                @inbounds vrel = SVector(vs[1,i]-vs[1,j], vs[2,i]-vs[2,j], vs[3,i]-vs[3,j])
                E_bin = 0.5*mu_ij*dot(vrel,vrel) - m[i]*m[j]/d_bin
                sma_f = E_bin < 0 ? -m[i]*m[j]/(2*E_bin) : Inf
                @inbounds v_esc_vec = SVector(
                    vs[1,esc]-(m[1]*vs[1,1]+m[2]*vs[1,2]+m[3]*vs[1,3])/M,
                    vs[2,esc]-(m[1]*vs[2,1]+m[2]*vs[2,2]+m[3]*vs[2,3])/M,
                    vs[3,esc]-(m[1]*vs[3,1]+m[2]*vs[3,2]+m[3]*vs[3,3])/M,
                )
                return ScatteringOutcome3D(:escape, esc, (min(i,j),max(i,j)),
                                          E_bin, sma_f, norm(v_esc_vec),
                                          length(config_seq), config_seq, t,
                                          E0, total_energy_3d(m, rs, vs))
            end
        end
    end

    return ScatteringOutcome3D(:timeout, 0, (0,0), 0.0, 0.0, 0.0,
                              length(config_seq), config_seq, t, E0,
                              total_energy_3d(m, rs, vs))
end

# ---------------------------------------------------------------------------
# Initial condition generators
# ---------------------------------------------------------------------------

function random_rotation_matrix(rng::AbstractRNG)
    u1, u2, u3 = rand(rng), rand(rng), rand(rng)
    q0 = sqrt(1-u1) * sin(2π*u2)
    q1 = sqrt(1-u1) * cos(2π*u2)
    q2 = sqrt(u1)   * sin(2π*u3)
    q3 = sqrt(u1)   * cos(2π*u3)
    R = SMatrix{3,3}(
        1-2*(q2^2+q3^2), 2*(q1*q2+q0*q3), 2*(q1*q3-q0*q2),
        2*(q1*q2-q0*q3), 1-2*(q1^2+q3^2), 2*(q2*q3+q0*q1),
        2*(q1*q3+q0*q2), 2*(q2*q3-q0*q1), 1-2*(q1^2+q2^2),
    )
    return R
end

function generate_3d_binary_single_ic(rng::AbstractRNG,
                                       m1::Float64, m2::Float64, m3::Float64;
                                       sma::Float64=1.0,
                                       v_inf::Float64=0.8, b_max::Float64=4.0)
    # Thermal eccentricity: f(e) = 2e → e = sqrt(U), cap at 0.95
    ecc = sqrt(rand(rng)) * 0.95

    r_peri = sma * (1 - ecc)
    v_peri = sqrt((m1 + m2) * (1 + ecc) / r_peri)

    r_loc = MMatrix{3,3,Float64}(zeros(3, 3))
    v_loc = MMatrix{3,3,Float64}(zeros(3, 3))

    # Binary at periapsis in local x-y plane
    r_loc[1,1] =  r_peri * m2/(m1+m2)
    r_loc[1,2] = -r_peri * m1/(m1+m2)
    v_loc[2,1] =  v_peri * m2/(m1+m2)
    v_loc[2,2] = -v_peri * m1/(m1+m2)

    # Rotate binary to random orbital plane
    R = random_rotation_matrix(rng)
    for i in 1:2
        pos = SVector(r_loc[1,i], r_loc[2,i], r_loc[3,i])
        vel_i = SVector(v_loc[1,i], v_loc[2,i], v_loc[3,i])
        rpos = R * pos
        rvel = R * vel_i
        r_loc[1,i] = rpos[1]; r_loc[2,i] = rpos[2]; r_loc[3,i] = rpos[3]
        v_loc[1,i] = rvel[1]; v_loc[2,i] = rvel[2]; v_loc[3,i] = rvel[3]
    end

    # Third body from random direction on sphere
    b = sqrt(rand(rng) * b_max^2)
    phi = rand(rng) * 2π
    theta = acos(2*rand(rng) - 1)
    d_start = 50.0 * sma

    app_dir = SVector(sin(theta)*cos(phi), sin(theta)*sin(phi), cos(theta))

    # Perpendicular directions for impact parameter
    aux = abs(app_dir[3]) < 0.9 ? SVector(0.0, 0.0, 1.0) : SVector(1.0, 0.0, 0.0)
    perp1 = normalize(cross(app_dir, aux))
    perp2 = cross(app_dir, perp1)
    b_angle = rand(rng) * 2π

    r3_pos = -d_start * app_dir + b * (cos(b_angle)*perp1 + sin(b_angle)*perp2)
    v3_dir = v_inf * app_dir

    r_loc[:,3] .= r3_pos
    v_loc[:,3] .= v3_dir

    masses = SVector(m1, m2, m3)
    return masses, SMatrix{3,3}(r_loc), SMatrix{3,3}(v_loc)
end

function generate_3d_democratic_ic(rng::AbstractRNG,
                                    m1::Float64, m2::Float64, m3::Float64;
                                    E_total::Float64=-0.5)
    masses = SVector(m1, m2, m3)

    # Random positions on a sphere with perturbations
    r = MMatrix{3,3,Float64}(zeros(3,3))
    for i in 1:3
        phi = rand(rng) * 2π
        costh = 2*rand(rng) - 1
        sinth = sqrt(1 - costh^2)
        rr = 0.8 + 0.4*rand(rng)
        r[1,i] = rr * sinth * cos(phi)
        r[2,i] = rr * sinth * sin(phi)
        r[3,i] = rr * costh
    end

    M = sum(masses)
    com = SVector(sum(masses[i]*r[1,i] for i in 1:3)/M,
                  sum(masses[i]*r[2,i] for i in 1:3)/M,
                  sum(masses[i]*r[3,i] for i in 1:3)/M)
    for i in 1:3; r[1,i]-=com[1]; r[2,i]-=com[2]; r[3,i]-=com[3]; end

    pe = 0.0
    for i in 1:3, j in (i+1):3
        dx=r[1,i]-r[1,j]; dy=r[2,i]-r[2,j]; dz=r[3,i]-r[3,j]
        pe -= masses[i]*masses[j]/sqrt(dx^2+dy^2+dz^2)
    end

    v = MMatrix{3,3,Float64}(0.1 .* randn(rng, 3, 3))
    vcom = SVector(sum(masses[i]*v[1,i] for i in 1:3)/M,
                   sum(masses[i]*v[2,i] for i in 1:3)/M,
                   sum(masses[i]*v[3,i] for i in 1:3)/M)
    for i in 1:3; v[1,i]-=vcom[1]; v[2,i]-=vcom[2]; v[3,i]-=vcom[3]; end

    ke = sum(0.5*masses[i]*(v[1,i]^2+v[2,i]^2+v[3,i]^2) for i in 1:3)
    desired_ke = E_total - pe
    if desired_ke > 0 && ke > 0
        scale = sqrt(desired_ke / ke)
        v .*= scale
    else
        v .*= 0.01
    end

    return masses, SMatrix{3,3}(r), SMatrix{3,3}(v)
end

# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

function config_to_dict_3d(c::BinaryConfig3D)
    Dict("pair" => [c.pair[1], c.pair[2]], "single" => c.single,
         "E_bin" => c.E_bin, "sma" => c.sma, "r_single" => c.r_single, "t" => c.t)
end

function sanitize(x::Float64)
    isfinite(x) ? x : (isinf(x) ? (x > 0 ? 1e30 : -1e30) : 0.0)
end

function outcome_to_dict_3d(o::ScatteringOutcome3D)
    Dict(
        "status" => string(o.status),
        "escaper" => o.escaper,
        "binary_pair" => [o.binary_pair[1], o.binary_pair[2]],
        "E_bin" => sanitize(o.E_bin),
        "sma" => sanitize(o.sma),
        "v_esc" => sanitize(o.v_esc),
        "n_excursions" => o.n_excursions,
        "config_sequence" => [config_to_dict_3d(c) for c in o.config_sequence],
        "lifetime" => o.lifetime,
        "E_initial" => sanitize(o.E_initial),
        "E_final" => sanitize(o.E_final),
    )
end

function save_results_3d(results::Vector{ScatteringOutcome3D}, filename::String)
    data = [outcome_to_dict_3d(o) for o in results]
    open(filename, "w") do f
        JSON.print(f, data, 2)
    end
    println("  Saved $(length(results)) results to $filename")
end

# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------

function run_3d_ensemble(n_runs::Int; masses=(1.0,1.0,1.0),
                          c::Float64=Inf, mode::Symbol=:binary_single_3d,
                          seed::Int=123, kwargs...)
    rng = MersenneTwister(seed)
    results = ScatteringOutcome3D[]
    sizehint!(results, n_runs)

    m1, m2, m3 = masses
    t_start = time()

    for i in 1:n_runs
        if mode == :binary_single_3d
            m, r, v = generate_3d_binary_single_ic(rng, m1, m2, m3; kwargs...)
        else
            m, r, v = generate_3d_democratic_ic(rng, m1, m2, m3; kwargs...)
        end

        if c < Inf
            outcome = simulate_dissipative(m, r, v; c=c)
        else
            outcome = simulate_conservative(m, r, v)
        end
        push!(results, outcome)

        if i % max(1, n_runs ÷ 10) == 0
            n_esc = count(r -> r.status == :escape, results)
            n_to = count(r -> r.status == :timeout, results)
            elapsed = time() - t_start
            @printf("  [%d/%d] %.1fs — escapes: %d, timeouts: %d\n",
                    i, n_runs, elapsed, n_esc, n_to)
        end
    end

    return results
end

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

function main_3d()
    n_runs = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 2000
    c_val = length(ARGS) >= 2 ? parse(Float64, ARGS[2]) : 100.0

    outdir = joinpath(@__DIR__, "..", "data")
    mkpath(outdir)

    configs = [
        ("3d_equal_mass",   (1.0, 1.0, 1.0)),
        ("3d_unequal_mass", (1.0, 2.0, 0.5)),
        ("3d_democratic",   (1.0, 1.0, 1.0)),
    ]

    # Phase A: Conservative 3D
    println("\n", "="^60)
    println("  Phase A: Conservative 3D (c = infinity)")
    println("="^60)

    for (name, masses) in configs
        println("\n  --- $name ($n_runs runs) ---")
        mode = name == "3d_democratic" ? :democratic_3d : :binary_single_3d

        # Warmup
        if mode == :binary_single_3d
            m, r, v = generate_3d_binary_single_ic(MersenneTwister(0), masses...)
        else
            m, r, v = generate_3d_democratic_ic(MersenneTwister(0), masses...)
        end
        simulate_conservative(m, r, v; t_max=100.0)

        t0 = time()
        results = run_3d_ensemble(n_runs; masses=masses, mode=mode, c=Inf, seed=123)
        elapsed = time() - t0

        n_esc = count(r -> r.status == :escape, results)
        n_to  = count(r -> r.status == :timeout, results)
        escaped = filter(r -> r.status == :escape, results)

        println("  Time: $(@sprintf("%.1f", elapsed))s | Escapes: $n_esc | Timeouts: $n_to")
        if !isempty(escaped)
            lts = [r.lifetime for r in escaped]
            @printf("  Lifetime: med=%.1f, mean=%.1f, max=%.0f\n",
                    median(lts), mean(lts), maximum(lts))
            dE = [abs((r.E_final - r.E_initial) / (abs(r.E_initial) + 1e-30))
                  for r in escaped]
            @printf("  Energy conservation: max|dE/E| = %.2e\n", maximum(dE))
        end

        save_results_3d(results, joinpath(outdir, "$(name)_conservative.json"))
    end

    # Phase B: Dissipative 3D
    println("\n", "="^60)
    println("  Phase B: Dissipative 3D (c = $c_val)")
    println("="^60)

    for (name, masses) in configs
        println("\n  --- $name ($n_runs runs, c=$c_val) ---")
        mode = name == "3d_democratic" ? :democratic_3d : :binary_single_3d

        # Warmup
        if mode == :binary_single_3d
            m, r, v = generate_3d_binary_single_ic(MersenneTwister(0), masses...)
        else
            m, r, v = generate_3d_democratic_ic(MersenneTwister(0), masses...)
        end
        simulate_dissipative(m, r, v; c=c_val, t_max=100.0)

        t0 = time()
        results = run_3d_ensemble(n_runs; masses=masses, mode=mode, c=c_val, seed=456)
        elapsed = time() - t0

        n_esc = count(r -> r.status == :escape, results)
        n_to  = count(r -> r.status == :timeout, results)
        escaped = filter(r -> r.status == :escape, results)

        println("  Time: $(@sprintf("%.1f", elapsed))s | Escapes: $n_esc | Timeouts: $n_to")
        if !isempty(escaped)
            lts = [r.lifetime for r in escaped]
            @printf("  Lifetime: med=%.1f, mean=%.1f, max=%.0f\n",
                    median(lts), mean(lts), maximum(lts))
            dE = [abs((r.E_final - r.E_initial) / (abs(r.E_initial) + 1e-30))
                  for r in escaped]
            @printf("  Energy dissipated (GW): median |dE/E| = %.4f\n", median(dE))
        end

        save_results_3d(results, joinpath(outdir, "$(name)_dissipative.json"))
    end

    println("\n", "="^60)
    println("  All 3D simulations complete!")
    println("="^60)
end

main_3d()
