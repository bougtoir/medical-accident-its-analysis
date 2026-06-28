"""
Three-body gravitational scattering simulator (Julia).

High-performance leapfrog integrator with adaptive time-stepping.
Classifies scattering outcomes and records the full sequence of
intermediate binary configurations for PK compartmental analysis.

Usage:
  julia threebody_scattering.jl [n_runs] [output_file]
"""

using StaticArrays
using LinearAlgebra
using Random
using JSON
using Printf

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

struct BinaryConfig
    pair::Tuple{Int,Int}    # 1-indexed
    single::Int
    E_bin::Float64
    sma::Float64
    r_single::Float64
    t::Float64
end

struct ScatteringOutcome
    status::Symbol          # :escape, :collision, :timeout
    escaper::Int            # 0 if none
    binary_pair::Tuple{Int,Int}
    E_bin::Float64
    sma::Float64
    v_esc::Float64
    n_excursions::Int
    config_sequence::Vector{BinaryConfig}
    lifetime::Float64
    E_initial::Float64
    E_final::Float64
end

# ---------------------------------------------------------------------------
# Core integrator (fully inlined, no allocations in hot loop)
# ---------------------------------------------------------------------------

@inline function accelerations(m::SVector{3,Float64}, r::SMatrix{3,3,Float64,9})
    # r is 3×3: column j = position of body j
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

@inline function closest_pair_dist(r::SMatrix{3,3,Float64,9})
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

function total_energy(m::SVector{3,Float64}, r::SMatrix{3,3,Float64,9},
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

function identify_config(m::SVector{3,Float64}, r::SMatrix{3,3,Float64,9},
                         v::SMatrix{3,3,Float64,9}, t::Float64)
    i, j, d_bin = closest_pair_dist(r)
    k = 6 - i - j  # 1+2+3=6

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

    return BinaryConfig((min(i,j), max(i,j)), k, E_bin, sma, r_single, t)
end

function check_escape(m::SVector{3,Float64}, r::SMatrix{3,3,Float64,9},
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

        # Check if unbound from other two
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

function simulate_scattering(m::SVector{3,Float64},
                              r0::SMatrix{3,3,Float64,9},
                              v0::SMatrix{3,3,Float64,9};
                              dt_initial::Float64=1e-3,
                              t_max::Float64=1e5,
                              escape_radius::Float64=100.0,
                              collision_radius::Float64=1e-4,
                              eta::Float64=0.01)
    # Move to COM frame
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
    E0 = total_energy(m, rs, vs)

    config_seq = BinaryConfig[]
    prev_pair = (0, 0)
    t = 0.0
    dt = dt_initial

    acc = accelerations(m, rs)

    check_interval = 0
    while t < t_max
        _, _, d_min = closest_pair_dist(rs)

        if d_min < collision_radius
            return ScatteringOutcome(:collision, 0, (0,0), 0.0, 0.0, 0.0,
                                     length(config_seq), config_seq, t, E0,
                                     total_energy(m, rs, vs))
        end

        max_acc = max(
            sqrt(acc[1,1]^2+acc[2,1]^2+acc[3,1]^2),
            sqrt(acc[1,2]^2+acc[2,2]^2+acc[3,2]^2),
            sqrt(acc[1,3]^2+acc[2,3]^2+acc[3,3]^2),
        )
        dt = min(eta * sqrt(d_min / (max_acc + 1e-30)), dt_initial * 10)
        dt = max(dt, 1e-8)

        # Leapfrog KDK
        # Half kick
        vel_h = MMatrix{3,3}(vs)
        @inbounds for i in 1:3
            vel_h[1,i] = vs[1,i] + 0.5*dt*acc[1,i]
            vel_h[2,i] = vs[2,i] + 0.5*dt*acc[2,i]
            vel_h[3,i] = vs[3,i] + 0.5*dt*acc[3,i]
        end

        # Drift
        r_new = MMatrix{3,3}(rs)
        @inbounds for i in 1:3
            r_new[1,i] = rs[1,i] + dt*vel_h[1,i]
            r_new[2,i] = rs[2,i] + dt*vel_h[2,i]
            r_new[3,i] = rs[3,i] + dt*vel_h[3,i]
        end
        rs = SMatrix{3,3}(r_new)

        # New acc
        acc = accelerations(m, rs)

        # Second half kick
        @inbounds for i in 1:3
            vel_h[1,i] += 0.5*dt*acc[1,i]
            vel_h[2,i] += 0.5*dt*acc[2,i]
            vel_h[3,i] += 0.5*dt*acc[3,i]
        end
        vs = SMatrix{3,3}(vel_h)

        t += dt
        check_interval += 1

        # Check config and escape every 10 steps to reduce overhead
        if check_interval >= 10
            check_interval = 0

            cfg = identify_config(m, rs, vs, t)
            if cfg !== nothing && cfg.pair != prev_pair
                push!(config_seq, cfg)
                prev_pair = cfg.pair
            end

            esc = check_escape(m, rs, vs, escape_radius)
            if esc > 0
                others = filter(x -> x != esc, 1:3)
                i, j = others[1], others[2]
                @inbounds d_bin = sqrt((rs[1,i]-rs[1,j])^2+(rs[2,i]-rs[2,j])^2+(rs[3,i]-rs[3,j])^2)
                mu_ij = m[i]*m[j]/(m[i]+m[j])
                @inbounds vrel = SVector(vs[1,i]-vs[1,j], vs[2,i]-vs[2,j], vs[3,i]-vs[3,j])
                E_bin = 0.5*mu_ij*dot(vrel,vrel) - m[i]*m[j]/d_bin
                sma_f = E_bin < 0 ? -m[i]*m[j]/(2*E_bin) : Inf

                # Escape velocity in COM frame
                @inbounds v_esc_vec = SVector(
                    vs[1,esc] - (m[1]*vs[1,1]+m[2]*vs[1,2]+m[3]*vs[1,3])/M,
                    vs[2,esc] - (m[1]*vs[2,1]+m[2]*vs[2,2]+m[3]*vs[2,3])/M,
                    vs[3,esc] - (m[1]*vs[3,1]+m[2]*vs[3,2]+m[3]*vs[3,3])/M,
                )

                return ScatteringOutcome(:escape, esc, (min(i,j),max(i,j)),
                                          E_bin, sma_f, norm(v_esc_vec),
                                          length(config_seq), config_seq, t,
                                          E0, total_energy(m, rs, vs))
            end
        end
    end

    return ScatteringOutcome(:timeout, 0, (0,0), 0.0, 0.0, 0.0,
                              length(config_seq), config_seq, t, E0,
                              total_energy(m, rs, vs))
end

# ---------------------------------------------------------------------------
# Initial condition generators
# ---------------------------------------------------------------------------

function generate_binary_single_ic(rng::AbstractRNG,
                                    m1::Float64, m2::Float64, m3::Float64;
                                    sma::Float64=1.0, ecc::Float64=0.0,
                                    v_inf::Float64=0.8, b_max::Float64=4.0)
    r_peri = sma * (1 - ecc)
    v_peri = sqrt((m1 + m2) * (1 + ecc) / r_peri)

    r = MMatrix{3,3,Float64}(zeros(3, 3))
    v = MMatrix{3,3,Float64}(zeros(3, 3))

    r[1,1] =  r_peri * m2/(m1+m2)
    r[1,2] = -r_peri * m1/(m1+m2)
    v[2,1] =  v_peri * m2/(m1+m2)
    v[2,2] = -v_peri * m1/(m1+m2)

    b = sqrt(rand(rng) * b_max^2)
    phi = rand(rng) * 2π
    theta = acos(2*rand(rng) - 1)

    d_start = 50.0 * sma

    r3 = SVector(d_start, b*cos(phi), b*sin(phi))
    ct, st = cos(theta), sin(theta)
    r3_rot = SVector(ct*r3[1]+st*r3[3], r3[2], -st*r3[1]+ct*r3[3])
    r[:,3] .= r3_rot
    nr = norm(r3_rot)
    v[:,3] .= -v_inf .* r3_rot ./ nr

    masses = SVector(m1, m2, m3)
    return masses, SMatrix{3,3}(r), SMatrix{3,3}(v)
end

function generate_democratic_ic(rng::AbstractRNG,
                                 m1::Float64, m2::Float64, m3::Float64;
                                 E_total::Float64=-0.5)
    masses = SVector(m1, m2, m3)

    angles = SVector(0.0, 2π/3, 4π/3) .+ SVector(0.3*(2*rand(rng)-1), 0.3*(2*rand(rng)-1), 0.3*(2*rand(rng)-1))
    r_sc = SVector(1.0+0.3*(2*rand(rng)-1), 1.0+0.3*(2*rand(rng)-1), 1.0+0.3*(2*rand(rng)-1))

    r = MMatrix{3,3,Float64}(zeros(3,3))
    for i in 1:3
        r[1,i] = r_sc[i]*cos(angles[i])
        r[2,i] = r_sc[i]*sin(angles[i])
        r[3,i] = 0.1*(2*rand(rng)-1)
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
# Batch runner
# ---------------------------------------------------------------------------

function run_ensemble(n_runs::Int; masses=(1.0,1.0,1.0),
                      mode::Symbol=:binary_single, seed::Int=42, kwargs...)
    rng = MersenneTwister(seed)
    results = ScatteringOutcome[]
    sizehint!(results, n_runs)

    m1, m2, m3 = masses
    t_start = time()

    for i in 1:n_runs
        if mode == :binary_single
            m, r, v = generate_binary_single_ic(rng, m1, m2, m3; kwargs...)
        else
            m, r, v = generate_democratic_ic(rng, m1, m2, m3; kwargs...)
        end

        outcome = simulate_scattering(m, r, v)
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
# JSON output for Python analysis
# ---------------------------------------------------------------------------

function config_to_dict(c::BinaryConfig)
    Dict("pair" => [c.pair[1], c.pair[2]], "single" => c.single,
         "E_bin" => c.E_bin, "sma" => c.sma, "r_single" => c.r_single, "t" => c.t)
end

function sanitize_float(x::Float64)
    isfinite(x) ? x : (isinf(x) ? (x > 0 ? 1e30 : -1e30) : 0.0)
end

function outcome_to_dict(o::ScatteringOutcome)
    Dict(
        "status" => string(o.status),
        "escaper" => o.escaper,
        "binary_pair" => [o.binary_pair[1], o.binary_pair[2]],
        "E_bin" => sanitize_float(o.E_bin),
        "sma" => sanitize_float(o.sma),
        "v_esc" => sanitize_float(o.v_esc),
        "n_excursions" => o.n_excursions,
        "config_sequence" => [config_to_dict(c) for c in o.config_sequence],
        "lifetime" => o.lifetime,
        "E_initial" => sanitize_float(o.E_initial),
        "E_final" => sanitize_float(o.E_final),
    )
end

function save_results(results::Vector{ScatteringOutcome}, filename::String)
    data = [outcome_to_dict(o) for o in results]
    open(filename, "w") do f
        JSON.print(f, data, 2)
    end
    println("  Saved $(length(results)) results to $filename")
end

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

function main()
    n_runs = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 5000
    outdir = joinpath(@__DIR__, "..", "data")
    mkpath(outdir)

    configs = [
        ("equal_mass",   (1.0, 1.0, 1.0), :binary_single,
         Dict(:v_inf=>0.8, :b_max=>4.0)),
        ("unequal_mass", (1.0, 2.0, 0.5), :binary_single,
         Dict(:v_inf=>0.8, :b_max=>4.0)),
        ("democratic",   (1.0, 1.0, 1.0), :democratic,
         Dict{Symbol,Any}()),
    ]

    for (name, masses, mode, kwargs) in configs
        println("\n", "="^60)
        println("  $name — $n_runs runs (mode=$mode)")
        println("="^60)

        # Warmup (JIT compile)
        if mode == :binary_single
            m, r, v = generate_binary_single_ic(MersenneTwister(0),
                                                 masses...; kwargs...)
        else
            m, r, v = generate_democratic_ic(MersenneTwister(0), masses...)
        end
        simulate_scattering(m, r, v; t_max=100.0)

        t0 = time()
        results = run_ensemble(n_runs; masses=masses, mode=mode, seed=42, kwargs...)
        elapsed = time() - t0

        n_esc = count(r -> r.status == :escape, results)
        n_col = count(r -> r.status == :collision, results)
        n_to  = count(r -> r.status == :timeout, results)
        println("\n  Total time: $(@sprintf("%.1f", elapsed))s")
        println("  Results: $n_esc escapes, $n_col collisions, $n_to timeouts")

        escaped = filter(r -> r.status == :escape, results)
        if !isempty(escaped)
            lts = [r.lifetime for r in escaped]
            excs = [r.n_excursions for r in escaped]
            @printf("  Lifetime: median=%.2f, mean=%.2f, max=%.2f\n",
                    median(lts), mean(lts), maximum(lts))
            @printf("  Excursions: median=%.0f, mean=%.1f, max=%d\n",
                    median(excs), mean(excs), maximum(excs))

            dE = [abs((r.E_final - r.E_initial) / (abs(r.E_initial) + 1e-30))
                  for r in escaped]
            @printf("  Energy conservation: max|dE/E| = %.2e\n", maximum(dE))
        end

        save_results(results, joinpath(outdir, "$(name).json"))
    end

    println("\n", "="^60)
    println("  All simulations complete!")
    println("="^60)
end

# Helper functions
using Statistics: median, mean

main()
