"""
Shared helpers for the Blood Pressure Monitoring manuscript generators.

Provides:
  * a Vancouver citation manager that numbers references in order of first
    appearance (so the reference list can never contain orphans and the
    numbering always matches the text);
  * loading of the machine-readable results (results/summary.json) so that
    no numerical result is hard-coded in the manuscript text.
"""

from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results", "summary.json")


def load_summary():
    with open(RESULTS) as f:
        return json.load(f)


class Citations:
    """Assigns Vancouver numbers to references on first use."""

    def __init__(self, refdb: dict):
        self.refdb = refdb
        self.order = []      # keys in order of first appearance

    def cite(self, *keys) -> str:
        nums = []
        for k in keys:
            if k not in self.refdb:
                raise KeyError(f"unknown reference key: {k}")
            if k not in self.order:
                self.order.append(k)
            nums.append(self.order.index(k) + 1)
        # collapse consecutive runs (e.g. 1,2,3 -> 1-3)
        return "{" + _fmt_nums(sorted(set(nums))) + "}"

    def ordered_references(self):
        """Return the reference strings in citation order."""
        return [self.refdb[k] for k in self.order]

    def check_all_cited(self):
        missing = [k for k in self.refdb if k not in self.order]
        return missing


def _fmt_nums(nums):
    if not nums:
        return ""
    runs = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        runs.append((start, prev))
        start = prev = n
    runs.append((start, prev))
    parts = []
    for a, b in runs:
        parts.append(f"{a}" if a == b else f"{a}\u2013{b}")
    return ",".join(parts)


# ----------------------------------------------------------------------
# Vancouver reference database (superscript-numbered in order of appearance)
# ----------------------------------------------------------------------
REFDB = {
    "saugel2020": "Saugel B, Kouz K, Meidert AS, Schulte-Uentrop L, Romagnoli S. How to measure blood pressure using an arterial catheter: a systematic 5-step approach. Crit Care. 2020;24:172.",
    "saugelsessler2021": "Saugel B, Sessler DI. Perioperative blood pressure management. Anesthesiology. 2021;134:250\u201361.",
    "gupta2025": "Gupta D, Jain A, Ismaeil M. Zero arterial catheters with every change in the height difference of pressure transducer and catheter insertion site. Ann Card Anaesth. 2025;28:205.",
    "mark1998": "Mark JB. Atlas of Cardiovascular Monitoring. New York: Churchill Livingstone; 1998.",
    "mcghee2002": "McGhee BH, Bridges MEJ. Monitoring arterial blood pressure: what you may not know. Crit Care Nurse. 2002;22:60\u201379.",
    "blandaltman1986": "Bland JM, Altman DG. Statistical methods for assessing agreement between two methods of clinical measurement. Lancet. 1986;327:307\u201310.",
    "blandaltman1999": "Bland JM, Altman DG. Measuring agreement in method comparison studies. Stat Methods Med Res. 1999;8:135\u201360.",
    "critchley1999": "Critchley LAH, Critchley JAJH. A meta-analysis of studies using bias and precision statistics to compare cardiac output measurement techniques. J Clin Monit Comput. 1999;15:85\u201391.",
    "cecconi2009": "Cecconi M, Rhodes A, Poloniecki J, Della Rocca G, Grounds RM. Bench-to-bedside review: the importance of the precision of the reference technique in method comparison studies. Crit Care. 2009;13:201.",
    "lin1989": "Lin LI-K. A concordance correlation coefficient to evaluate reproducibility. Biometrics. 1989;45:255\u201368.",
    "lin2000": "Lin LI-K. A note on the concordance correlation coefficient. Biometrics. 2000;56:324\u20135.",
    "mcbride2005": "McBride GB. A proposal for strength-of-agreement criteria for Lin\u2019s concordance correlation coefficient. NIWA Client Report HAM2005-062; 2005.",
    "gardner1981": "Gardner RM. Direct blood pressure measurement\u2014dynamic response requirements. Anesthesiology. 1981;54:227\u201336.",
    "romagnoli2014": "Romagnoli S, Ricci Z, Quattrone D, et al. Accuracy of invasive arterial pressure monitoring in cardiovascular patients: an observational study. Crit Care. 2014;18:644.",
    "kleinman1992": "Kleinman B, Powell S, Kumar P, Gardner RM. The fast flush test measures the dynamic response of the entire blood pressure monitoring system. Anesthesiology. 1992;77:1215\u201320.",
    "linnet1990": "Linnet K. Estimation of the linear relationship between the measurements of two methods with proportional errors. Stat Med. 1990;9:1463\u201373.",
    "passingbablok1983": "Passing H, Bablok W. A new biometrical procedure for testing the equality of measurements from two different analytical methods. J Clin Chem Clin Biochem. 1983;21:709\u201320.",
    "atkinson1997": "Atkinson G, Nevill A. Comment on the use of concordance correlation to assess the agreement between two variables. Biometrics. 1997;53:775\u20137.",
    "barnhart2007": "Barnhart HX, Haber MJ, Lin LI. An overview on assessing agreement with continuous measurements. J Biopharm Stat. 2007;17:529\u201369.",
    "hasenkamp2012": "Hasenkamp W, Theumer T, Nolte J, Aschenbrenner L, Dietzel A, B\u00fcttgenbach S. Polyimide/SU-8 catheter-tip MEMS gauge pressure sensor. Biomed Microdevices. 2012;14:819\u201328.",
    "song2020": "Song P, Ma Z, Ma J, et al. Recent progress of miniature MEMS pressure sensors. Micromachines. 2020;11:56.",
    "kang2022": "Kang Y, Ge C, Hu Y, et al. Development of a flexible integrated self-calibrating MEMS pressure sensor using a liquid-to-vapor phase change. Sensors. 2022;22:9737.",
    "barlian2009": "Barlian AA, Park W-T, Mallon JR, Rastegar AJ, Pruitt BL. Review: semiconductor piezoresistance for microsystems. Proc IEEE. 2009;97:513\u201352.",
    "scalia2023": "Scalia A, Ghafari C, Navarre W, et al. High fidelity pressure wires provide accurate validation of non-invasive central blood pressure and pulse wave velocity measurements. Biomedicines. 2023;11:1235.",
    "odor2017": "Odor PM, Bampoe S, Cecconi M. Cardiac output monitoring: validation studies\u2014how results should be presented. Curr Anesthesiol Rep. 2017;7:410\u201315.",
    "kim2014": "Kim S-H, Lilot M, Sidhu KS, et al. Accuracy and precision of continuous noninvasive arterial pressure monitoring compared with invasive arterial pressure. Anesthesiology. 2014;120:1080\u201397.",
    "joosten2017": "Joosten A, Desebbe O, Suehiro K, et al. Accuracy and precision of non-invasive cardiac output monitoring devices in perioperative medicine: a systematic review and meta-analysis. Br J Anaesth. 2017;118:298\u2013310.",
    "chatterjee2009": "Chatterjee K. The Swan\u2013Ganz catheters: past, present, and future. Circulation. 2009;119:147\u201352.",
    "ameloot2015": "Ameloot K, Palmers PJ, Malbrain MLNG. The accuracy of noninvasive cardiac output and pressure measurements with finger cuff: a concise review. Curr Opin Crit Care. 2015;21:232\u20139.",
    "squara2007": "Squara P, Denjean D, Estagnasie P, Brusset A, Dib JC, Dubois C. Noninvasive cardiac output monitoring (NICOM): a clinical validation. Intensive Care Med. 2007;33:1191\u20134.",
    "manecke2005": "Manecke GR. Edwards FloTrac sensor and Vigileo monitor: easy, accurate, reliable cardiac output assessment using the arterial pulse wave. Expert Rev Med Devices. 2005;2:523\u20137.",
}
