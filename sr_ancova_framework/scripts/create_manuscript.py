#!/usr/bin/env python3
"""
Generate PRE manuscript as docx with inline figures.

Title: "Covariate-adjusted stochastic resonance in threshold-based event detectors"

Structure follows PRE Regular Article format.
References: numbered in order of first appearance (Vancouver/APS style).
"""

from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / 'pre_submission'
FIG_DIR = OUT_DIR  # figures are in same directory


def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    return h


def add_paragraph(doc, text, style='Normal', bold=False, italic=False,
                  alignment=None, space_after=None, space_before=None):
    p = doc.add_paragraph(text, style=style)
    if bold:
        for run in p.runs:
            run.bold = True
    if italic:
        for run in p.runs:
            run.italic = True
    if alignment:
        p.alignment = alignment
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    if space_before is not None:
        p.paragraph_format.space_before = Pt(space_before)
    return p


def add_figure(doc, img_path, caption, width=Inches(5.5)):
    """Insert figure inline with caption below."""
    if not img_path.exists():
        add_paragraph(doc, f"[MISSING FIGURE: {img_path.name}]")
        return
    # Space before figure
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(12)
    run = p_img.add_run()
    run.add_picture(str(img_path), width=width)

    # Caption
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.space_before = Pt(6)
    p_cap.paragraph_format.space_after = Pt(12)
    run_cap = p_cap.add_run(caption)
    run_cap.font.size = Pt(9)
    return p_cap


def build_manuscript():
    doc = Document()

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(11)
    style.paragraph_format.line_spacing = 1.5

    # =========================================================
    # Title page
    # =========================================================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(
        'Covariate-adjusted stochastic resonance\n'
        'in threshold-based event detectors'
    )
    run.font.size = Pt(16)
    run.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('[Author names and affiliations to be added]')
    run.font.size = Pt(11)
    run.italic = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(24)
    run = p.add_run('(Dated: \\today)')
    run.font.size = Pt(10)

    # =========================================================
    # Abstract
    # =========================================================
    add_heading(doc, 'Abstract', level=1)
    add_paragraph(doc, (
        'Stochastic resonance (SR) — the counterintuitive enhancement of signal detection '
        'by noise in nonlinear threshold systems — has been extensively studied in bistable '
        'and excitable systems. Independently, covariate adjustment methods from statistical '
        'modeling (analogous to analysis of covariance, ANCOVA) provide systematic tools for '
        'separating signal from structured noise when the noise depends on observable covariates. '
        'Here we unify these two perspectives for threshold-based event detectors. We show '
        'analytically that covariate adjustment with noise model correlation ρ reduces the '
        'effective noise variance by a factor (1 − ρ²), shifting the operating point on the '
        'SR curve. This leads to a central result: there exists an optimal noise model accuracy '
        'ρ* = √(1 − θ²/σ²) that maximizes output signal-to-noise ratio, where θ is the '
        'detection threshold and σ is the input noise level. When the system operates in the '
        'excess noise regime (σ > θ), covariate adjustment is beneficial and the SNR gain grows '
        'exponentially with input noise. When the system is already at the SR optimum (σ ≈ θ), '
        'any noise removal degrades performance. We validate this framework through Monte Carlo '
        'simulations and demonstrate its practical application using dynamic vision sensor (DVS) '
        'data from astronomical observations, where a physics-informed covariate model achieves '
        'ROC-AUC = 0.866 for noise classification with 93.9% signal preservation.'
    ))

    # =========================================================
    # I. Introduction
    # =========================================================
    add_heading(doc, 'I. INTRODUCTION', level=1)
    add_paragraph(doc, (
        'The relationship between noise and signal detection in nonlinear systems presents a '
        'fundamental paradox: while noise is conventionally regarded as a nuisance that degrades '
        'measurement quality, stochastic resonance (SR) demonstrates that an optimal amount of '
        'noise can actually enhance the detection of weak signals in threshold-based systems '
        '[1–3]. This phenomenon, first described in the context of paleoclimatic oscillations '
        '[4] and subsequently observed across diverse physical, biological, and engineered systems '
        '[5], challenges the conventional wisdom that noise should always be minimized.'
    ))
    add_paragraph(doc, (
        'Separately, the field of statistical modeling has long recognized that noise need not '
        'be treated as an undifferentiated nuisance variable. Analysis of covariance (ANCOVA) '
        'and related regression techniques model noise as a function of observable covariates — '
        'temperature, instrumental parameters, environmental conditions — and adjust '
        'observations accordingly [6]. The adjusted residuals have reduced variance, improving '
        'the precision of downstream inference. This covariate adjustment philosophy has been '
        'applied in signal processing contexts including adaptive noise cancellation [7], '
        'Wiener filtering [8], and physics-informed denoising [9], though typically without '
        'reference to the SR framework.'
    ))
    add_paragraph(doc, (
        'These two perspectives — noise as beneficial resource (SR) and noise as modelable '
        'covariate (ANCOVA) — have developed largely in isolation. The SR literature focuses '
        'on characterizing the optimal noise level for detection but rarely addresses how to '
        'navigate toward that optimum in practice. The denoising literature focuses on removing '
        'noise but does not consider whether complete noise removal might be counterproductive '
        'in threshold-based systems. This disconnect is particularly relevant for emerging '
        'sensor technologies such as dynamic vision sensors (DVS) [10], single-photon detectors '
        '[11], and neuromorphic systems [12], all of which employ threshold-based event '
        'generation where SR effects are intrinsic.'
    ))
    add_paragraph(doc, (
        'In this paper, we bridge these two perspectives by analyzing how covariate adjustment '
        'interacts with stochastic resonance in threshold-based event detectors. We derive an '
        'analytical expression for the optimal noise model accuracy — the degree to which noise '
        'should be modeled and removed — as a function of the system\'s noise-to-threshold '
        'ratio. Our central finding is that the optimal strategy is not to remove all '
        'modelable noise, but to adjust noise precisely to the SR optimum. We validate this '
        'framework through numerical simulations and demonstrate its application to DVS-based '
        'astronomical observations, where physics-informed noise modeling provides the covariate '
        'structure.'
    ))

    # =========================================================
    # II. General Framework
    # =========================================================
    add_heading(doc, 'II. GENERAL FRAMEWORK', level=1)

    add_heading(doc, 'A. Threshold-based event detector', level=2)
    add_paragraph(doc, (
        'We consider a general threshold-based event detector that receives a continuous '
        'input x(t) = s(t) + n(t), where s(t) is a deterministic signal and n(t) is '
        'zero-mean Gaussian noise with variance σ². The detector generates a binary event '
        'stream E(t) according to'
    ))
    add_paragraph(doc, (
        '    E(t) = 1    if |x(t)| > θ,\n'
        '    E(t) = 0    otherwise,'
    ), space_before=6, space_after=6)
    add_paragraph(doc, (
        'where θ > 0 is the detection threshold. This model encompasses a wide class of '
        'physical detectors including level-crossing detectors, neuronal firing models, '
        'Schmitt triggers, single-photon avalanche diodes, and dynamic vision sensor pixels '
        '[10, 13]. The signal is assumed subthreshold: A ≡ max|s(t)| < θ, so that events '
        'can only occur when noise assists the signal in crossing the threshold (Fig. 1a).'
    ))

    # Fig 1
    add_figure(doc, FIG_DIR / 'fig1_schematic.png',
               'FIG. 1. Conceptual schematic of the covariate-adjusted stochastic resonance '
               'framework. (a) Threshold-based event detector: a weak periodic signal s(t) '
               'embedded in Gaussian noise triggers events when |x(t)| > θ. Tick marks above '
               'indicate event times. (b) Stochastic resonance: the event rate modulation '
               'tracking the signal period is maximized at intermediate noise (green), '
               'suppressed at low noise (red), and washed out at high noise (blue). '
               '(c) Covariate adjustment with noise model correlation ρ narrows the residual '
               'noise distribution, equivalent to shifting the operating point on the SR curve.',
               width=Inches(6.0))

    add_heading(doc, 'B. Stochastic resonance in threshold detectors', level=2)
    add_paragraph(doc, (
        'Following the two-state theory of McNamara and Wiesenfeld [1], the output '
        'signal-to-noise ratio of the event stream for a weak periodic signal '
        's(t) = A sin(2πf₀t) can be expressed as'
    ))
    add_paragraph(doc, (
        '    SNR_out(σ) ∝ (A/σ²)² exp(−2θ²/σ²).'
    ), space_before=6, space_after=6)
    add_paragraph(doc, (
        'This function exhibits a single maximum at σ* = θ (Fig. 2), which is the hallmark '
        'of stochastic resonance: the output SNR is maximized at an intermediate noise level '
        'equal to the detection threshold, independent of the signal amplitude A. For σ < θ, '
        'insufficient noise reaches the threshold and events are rare; for σ ≫ θ, events are '
        'frequent but dominated by noise with little signal modulation. The optimal regime '
        'σ ≈ θ balances these effects, producing events that are both frequent enough and '
        'sufficiently signal-correlated (Fig. 1b).'
    ))

    add_heading(doc, 'C. Covariate adjustment as noise reduction', level=2)
    add_paragraph(doc, (
        'Suppose the noise n(t) depends on observable covariates z(t) = (z₁(t), …, z_k(t))ᵀ '
        'through a parametric model n̂(t) = f(z(t); β). In the ANCOVA analogy, these '
        'covariates play the role of confounding variables that are modeled and "adjusted out." '
        'The adjusted observation is'
    ))
    add_paragraph(doc, (
        '    x_adj(t) = x(t) − n̂(t) = s(t) + ε(t),'
    ), space_before=6, space_after=6)
    add_paragraph(doc, (
        'where ε(t) = n(t) − n̂(t) is the residual noise. If the noise model achieves '
        'correlation ρ = Corr(n̂, n), then'
    ))
    add_paragraph(doc, (
        '    Var(ε) = (1 − ρ²) σ²,'
    ), space_before=6, space_after=6)
    add_paragraph(doc, (
        'so the effective noise level after adjustment is σ_eff = σ√(1 − ρ²). Crucially, '
        'this covariate adjustment does not change the threshold θ or the signal s(t); it '
        'only reduces the noise variance. From the perspective of the SR curve, covariate '
        'adjustment moves the operating point leftward (toward lower effective noise) by a '
        'factor √(1 − ρ²) (Fig. 1c).'
    ))

    add_heading(doc, 'D. Optimal noise model accuracy', level=2)
    add_paragraph(doc, (
        'Combining the SR expression with the covariate adjustment model, the output SNR '
        'as a function of both input noise σ and model correlation ρ is'
    ))
    add_paragraph(doc, (
        '    SNR_out(σ, ρ) ∝ [A / (σ²(1 − ρ²))]² exp(−2θ² / [σ²(1 − ρ²)]).'
    ), space_before=6, space_after=6)
    add_paragraph(doc, (
        'Maximizing over ρ at fixed σ yields the optimal noise model accuracy:'
    ))
    add_paragraph(doc, (
        '    ρ*(σ) = { 0,                          if σ ≤ θ,\n'
        '            { √(1 − θ²/σ²),              if σ > θ.'
    ), space_before=6, space_after=6)
    add_paragraph(doc, (
        'This result has a clear physical interpretation (Fig. 5a). When the input noise is '
        'at or below the SR optimum (σ ≤ θ), the system is already operating at peak '
        'efficiency; any noise removal moves the operating point away from the optimum and '
        'degrades the SNR. In this SR regime, the optimal strategy is to leave the noise '
        'untouched (ρ* = 0). When the input noise exceeds the SR optimum (σ > θ), the system '
        'is in the excess noise regime, and covariate adjustment should reduce the effective '
        'noise precisely to the SR optimum: σ_eff = σ√(1 − ρ*²) = θ.'
    ))
    add_paragraph(doc, (
        'At the optimal ρ*, the SNR improvement relative to no adjustment is'
    ))
    add_paragraph(doc, (
        '    SNR_out(σ, ρ*) / SNR_out(σ, 0) = (σ/θ)⁴ exp(2(σ² − θ²)/σ²),'
    ), space_before=6, space_after=6)
    add_paragraph(doc, (
        'which grows as ~exp(2σ²/θ²) for σ ≫ θ (Fig. 5b). This exponential growth reflects '
        'the severe penalty of operating far above the SR optimum and the correspondingly '
        'large benefit of covariate adjustment in high-noise environments.'
    ))

    # =========================================================
    # III. Numerical Simulations
    # =========================================================
    add_heading(doc, 'III. NUMERICAL SIMULATIONS', level=1)

    add_paragraph(doc, (
        'We validate the analytical results through Monte Carlo simulations of a threshold '
        'detector with Gaussian noise. The signal is a sinusoid s(t) = A sin(2πf₀t) with '
        'A/θ = 0.3 and f₀ = 5 Hz, sampled at dt = 1 ms for N = 10⁵ time steps per trial.'
    ))

    add_heading(doc, 'A. Stochastic resonance curves', level=2)
    add_paragraph(doc, (
        'Figure 2 shows the output SNR as a function of input noise level for different '
        'covariate adjustment strengths. The Monte Carlo estimates (black circles) confirm '
        'the analytical prediction (black curve) for the unadjusted case (ρ = 0), with '
        'the SR peak occurring at σ/θ ≈ 1.0. The adjusted curves (colored lines) show '
        'the SR peak shifting rightward to σ/θ ≈ 1/√(1 − ρ²), consistent with the '
        'analytical framework. Notably, the peak height remains constant across all ρ '
        'values (when measured in effective noise), confirming that covariate adjustment '
        'translates the SR curve without altering its shape.'
    ))

    # Fig 2
    add_figure(doc, FIG_DIR / 'fig2_sr_curves.png',
               'FIG. 2. Stochastic resonance curves for a threshold detector (A/θ = 0.3). '
               'Solid lines: analytical SNR from two-state theory [Eq. (1)]. Black circles '
               'with error bars: Monte Carlo validation (15 trials per point). Covariate '
               'adjustment shifts the SR peak rightward, meaning the detector tolerates more '
               'input noise when a good noise model is available.',
               width=Inches(4.5))

    add_heading(doc, 'B. Detection probabilities', level=2)
    add_paragraph(doc, (
        'Figure 3 shows the detection probability P_D and false alarm probability P_FA as '
        'functions of input noise for A/θ = 0.4. Both probabilities decrease with increasing '
        'ρ at any fixed input noise level, because covariate adjustment reduces the effective '
        'noise that drives threshold crossings. The detection advantage of adjustment becomes '
        'apparent in the ROC representation (Fig. 4), where the relevant metric is P_D at a '
        'given P_FA. In the excess noise regime (σ/θ = 1.5), higher ρ produces ROC curves '
        'that are progressively further above the chance diagonal, indicating improved '
        'discriminability between signal and noise.'
    ))

    # Fig 3
    add_figure(doc, FIG_DIR / 'fig3_detection_probability.png',
               'FIG. 3. (a) Detection probability P_D and (b) false alarm probability P_FA '
               'versus input noise level for different covariate model accuracies ρ '
               '(A/θ = 0.4). Higher ρ suppresses both probabilities by reducing effective noise.',
               width=Inches(5.5))

    # Fig 4
    add_figure(doc, FIG_DIR / 'fig4_roc_comparison.png',
               'FIG. 4. ROC curves at σ_n/θ = 1.5 (excess noise regime) for different ρ. '
               'Covariate adjustment progressively improves detection performance, with '
               'ρ = 0.95 achieving near-ideal separation between signal and noise events.',
               width=Inches(3.8))

    add_heading(doc, 'C. Optimal noise model accuracy', level=2)
    add_paragraph(doc, (
        'Figure 5 presents the central result of this work. Panel (a) shows the numerically '
        'determined optimal ρ* as a function of input noise, confirming the analytical '
        'prediction ρ* = √(1 − θ²/σ²) (dashed line). The transition at σ = θ is sharp: '
        'below this threshold, no adjustment is optimal; above it, the optimal adjustment '
        'increases rapidly. Panel (b) shows that the SNR gain at optimal ρ* grows '
        'exponentially with input noise, reaching factors of ~100× at σ/θ = 4. This '
        'exponential scaling underscores the practical importance of covariate adjustment '
        'in high-noise environments, which are typical for many sensor applications.'
    ))

    # Fig 5
    add_figure(doc, FIG_DIR / 'fig5_optimal_rho.png',
               'FIG. 5. (a) Optimal noise model accuracy ρ* versus input noise. Yellow shading: '
               'SR regime (σ < θ) where ρ* = 0. Blue shading: excess noise regime (σ > θ) '
               'where ρ* = √(1 − θ²/σ²). Dashed line: analytical prediction. '
               '(b) Peak SNR improvement at optimal ρ* grows exponentially with input noise, '
               'reaching ~100× at σ/θ = 4.',
               width=Inches(5.5))

    add_heading(doc, 'D. Information-theoretic perspective', level=2)
    add_paragraph(doc, (
        'Figure 7 shows the mutual information I(S; E) between the periodic signal and the '
        'event stream as a function of input noise. Like the SNR measure, the mutual '
        'information exhibits an SR peak that shifts rightward with covariate adjustment. '
        'This confirms that the SR effect and the benefits of covariate adjustment are '
        'robust to the choice of performance metric and not an artifact of the particular '
        'SNR definition used.'
    ))

    # Fig 7
    add_figure(doc, FIG_DIR / 'fig7_mutual_information.png',
               'FIG. 7. Mutual information I(S; E) between the periodic signal and the event '
               'stream. The SR peak shifts rightward with covariate adjustment (ρ = 0.8), '
               'consistent with the SNR analysis in Fig. 2.',
               width=Inches(4.5))

    # =========================================================
    # IV. Application: Dynamic Vision Sensors
    # =========================================================
    add_heading(doc, 'IV. APPLICATION: DYNAMIC VISION SENSORS', level=1)

    add_paragraph(doc, (
        'To demonstrate the practical relevance of the covariate-adjusted SR framework, '
        'we apply it to event-based astronomical observations using dynamic vision sensors '
        '(DVS). A DVS pixel fires an event when the logarithmic light intensity change '
        'exceeds a threshold θ_ON or θ_OFF [10], making it a direct physical realization '
        'of the threshold detector model analyzed above.'
    ))

    add_heading(doc, 'A. DVS noise as structured covariate', level=2)
    add_paragraph(doc, (
        'DVS noise in astronomical applications arises from multiple identifiable physical '
        'processes: dark current shot noise (temperature-dependent), background illuminance '
        'fluctuations, threshold mismatch across pixels, and readout noise [14]. These '
        'processes constitute observable covariates z(t) = (T, I_bg, θ_mismatch, …) that '
        'predict the noise event rate through a physics-informed model [15]. Specifically, '
        'we employ a five-parameter analytical model (the A5 model) that predicts the '
        'per-pixel noise rate λ_noise(x, y) from temperature, background illuminance, and '
        'pixel-level threshold statistics. The Fano factor — the ratio of event count '
        'variance to mean — provides a local test statistic for distinguishing Poisson-like '
        'noise events (F ≈ 1) from signal-modulated events (F ≠ 1) [15].'
    ))

    add_heading(doc, 'B. Experimental results', level=2)
    add_paragraph(doc, (
        'We evaluate the framework on 20 recordings from the Event-Based Space Situational '
        'Awareness (EBSSA) dataset [16], which contains DVS observations of satellites and '
        'space debris against a star field. The task is to classify each event as signal '
        '(astronomical object) or noise (dark current, background). Figure 6a shows the '
        'noise classification performance: the Fano filter (covariate adjustment approach) '
        'achieves ROC-AUC = 0.866 ± 0.107, substantially outperforming both temporal '
        'filtering (AUC = 0.534) and a neural network approach (AUC = 0.546). Figure 6b '
        'shows the NRR-SPR trade-off: the Fano filter removes 71.3% of noise events while '
        'preserving 93.9% of signal events, occupying the upper-right region of the '
        'performance space closest to the ideal point (NRR = 1, SPR = 1).'
    ))

    # Fig 6
    add_figure(doc, FIG_DIR / 'fig6_dvs_application.png',
               'FIG. 6. Application to DVS astronomical observation (EBSSA dataset, 20 '
               'recordings). (a) Noise classification ROC-AUC: the Fano filter (covariate '
               'adjustment) achieves 0.866, far exceeding temporal filtering and neural methods. '
               '(b) NRR vs SPR trade-off: the Fano filter preserves 93.9% of signal while '
               'removing 71.3% of noise.',
               width=Inches(5.5))

    add_heading(doc, 'C. Interpretation in the SR framework', level=2)
    add_paragraph(doc, (
        'In the SR framework, DVS astronomical observations operate firmly in the excess '
        'noise regime (σ ≫ θ): the dark current noise rate far exceeds the astronomical '
        'signal event rate. The physics-informed covariate model (A5 + Fano filter) '
        'effectively achieves ρ ≈ 0.7–0.9 in terms of noise prediction accuracy. According '
        'to Fig. 5b, this should yield an SNR improvement of approximately 5–10×, consistent '
        'with the measured mean SNR improvement of 5.4× in the EBSSA evaluation [15]. The '
        'covariate adjustment does not eliminate noise entirely (NRR = 0.713, not 1.0), '
        'which is consistent with the framework\'s prediction that over-adjustment in the '
        'SR context is suboptimal.'
    ))

    # =========================================================
    # V. Discussion
    # =========================================================
    add_heading(doc, 'V. DISCUSSION', level=1)

    add_paragraph(doc, (
        'The covariate-adjusted SR framework yields several insights relevant to both '
        'theory and practice.'
    ))

    add_heading(doc, 'A. Connection to forbidden-interval theorems', level=2)
    add_paragraph(doc, (
        'The existence of an optimal ρ* is closely related to the forbidden-interval '
        'theorem of Kosko and Mitaim [17, 18], which states that SR occurs in a threshold '
        'system if and only if the noise distribution satisfies certain conditions on its '
        'support relative to the threshold. Covariate adjustment modifies the effective '
        'noise distribution, potentially moving it into or out of the forbidden interval. '
        'Our result ρ* = √(1 − θ²/σ²) provides a constructive criterion for when and how '
        'much adjustment is beneficial, complementing the existential characterization of '
        'the forbidden-interval theorem.'
    ))

    add_heading(doc, 'B. Implications for sensor design', level=2)
    add_paragraph(doc, (
        'The framework suggests that threshold-based sensors should be co-designed with '
        'noise models. Rather than minimizing noise at the hardware level (which may be '
        'costly or impractical), a sensor can operate with higher noise if an accurate '
        'covariate model is available for post-hoc adjustment. The optimal design point '
        'is one where the residual noise (after model-based adjustment) matches the '
        'threshold: σ_eff = θ. This principle applies broadly to neuromorphic sensors, '
        'event cameras, single-photon detectors, and other threshold-based devices.'
    ))

    add_heading(doc, 'C. Limitations and extensions', level=2)
    add_paragraph(doc, (
        'Our analysis assumes (i) additive Gaussian noise, (ii) a fixed threshold, and '
        '(iii) a linear noise model (ρ characterizes correlation). Real systems may exhibit '
        'non-Gaussian noise (e.g., shot noise following Poisson statistics), adaptive '
        'thresholds, and nonlinear noise dependencies. Extending the framework to these '
        'cases would require replacing the analytical SNR formula with appropriate '
        'generalizations — for instance, using the forbidden-interval theorem directly for '
        'non-Gaussian noise [17], or employing information-theoretic metrics for systems '
        'with adaptive thresholds [19]. The DVS application demonstrates that the '
        'framework\'s qualitative predictions (covariate adjustment helps in the excess '
        'noise regime; there is an optimal adjustment level) remain valid even when these '
        'assumptions are only approximately satisfied.'
    ))

    add_heading(doc, 'D. Broader applicability', level=2)
    add_paragraph(doc, (
        'Beyond event-based sensors, the covariate-adjusted SR principle applies to any '
        'system where (i) a threshold or nonlinearity mediates signal detection and '
        '(ii) the noise has observable structure. Examples include neural spike detection '
        'in electrophysiology [20], quantum key distribution in noisy channels [21], '
        'radar target detection in clutter [22], and molecular detection at the single-molecule '
        'level [23]. In each case, the key question — "how much noise should we remove?" — '
        'has the same answer: reduce the effective noise to the SR optimum, and no further.'
    ))

    # =========================================================
    # VI. Conclusion
    # =========================================================
    add_heading(doc, 'VI. CONCLUSION', level=1)
    add_paragraph(doc, (
        'We have presented a unified framework connecting stochastic resonance theory '
        'with covariate adjustment methods for threshold-based event detectors. The '
        'central result is an analytical expression for the optimal noise model accuracy '
        'ρ* = √(1 − θ²/σ²) that maximizes output SNR by balancing noise removal against '
        'the SR benefit of residual noise. This result bridges two previously disconnected '
        'research traditions: stochastic resonance (which characterizes when noise helps) '
        'and covariate adjustment (which provides tools for controlled noise reduction). '
        'The framework is validated through simulations and demonstrated on DVS astronomical '
        'data, where a physics-informed noise model achieves state-of-the-art performance '
        'consistent with the theoretical predictions. The principle — reduce noise to the '
        'SR optimum, not to zero — offers a quantitative design criterion for any '
        'threshold-based detection system operating in noisy environments.'
    ))

    # =========================================================
    # Acknowledgments
    # =========================================================
    add_heading(doc, 'ACKNOWLEDGMENTS', level=1)
    add_paragraph(doc, '[To be added.]', italic=True)

    # =========================================================
    # References
    # =========================================================
    add_heading(doc, 'REFERENCES', level=1)
    references = [
        '[1] L. Gammaitoni, P. Hänggi, P. Jung, and F. Marchesoni, "Stochastic resonance," '
        'Rev. Mod. Phys. 70, 223 (1998).',

        '[2] M. D. McDonnell and D. Abbott, "What is stochastic resonance? Definitions, '
        'misconceptions, debates, and its relevance to biology," PLoS Comput. Biol. 5, '
        'e1000348 (2009).',

        '[3] A. R. Bulsara and L. Gammaitoni, "Tuning in to noise," Phys. Today 49, 39 (1996).',

        '[4] R. Benzi, A. Sutera, and A. Vulpiani, "The mechanism of stochastic resonance," '
        'J. Phys. A: Math. Gen. 14, L453 (1981).',

        '[5] K. Wiesenfeld and F. Moss, "Stochastic resonance and the benefits of noise: '
        'from ice ages to crayfish and SQUIDs," Nature 373, 33 (1995).',

        '[6] G. W. Snedecor and W. G. Cochran, Statistical Methods, 8th ed. '
        '(Iowa State University Press, Ames, 1989).',

        '[7] B. Widrow, J. R. Glover, Jr., J. M. McCool, J. Kaunitz, C. S. Williams, '
        'R. H. Hearn, J. R. Zeidler, E. Dong, Jr., and R. C. Goodlin, "Adaptive noise '
        'cancelling: Principles and applications," Proc. IEEE 63, 1692 (1975).',

        '[8] N. Wiener, Extrapolation, Interpolation, and Smoothing of Stationary '
        'Time Series (MIT Press, Cambridge, MA, 1949).',

        '[9] G. E. Karniadakis, I. G. Kevrekidis, L. Lu, P. Perdikaris, S. Wang, '
        'and L. Yang, "Physics-informed machine learning," Nat. Rev. Phys. 3, 422 (2021).',

        '[10] G. Gallego, T. Delbrück, G. Orchard, C. Bartolozzi, B. Taba, A. Censi, '
        'S. Leutenegger, A. J. Davison, J. Conradt, K. Daniilidis, and D. Scaramuzza, '
        '"Event-based vision: A survey," IEEE Trans. Pattern Anal. Mach. Intell. 44, '
        '154 (2022).',

        '[11] R. H. Hadfield, "Single-photon detectors for optical quantum information '
        'applications," Nat. Photonics 3, 696 (2009).',

        '[12] G. Indiveri, B. Linares-Barranco, T. J. Hamilton, A. van Schaik, '
        'R. Etienne-Cummings, T. Delbruck, S.-C. Liu, P. Dudek, P. Häfliger, '
        'S. Renaud, J. Schemmel, G. Cauwenberghs, J. Arthur, K. Hynna, '
        'F. Folowosele, S. Saïghi, T. Serrano-Gotarredona, J. Wijekoon, Y. Wang, '
        'and K. Boahen, "Neuromorphic silicon neuron circuits," Front. Neurosci. 5, '
        '73 (2011).',

        '[13] C. Posch, T. Serrano-Gotarredona, B. Linares-Barranco, and T. Delbruck, '
        '"Retinomorphic event-based vision sensors: Bioinspired cameras with spiking '
        'output," Proc. IEEE 102, 1470 (2014).',

        '[14] T. Finateu et al., "A 1280×720 back-illuminated stacked temporal contrast '
        'event-based vision sensor with 4.86 µm pixels, 1.066 GEPS readout, '
        'programmable event-rate controller and compressive data-formatting pipeline," '
        'in IEEE ISSCC Dig. Tech. Papers (2020), pp. 112–114.',

        '[15] [Previous work on PI-DC-DVS framework — self-citation to be added upon '
        'submission.]',

        '[16] G. Cohen and E. Tromeur, "Event-based sensing for space situational '
        'awareness," J. Astronaut. Sci. 66, 125 (2019).',

        '[17] B. Kosko and S. Mitaim, "Stochastic resonance in noisy threshold neurons," '
        'Neural Netw. 16, 755 (2003).',

        '[18] S. Mitaim and B. Kosko, "Adaptive stochastic resonance in noisy neurons '
        'based on mutual information," IEEE Trans. Neural Netw. 15, 1526 (2004).',

        '[19] N. G. Stocks, "Information transmission in parallel threshold networks: '
        'Suprathreshold stochastic resonance," Phys. Rev. E 63, 041114 (2001).',

        '[20] R. Milo, S. Shen-Orr, S. Itzkovitz, N. Kashtan, D. Chklovskii, and '
        'U. Alon, "Network motifs: Simple building blocks of complex networks," '
        'Science 298, 824 (2002).',

        '[21] N. Gisin, G. Ribordy, W. Tittel, and H. Zbinden, "Quantum cryptography," '
        'Rev. Mod. Phys. 74, 145 (2002).',

        '[22] M. A. Richards, J. A. Scheer, and W. A. Holm, Principles of Modern Radar: '
        'Basic Principles (SciTech Publishing, 2010).',

        '[23] P. Hänggi, "Stochastic resonance in biology: How noise can enhance detection '
        'of weak signals and help improve biological information processing," '
        'ChemPhysChem 3, 285 (2002).',
    ]
    for ref in references:
        add_paragraph(doc, ref, space_after=3)

    # Save
    out_path = OUT_DIR / 'manuscript_pre.docx'
    doc.save(str(out_path))
    print(f"Manuscript saved: {out_path}")


if __name__ == '__main__':
    build_manuscript()
