"""
Mass-ratio scan for Population PK analysis.

Runs three-body scattering ensembles across a grid of mass ratios,
outputting transition counts and summary statistics for each.
This provides the "population" data for mixed-effects PK modelling.

Usage:
  julia mass_scan.jl [n_runs_per_point]
"""

include("threebody_scattering.jl")

using Printf
using JSON
using Random
using Statistics

# ---------------------------------------------------------------------------
# Extract transition data from outcomes (Julia-side aggregation)
# ---------------------------------------------------------------------------

function extract_transitions(results::Vector{ScatteringOutcome})
    trans = zeros(Int, 3, 3)   # compartment i→j transition counts
    esc_counts = zeros(Int, 3) # escapes from each compartment
    dwell_times = [Float64[] for _ in 1:3]
    lifetimes = Float64[]
    n_excursions = Int[]
    escaper_body = Int[]

    pair_to_comp = Dict((1,2)=>1, (1,3)=>2, (2,3)=>3)

    for r in results
        r.status != :escape && continue
        seq = r.config_sequence
        isempty(seq) && continue

        push!(lifetimes, r.lifetime)
        push!(n_excursions, r.n_excursions)
        push!(escaper_body, r.escaper)

        # Transitions
        for k in 1:length(seq)-1
            c_from = get(pair_to_comp, seq[k].pair, 0)
            c_to = get(pair_to_comp, seq[k+1].pair, 0)
            if c_from > 0 && c_to > 0 && c_from != c_to
                trans[c_from, c_to] += 1
            end
        end

        # Dwell times
        for k in 1:length(seq)
            c = get(pair_to_comp, seq[k].pair, 0)
            c == 0 && continue
            t_start = seq[k].t
            t_end = k < length(seq) ? seq[k+1].t : r.lifetime
            dt = t_end - t_start
            dt > 0 && push!(dwell_times[c], dt)
        end

        # Escape from which compartment
        last_c = get(pair_to_comp, seq[end].pair, 0)
        last_c > 0 && (esc_counts[last_c] += 1)
    end

    # Compute rates (CTMC MLE)
    T = [isempty(dwell_times[i]) ? 1e-10 : sum(dwell_times[i]) for i in 1:3]
    rates = zeros(3, 3)
    ke = zeros(3)
    for i in 1:3
        for j in 1:3
            i == j && continue
            rates[i,j] = trans[i,j] / T[i]
        end
        ke[i] = esc_counts[i] / T[i]
    end

    return Dict(
        "trans" => [[trans[i,j] for j in 1:3] for i in 1:3],
        "esc_counts" => [esc_counts[i] for i in 1:3],
        "total_dwell_time" => T,
        "rates" => [[rates[i,j] for j in 1:3] for i in 1:3],
        "ke" => [ke[i] for i in 1:3],
        "n_escape" => length(lifetimes),
        "lifetimes_median" => isempty(lifetimes) ? 0.0 : median(lifetimes),
        "lifetimes_mean" => isempty(lifetimes) ? 0.0 : mean(lifetimes),
        "lifetimes_std" => isempty(lifetimes) ? 0.0 : std(lifetimes),
        "lifetimes_q25" => isempty(lifetimes) ? 0.0 : quantile(lifetimes, 0.25),
        "lifetimes_q75" => isempty(lifetimes) ? 0.0 : quantile(lifetimes, 0.75),
        "mean_excursions" => isempty(n_excursions) ? 0.0 : mean(n_excursions),
        "escaper_probs" => begin
            n = length(escaper_body)
            n == 0 ? [0.0, 0.0, 0.0] :
                [count(==(b), escaper_body)/n for b in 1:3]
        end,
        "lifetime_percentiles" => isempty(lifetimes) ? zeros(11) :
            [quantile(lifetimes, p) for p in 0.0:0.1:1.0],
    )
end

# ---------------------------------------------------------------------------
# Mass scan
# ---------------------------------------------------------------------------

function run_mass_scan(; n_runs::Int=1000, seed::Int=42)
    # Mass ratios to scan: fix m1=1.0, vary m2 and m3
    # This gives us a 2D parameter space for population PK
    m2_values = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
    m3_values = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]

    results_all = Dict[]
    total = length(m2_values) * length(m3_values)
    idx = 0

    for m2 in m2_values
        for m3 in m3_values
            # Skip duplicate by symmetry (m2 > m3 only when m2 != m3)
            # Actually keep all for now — asymmetry in IC breaks the symmetry
            idx += 1
            masses = (1.0, m2, m3)
            @printf("\n[%d/%d] masses=(1.0, %.2f, %.2f) — %d runs\n",
                    idx, total, m2, m3, n_runs)

            t0 = time()
            outcomes = run_ensemble(n_runs; masses=masses,
                                    mode=:binary_single, seed=seed,
                                    v_inf=0.8, b_max=4.0)
            elapsed = time() - t0

            data = extract_transitions(outcomes)
            data["masses"] = [1.0, m2, m3]
            data["mass_ratio_q"] = m2 / (1.0 + m2 + m3)  # fraction of total
            data["mass_ratio_q3"] = m3 / (1.0 + m2 + m3)
            data["elapsed_s"] = elapsed

            n_esc = data["n_escape"]
            @printf("  %.1fs — %d escapes, median_τ=%.1f, mean_exc=%.1f\n",
                    elapsed, n_esc, data["lifetimes_median"], data["mean_excursions"])

            push!(results_all, data)
        end
    end

    return results_all
end

function main()
    n_runs = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 1000

    println("="^60)
    println("  Mass-ratio scan for Population PK")
    println("  $n_runs runs per mass configuration")
    println("="^60)

    results = run_mass_scan(n_runs=n_runs, seed=42)

    outdir = joinpath(@__DIR__, "..", "data")
    mkpath(outdir)
    outfile = joinpath(outdir, "mass_scan.json")
    open(outfile, "w") do f
        JSON.print(f, results, 2)
    end
    println("\nSaved $(length(results)) configurations to $outfile")

    println("\n", "="^60)
    println("  Mass scan complete!")
    println("="^60)
end

main()
