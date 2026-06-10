# Natural Experiment: Academic Calendar vs Biological Seasonality

## Design

Using geographic variation in academic year start months as a natural
instrument to separate institutional from biological drivers of seasonality
in GEO PSC differentiation dataset submissions.

| Group | Countries | Academic Year Start | Hemisphere | n |
|-------|-----------|--------------------|-----------:|--:|
| Jan/Feb-start (AU/NZ/BR, SH) | Australia, NZ, Brazil, ... | Jan/Feb | SH | 83 |
| Mar/Apr-start (JP/KR) | Japan, South Korea | Mar/Apr | NH | 250 |
| Sep/Oct-start (US/EU/CN) | USA, UK, Germany, China, ... | Sep/Oct | NH | 2825 |

## Results

### Group-level Statistics

| Group | n | Peak (mode) | Circular peak | Rayleigh R | χ² | p |
|-------|---:|:---:|:---:|:---:|---:|---:|
| Jan/Feb-start (AU/NZ/BR, SH) | 83 | Mar | 2.7 | 0.172 | 15.2 | 0.1749 |
| Mar/Apr-start (JP/KR) | 250 | Mar | 4.4 | 0.172 | 32.8 | 0.0006 |
| Sep/Oct-start (US/EU/CN) | 2825 | Jan | 1.3 | 0.023 | 15.7 | 0.1542 |

### Per-Country Detail

| Country | Acad Start | Hemisphere | n | Peak (mode) | Circular peak | R |
|---------|:---:|:---:|---:|:---:|:---:|:---:|
| Japan | Apr | NH | 200 | Mar | 4.3 | 0.182 |
| South Korea | Mar | NH | 50 | Jan | 5.2 | 0.147 |
| USA | Sep | NH | 1483 | Jan | 12.1 | 0.029 |
| United Kingdom | Sep | NH | 215 | Jan | 1.7 | 0.125 |
| Germany | Oct | NH | 235 | Oct | 10.3 | 0.036 |
| China | Sep | NH | 282 | May | 5.4 | 0.083 |
| Australia | Jan | SH | 74 | Feb | 2.6 | 0.156 |

## Interpretation

**Key finding**: Peak months differ between Mar/Apr-start (4.4) and Sep-start (1.3) groups. This pattern is **partially consistent with academic-calendar effects**.

The Southern Hemisphere group does NOT show clear inversion of peak month. This may reflect small sample size or dominant institutional effects.

### Limitations

1. GEO submission date ≠ experiment date (6–18 month lag)
2. Southern Hemisphere sample is very small
3. Multiple confounders (funding cycles, conference deadlines, etc.)
4. Rayleigh test assumes unimodal circular distribution
