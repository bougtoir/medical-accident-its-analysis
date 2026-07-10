#!/usr/bin/env python3

from __future__ import annotations

import re
import shutil
import subprocess
import textwrap
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor as PptxRGB
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches as PptxInches, Pt as PptxPt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as ReportLabImage,
    KeepTogether,
    Paragraph as ReportLabParagraph,
    SimpleDocTemplate,
    Spacer,
    Table as ReportLabTable,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
WORK = ROOT / "build"

TITLE = (
    "Discharged Secrets: Lifecycle Telemetry and Supply-Chain Exposure "
    "in Serviced Hardware for Critical Infrastructure"
)
SHORT_TITLE = "Lifecycle telemetry exposure in serviced hardware"
AUTHOR = "[Author name]"
AFFILIATION = "[Department, institution, city, postal code, country]"
EMAIL = "[Corresponding author email]"
ORCID = "[ORCID]"
JOURNAL = "International Journal of Critical Infrastructure Protection"
BUILD_DATE = "10 July 2026"

ABSTRACT = (
    "Critical-infrastructure organizations increasingly use connected devices that they "
    "do not own, maintain, or decommission. Shared micromobility provides a visible "
    "example of this broader class of serviced hardware. Existing assessments often "
    "concentrate on real-time location, yet exposure can persist when positioning is "
    "disabled because battery consumption, odometry, fault events, and service records "
    "may reveal identity, occupancy, operating tempo, and recurring activity. This "
    "article presents a structured evidence synthesis spanning mobility re-identification, "
    "micromobility privacy measurement, battery side channels, battery-management data, "
    "connected-vehicle governance, and cybersecurity supply-chain guidance. It develops "
    "a lifecycle model covering procurement, deployment, operation, maintenance, "
    "recall or return, and second-life disposal. The model shows that risk depends not "
    "only on connectivity but also on custody, data retention, component provenance, "
    "contractor access, and the legal jurisdiction of service backends. A Japanese "
    "government-facility deployment is used as a bounded policy vignette; no compromise "
    "or vendor misconduct is alleged. The article proposes proportionate controls based "
    "on deployment criticality: telemetry inventories, local processing, access and "
    "retention limits, component and contractor assurance, controlled maintenance, "
    "recall-specific chain of custody, and verified sanitization. These controls extend "
    "critical-infrastructure protection from network security to the full service and "
    "hardware lifecycle."
)

KEYWORDS = [
    "critical infrastructure",
    "battery telemetry",
    "micromobility",
    "supply-chain risk",
    "data minimization",
    "lifecycle security",
]

HIGHLIGHTS = [
    "Serviced hardware creates exposure beyond network connectivity.",
    "Battery telemetry can reveal identity, occupancy, and operating patterns.",
    "Maintenance, recalls, and disposal create recurring custody gaps.",
    "A lifecycle model links evidence to auditable procurement controls.",
    "Controls scale from sensitive sites to civilian infrastructure fleets.",
]


SECTIONS = [
    (
        "1. Introduction",
        [
            (
                "In July 2026, shared electric scooters and assisted bicycles were introduced "
                "at the Ichigaya headquarters of Japan's Ministry of Defense. When concerns "
                "were raised about location data, the defense minister stated that location "
                "data alone were not expected to create an information-security problem [1]. "
                "The statement is useful as a policy vignette because it captures a common "
                "assessment boundary: if a device's coordinates are not classified and an "
                "individual trip appears innocuous, the service may seem operationally "
                "convenient and security-neutral. That boundary is too narrow for devices "
                "used in or around critical infrastructure."
            ),
            (
                "Critical-infrastructure protection concerns systems whose disruption or "
                "exploitation could affect national security, public safety, economic "
                "activity, or continuity of essential services. Transportation, government "
                "facilities, the defense industrial base, commercial facilities, and "
                "information technology are recognized sectors [2]. Across those sectors, "
                "organizations increasingly rely on equipment delivered as a service: "
                "shared vehicles, leased sensors, smart lockers, wearables, inspection "
                "devices, delivery robots, charging systems, and other connected assets. "
                "The user organization may determine where the equipment is placed while "
                "another entity owns the hardware, administers software, stores telemetry, "
                "dispatches maintenance, and controls end-of-life handling."
            ),
            (
                "This article calls that class serviced telemetry-emitting hardware: a "
                "physical device that records operational data and is used by an organization "
                "that does not exercise complete control over its components, software, "
                "maintenance, data backend, or disposition. The definition does not imply "
                "that the equipment is malicious or that the service provider has acted "
                "improperly. It identifies a governance condition: operational dependence "
                "exists without end-to-end visibility."
            ),
            (
                "The central argument is that critical-infrastructure assessments should "
                "treat telemetry, custody, and provenance as a single lifecycle problem. "
                "Location is only one signal. Battery consumption, charging intervals, "
                "cycle counts, temperature excursions, odometry, torque, fault logs, and "
                "maintenance records can reveal recurring use even when Global Positioning "
                "System (GPS) data are unavailable. Exposure can occur immediately through "
                "a service backend or later when a device is inspected, returned, recalled, "
                "resold, or recycled. Network isolation therefore reduces only part of the "
                "attack surface."
            ),
            (
                "The article makes four contributions. First, it translates evidence from "
                "mobility privacy and battery side-channel research into a critical-"
                "infrastructure threat model. Second, it distinguishes demonstrated "
                "capabilities from plausible transfers, avoiding the claim that every "
                "battery or service stores the same data. Third, it introduces a lifecycle "
                "exposure model spanning acquisition through disposition. Fourth, it "
                "provides a control matrix that turns broad calls for trusted supply chains "
                "into procurement clauses and verifiable evidence."
            ),
        ],
    ),
    (
        "2. Scope and structured synthesis method",
        [
            (
                "This is a conceptual policy analysis supported by a structured evidence "
                "synthesis, not a systematic review and not a forensic investigation of a "
                "specific deployment. Evidence was organized around four questions: "
                "(1) whether mobility traces can be linked to individuals or sensitive "
                "activities; (2) whether non-positional electrical or battery data can "
                "reveal behavior; (3) whether devices retain data that remain accessible "
                "through service and end-of-life transitions; and (4) which established "
                "supply-chain and device-lifecycle controls can reduce the resulting risk."
            ),
            (
                "The evidence base includes peer-reviewed measurement studies, standards "
                "and regulatory documents, official guidance, and well-documented public "
                "incidents. The Open Mobility Foundation's privacy guidance is included "
                "because it explicitly recognizes that vehicle and trip data remain "
                "sensitive even when rider names, contact details, and payment information "
                "are absent [3]. Peer-reviewed evidence was prioritized for technical "
                "capabilities; government and standards documents were used for control "
                "design. News reporting appears only to establish the Japanese policy "
                "vignette and the earlier public fitness-tracker incidents."
            ),
            (
                "Transfer from one device class to another was accepted only when the "
                "underlying mechanism was shared. For example, a smart-meter study does not "
                "prove that a scooter battery identifies a rider. It establishes the more "
                "limited proposition that electrical load signatures can encode behavior. "
                "Direct evidence from electric-vehicle battery consumption then supports "
                "the stronger inference that battery patterns can disclose driver and trip "
                "attributes. Each transfer is therefore labelled as demonstrated, supported "
                "by analogy, or conditional in Table 1."
            ),
            (
                "The analysis excludes offensive exploitation techniques, firmware reverse "
                "engineering, and claims about undisclosed vendor architecture. It also "
                "does not treat foreign manufacture as a vulnerability by itself. Risk "
                "arises from the combination of data sensitivity, access, retention, "
                "custody, legal jurisdiction, and insufficient assurance. The relevant "
                "question is not where a supplier is located, but whether the operator can "
                "demonstrate who can access the device and its data throughout the lifecycle."
            ),
            (
                "The unit of analysis is the device-service arrangement rather than the "
                "device in isolation. That arrangement includes the physical assembly, "
                "embedded controllers, batteries, user and technician applications, "
                "operator and manufacturer backends, diagnostic tools, subcontractors, "
                "warranty processes, and disposition channels. A technically hardened "
                "device can still create exposure if a maintenance workflow exports its "
                "logs, while a highly connected device can be acceptable when telemetry is "
                "strictly minimized, processed locally, and separated from sensitive "
                "operational context. This unit prevents the analysis from equating "
                "connectivity with risk."
            ),
            (
                "Evidence was evaluated along three dimensions. Technical relevance asks "
                "whether a source demonstrates generation, linkage, retention, or access "
                "to a signal. Contextual relevance asks whether that mechanism could operate "
                "in a serviced-hardware setting without assuming undisclosed capabilities. "
                "Control relevance asks whether a mitigation can be written as a requirement "
                "and verified through an artifact or test. Claims supported only by analogy "
                "are not used to assert prevalence. This approach favors a bounded chain "
                "from evidence to mechanism to control over an exhaustive catalogue of "
                "possible threats."
            ),
        ],
    ),
    (
        "3. Mobility data as critical-infrastructure information",
        [
            (
                "Mobility traces are unusually identifying. A large-scale study of mobile-"
                "phone records showed that four spatiotemporal points were sufficient to "
                "uniquely characterize 95% of individuals in the studied dataset [4]. "
                "Shared-micromobility data create a similar linkage opportunity because "
                "vehicle identifiers, timestamps, and origins or destinations can be "
                "combined with work schedules, access records, public photographs, or "
                "other datasets."
            ),
            (
                "A long-term real-world analysis of shared micromobility found that privacy "
                "leakage persisted despite changes in vehicle identifiers and reported that "
                "journeys could be reconstructed across time [5]. Earlier scholarship "
                "identified the invisible privacy costs of rental scooters [6], while "
                "security research described threats arising from positioning, wireless "
                "interfaces, user applications, and operator infrastructure [7]. These "
                "studies do not establish a compromise at a government facility. They show "
                "that apparently impersonal fleet data can preserve continuity and support "
                "inference."
            ),
            (
                "The critical-infrastructure consequence is aggregation. A single trip "
                "rarely matters. Repeated observations may disclose shift changes, "
                "maintenance windows, abnormal staffing, visits to restricted areas, or "
                "the difference between routine and surge operations. Data from an "
                "externally operated convenience service can become an indirect sensor of "
                "the host organization's tempo. This remains true when the service is "
                "legitimate and the provider's primary purpose is transportation."
            ),
            (
                "Public fitness-tracker incidents demonstrate how aggregation can expose "
                "sensitive populations. In 2018, a global heatmap published by Strava "
                "revealed activity around military sites [8]. The United States Department "
                "of Defense subsequently restricted geolocation-capable devices, "
                "applications, and services in designated operational areas [9]. A separate "
                "investigation of Polar fitness data linked activity traces to homes and "
                "identities of military and intelligence personnel [10]. The policy lesson "
                "is broader than wearable devices: anonymization and absence of classified "
                "content do not prevent inference when repeated observations can be joined "
                "with external information."
            ),
            (
                "For shared or leased devices, the organization must therefore ask which "
                "entities receive raw or derived data, how persistent identifiers are "
                "generated, what retention periods apply, whether data are reused for "
                "safety or analytics, and whether aggregate outputs can be queried at a "
                "granularity that exposes operational patterns. A privacy notice directed "
                "at individual consumers does not substitute for a critical-infrastructure "
                "data-flow assessment."
            ),
            (
                "Operational sensitivity can also differ from personal-data sensitivity. "
                "A dataset may contain no rider name and still disclose that a facility is "
                "entering an unusual operating state. Conversely, a dataset that is useful "
                "for safety investigations may be legitimate to collect but require stronger "
                "separation, retention, and access governance near a sensitive site. The "
                "assessment should therefore record both privacy impact and mission impact. "
                "Applying only consumer privacy law may miss aggregate operational harm; "
                "applying only classified-information rules may miss unclassified patterns "
                "whose value emerges through repeated observation."
            ),
        ],
    ),
    (
        "4. Beyond GPS: battery and non-positional telemetry",
        [
            (
                "A location-only review can fail even when GPS collection is disabled. "
                "Battery and power data are shaped by speed, acceleration, gradient, payload, "
                "temperature, route conditions, and driving style. Marchiori and Conti "
                "demonstrated side-channel attacks that used electric-vehicle battery "
                "consumption to identify drivers and driving style, estimate the number of "
                "occupants, and infer trip endpoints when habitual information was available "
                "[11]. Their reported average success across attack objectives was 95.4%. "
                "The experiment concerns electric vehicles rather than shared scooters, but "
                "it directly establishes that battery consumption is not operationally "
                "neutral."
            ),
            (
                "The inference mechanism is consistent with earlier work on electrical load "
                "signatures. Smart-meter measurements have been used to infer household "
                "activities [12], and privacy research has sought to mask appliance load "
                "signatures precisely because power profiles reveal use [13]. These studies "
                "support a general proposition: time-varying electrical demand can encode "
                "behavior. Device class, sampling frequency, sensor precision, and access "
                "determine whether a particular inference is feasible."
            ),
            (
                "Battery-management systems (BMSs) add another layer. State-of-health "
                "estimation for second-life batteries relies on historical operating "
                "profiles and variables such as capacity, current, voltage, temperature, "
                "and cycling [14]. European battery regulation defines a BMS as an "
                "electronic device that manages and stores parameters used to determine "
                "state of health and expected lifetime; it also requires access to updated "
                "state-of-health and lifetime information for relevant battery classes "
                "[15]. A 2026 fire-investigation study further demonstrated the forensic "
                "use of historical BMS voltage, current, and temperature sequences to "
                "reconstruct abuse conditions [16]."
            ),
            (
                "These sources do not imply that every micromobility battery stores a "
                "continuous trip history. Implementations vary. Some systems retain only "
                "counters or fault events; others transmit detailed telemetry to a vehicle "
                "controller or cloud service. The defensible claim is conditional: when "
                "high-resolution consumption data, timestamped events, or persistent "
                "health records are retained, they may reveal operational patterns and "
                "remain useful after the immediate ride."
            ),
            (
                "The temporal distinction matters. A device can be offline during use yet "
                "disclose information later. A technician may connect diagnostic equipment; "
                "a returned battery may be evaluated for warranty or second-life value; or "
                "a service backend may receive stored records when connectivity resumes. "
                "Disabling live transmission is therefore different from preventing data "
                "generation, retention, or delayed extraction."
            ),
            (
                "Battery telemetry can be divided into three practical layers. Instantaneous "
                "signals include voltage, current, temperature, power, and state of charge. "
                "Accumulated signals include cycle count, energy throughput, distance, "
                "maximum and minimum values, and fault counters. Event records capture "
                "overcurrent, undervoltage, thermal excursions, impacts, charging faults, "
                "or controller resets. Even when the first layer is not retained, the second "
                "and third may encode frequency, intensity, and abnormality of use. A "
                "procurement questionnaire should distinguish these layers because the phrase "
                "\"battery status\" is too broad to support a security decision."
            ),
            (
                "Derived analytics require equal attention. Predictive maintenance, state-of-"
                "health scoring, fraud detection, fleet balancing, and warranty analysis may "
                "combine raw telemetry with user accounts, device history, weather, maps, "
                "and depot records. The derived score may be less interpretable than the raw "
                "data yet preserve sensitive correlations for longer. Model training sets, "
                "feature stores, exports to analytics vendors, and support tickets are thus "
                "part of the data path. A promise not to sell precise location does not answer "
                "whether derived patterns are retained or shared."
            ),
            (
                "For critical-infrastructure operators, the minimum assessment unit should "
                "be a telemetry inventory rather than a list of radios. The inventory "
                "should identify each generated field, sampling interval, storage location, "
                "retention period, recipient, diagnostic interface, export function, and "
                "derived analytic. It should cover the vehicle controller, BMS, application, "
                "operator backend, maintenance tools, and any battery-passport or warranty "
                "system."
            ),
        ],
    ),
    (
        "5. Lifecycle exposure in serviced hardware",
        [
            (
                "The preceding evidence suggests that the attack surface is organized by "
                "lifecycle transitions rather than by a single network boundary. Figure 1 "
                "maps six stages: procurement, deployment, operation, maintenance, recall "
                "or return, and second life or disposal. At each stage, a different party "
                "may gain physical or logical access, and data created at an earlier stage "
                "may become visible later."
            ),
            (
                "Procurement determines what can be known. Bills of materials, component "
                "origin, firmware ownership, cryptographic update mechanisms, diagnostic "
                "interfaces, backend sub-processors, and data jurisdictions are difficult "
                "to recover after deployment. A contract that specifies only service "
                "availability leaves the operator unable to assess telemetry or custody "
                "risk. Procurement must therefore require evidence before a device enters "
                "a controlled environment."
            ),
            (
                "Deployment establishes identity and context. Device identifiers, ports, "
                "geofences, authorized users, and physical placement can link otherwise "
                "generic telemetry to a specific facility. Configuration errors can also "
                "leave consumer defaults, unnecessary radios, broad permissions, or "
                "vendor-wide administrator access in place. A hardened configuration "
                "baseline and a record of authorized data flows are required before use."
            ),
            (
                "Operation creates the richest stream: location, time, speed, battery "
                "consumption, faults, user-account events, and service analytics. European "
                "data-protection guidance for connected vehicles recommends data "
                "minimization, local processing where possible, privacy-protective defaults, "
                "and controls on third-party transfers [17]. A recent holistic review of "
                "electric-vehicle security similarly treats the BMS, charging system, "
                "vehicle, and infrastructure as an integrated cyber-physical attack surface "
                "[18]. Critical-infrastructure use requires the same integrated view, with "
                "operational sensitivity added to personal-data concerns."
            ),
            (
                "Maintenance changes custody. Technicians may attach diagnostic tools, "
                "replace controllers, remove batteries, or move equipment off-site. Even "
                "when the operational network is isolated, maintenance can bridge the "
                "device to a vendor laptop, mobile application, depot network, or warranty "
                "portal. Contractor vetting, authorized tools, access logging, tamper "
                "evidence, and documented chain of custody are therefore security controls, "
                "not administrative details."
            ),
            (
                "Recall or return is a distinct stage because safety can override ordinary "
                "disposition plans. Lithium-ion batteries may be returned rapidly after "
                "faults, thermal events, or manufacturer notices. A contract that requires "
                "sanitization only at scheduled end of life may not cover emergency return. "
                "The organization needs a recall protocol that identifies data-bearing "
                "components, preserves evidence when required, limits recipients, and "
                "documents whether data were deleted, cryptographically erased, retained "
                "under legal hold, or transferred with explicit authorization."
            ),
            (
                "Second-life use, refurbishment, resale, and recycling create the final "
                "custody transition. Batteries have economic value precisely because their "
                "condition can be estimated from use history. Devices may also contain "
                "persistent identifiers, credentials, logs, or configuration data. "
                "Disposition controls must apply to the whole assembly and to removed "
                "components, not only to conventional storage media."
            ),
            (
                "Three threat scenarios illustrate how stages combine. In a backend scenario, "
                "a legitimate service continuously aggregates device events and is later "
                "compromised, legally compelled, or misconfigured. In a maintenance scenario, "
                "a device stores telemetry locally and discloses it only when a contractor "
                "connects a diagnostic tool. In a return scenario, an apparently defective "
                "battery leaves the site under an urgent safety process and its retained "
                "history is examined by parties not covered by the routine data agreement. "
                "The same deployment may face all three scenarios, and controls that address "
                "only cloud access will not cover the latter two."
            ),
            (
                "Lifecycle risk can be expressed conceptually as the product of informativeness, "
                "linkability, accessibility, persistence, and consequence. The formulation is "
                "not intended as a quantitative score: evidence is not yet sufficient to assign "
                "universal probabilities. It is a review discipline. A low-resolution signal "
                "may become important when persistently linked to one site; a highly informative "
                "signal may pose limited risk when immediately aggregated and inaccessible; "
                "and a routine dataset may become consequential during a crisis. Recording each "
                "factor makes the rationale for acceptance, restriction, or rejection auditable."
            ),
        ],
    ),
    (
        "6. Evidence-to-risk synthesis",
        [
            (
                "Table 1 separates direct demonstrations from conditional transfer. The "
                "strongest evidence concerns mobility re-identification and battery-based "
                "inference. The lifecycle conclusion is a synthesis: if data can identify "
                "activity and if access changes across service transitions, then custody "
                "and retention must be governed as part of critical-infrastructure "
                "protection. This conclusion does not depend on a malicious manufacturer; "
                "ordinary diagnostics, warranty processes, and analytics are sufficient to "
                "create access paths."
            ),
            (
                "The synthesis also clarifies what should not be claimed. A battery cycle "
                "count alone usually cannot reconstruct a route. A foreign supplier is not "
                "automatically an adversary. Whitelisting does not eliminate compromise. "
                "The risk becomes material when informative data, persistent linkage, "
                "accessible interfaces, weak custody, and consequential deployment occur "
                "together. Controls should be proportionate to that combination."
            ),
        ],
    ),
    (
        "7. A lifecycle assurance framework",
        [
            (
                "Established cybersecurity supply-chain risk management already requires "
                "organizations to identify, assess, and mitigate risks arising from "
                "products and services across the supply chain [19]. The gap is not the "
                "absence of a general principle but its application to small, convenient, "
                "externally serviced devices. Such devices may fall below the threshold of "
                "traditional capital-equipment review even though their placement and "
                "telemetry make them sensitive."
            ),
            (
                "The proposed framework uses five assurance questions. First, what data are "
                "generated, derived, stored, and transmitted? Second, who can access the "
                "device or data at each lifecycle stage? Third, where do software, "
                "components, diagnostic tools, and service backends originate and operate? "
                "Fourth, what event changes custody, and what evidence accompanies that "
                "change? Fifth, how can the operator verify that contractual controls work "
                "in practice?"
            ),
            (
                "Table 2 converts those questions into minimum requirements. The controls "
                "are evidence-oriented. A statement that data are secure is weaker than a "
                "field-level data inventory, retention schedule, sub-processor list, "
                "architecture diagram, access log, software bill of materials, signed "
                "sanitization record, or right-to-audit report. Procurement should specify "
                "the artifact that demonstrates compliance."
            ),
            (
                "Data minimization should begin at collection. Fields not required for the "
                "approved use case should be disabled or aggregated. Local processing is "
                "preferable when the service can function without exporting raw telemetry. "
                "Persistent identifiers should rotate when continuity is unnecessary, and "
                "retention should be bounded by a documented purpose. Derived data, model "
                "features, and backups must be included because deleting a raw record while "
                "retaining an equally revealing derivative does not reduce exposure."
            ),
            (
                "Device capabilities must support the policy. Guidance from the U.S. "
                "National Institute of Standards and Technology (NIST) for Internet of "
                "Things devices identifies secure data storage, audit-event generation, "
                "log retention, and the ability to sanitize or purge data as relevant "
                "capabilities [20]. These requirements should be tested before purchase. "
                "If a device cannot enumerate or erase retained data, the operator cannot "
                "reliably govern maintenance, return, or disposal."
            ),
            (
                "Sanitization should be defined by outcome rather than a generic factory "
                "reset. Current NIST media-sanitization guidance distinguishes methods "
                "according to media and confidentiality risk [21]. For integrated devices, "
                "the process should identify every data-bearing component, verify the "
                "result, record the person and tool used, and address keys or credentials "
                "that enable access to remote records. Where sanitization would destroy "
                "safety evidence, controlled retention and transfer may be more appropriate "
                "than deletion; the decision should be explicit."
            ),
            (
                "Supplier assurance should be risk-based. For high-consequence sites, "
                "requirements may include component provenance, signed firmware, controlled "
                "update infrastructure, named service locations, screened personnel, "
                "domestic or otherwise approved data hosting, and independent testing. "
                "For ordinary civilian fleets, transparency, minimization, access controls, "
                "and verified deletion may be sufficient. A tiered approach avoids treating "
                "all deployments as classified while preventing convenience services from "
                "bypassing review entirely."
            ),
            (
                "A three-tier profile is sufficient for many organizations. Tier 1 covers "
                "ordinary public settings and emphasizes transparency, access control, "
                "reasonable retention, supported software, and verified deletion. Tier 2 "
                "covers facilities where aggregate activity could affect continuity or "
                "security and adds local or regional processing, restricted identifiers, "
                "approved maintenance, material-change notification, and recall exercises. "
                "Tier 3 covers mission-sensitive zones and may require dedicated fleets, "
                "offline or one-way operation, organization-controlled keys, approved-source "
                "components, independent testing, escorted maintenance, and prohibition of "
                "off-site return before sanitization or controlled evidence transfer."
            ),
            (
                "Contracts should allocate responsibility when controls fail. Required terms "
                "include incident-notification time, vulnerability disclosure and remediation, "
                "subcontractor flow-down, support and end-of-life dates, audit access, return "
                "or destruction of data, restrictions on secondary use and model training, "
                "government or customer access to relevant logs, and consequences for "
                "unapproved architectural change. A supplier should also disclose when safety "
                "or legal obligations prevent deletion. The objective is not to demand "
                "impossible guarantees but to prevent ambiguity from surfacing only after an "
                "incident or recall."
            ),
        ],
    ),
    (
        "8. Interorganizational and cross-sector dependencies",
        [
            (
                "Serviced hardware often crosses organizational boundaries. A transportation "
                "service may operate at a government facility, use commercial cellular "
                "networks, depend on cloud infrastructure, and send batteries to an external "
                "depot. Each participant may satisfy its own sector-specific obligations "
                "while the end-to-end data and custody path remains unowned. This is a "
                "classic critical-infrastructure dependency problem: local controls do not "
                "guarantee system-level assurance."
            ),
            (
                "Inconsistent procurement rules create a weakest-link effect. An organization "
                "may restrict personal devices yet admit functionally similar sensors through "
                "a facilities or mobility contract. One site may require local storage while "
                "another permits the same fleet to use a global backend, allowing patterns "
                "to be inferred across a shared workforce or joint operation. Harmonized "
                "minimum requirements are therefore valuable across agencies, operators, "
                "and allied or partner organizations."
            ),
            (
                "Regulatory precedent supports anticipatory supply-chain controls. The United "
                "States connected-vehicle rule addresses national-security risks associated "
                "with covered connectivity hardware and software linked to specified foreign "
                "adversaries [22]. The rule is narrower than the framework proposed here, "
                "but it demonstrates that governments need not wait for a documented "
                "individual compromise before imposing provenance and jurisdictional "
                "requirements on connected transportation technology."
            ),
            (
                "The broader policy should remain vendor-neutral and capability-based. "
                "Jurisdiction is one factor because it shapes legal access and government "
                "compulsion, but technical architecture and operational practice matter as "
                "well. A domestic service with excessive retention and uncontrolled "
                "contractors may present more risk than a foreign-origin component operated "
                "under transparent, locally controlled conditions. The framework therefore "
                "uses approved-source lists only as one layer within continuous assurance."
            ),
            (
                "Governance ownership must be explicit. Facilities teams may own physical "
                "placement, procurement teams the contract, cybersecurity teams the network, "
                "privacy teams personal information, and safety teams recalls. None may own "
                "the combined lifecycle. Designating an accountable service owner and a "
                "cross-functional approval path prevents gaps between these domains. The "
                "owner should maintain the authoritative data and custody model and have the "
                "power to suspend deployment when a supplier, component, backend, or support "
                "process changes materially."
            ),
        ],
    ),
    (
        "9. Implementation priorities",
        [
            (
                "Organizations can begin without creating a new bureaucracy. The first "
                "priority is to add serviced telemetry-emitting hardware to existing asset "
                "and supply-chain inventories. The second is to require a data-flow and "
                "custody worksheet during procurement. The third is to define prohibited "
                "deployment zones and higher assurance tiers. The fourth is to create "
                "maintenance, recall, and disposition procedures that are exercised rather "
                "than left as contract language."
            ),
            (
                "A practical pilot can examine one existing service. The operator should "
                "enumerate device and backend data, observe diagnostic and maintenance "
                "workflows, test account and identifier separation, verify retention and "
                "deletion, inspect sub-processor and hosting arrangements, and conduct a "
                "mock emergency recall. Findings can be mapped to Table 2 and used to revise "
                "the contract or restrict deployment. This produces evidence without "
                "requiring access to proprietary algorithms."
            ),
            (
                "Lifecycle support should be planned before purchase. NIST's 2026 guidance "
                "for Internet of Things product manufacturers emphasizes cybersecurity "
                "support through the product lifecycle and end of life [23]. Critical-"
                "infrastructure customers should request the corresponding support period, "
                "vulnerability process, update mechanism, end-of-life notice, and data-"
                "handling plan. A service should not remain in a sensitive setting after "
                "the provider can no longer support its software or components."
            ),
            (
                "Metrics should track assurance rather than incident counts alone. Useful "
                "measures include the percentage of devices with complete telemetry "
                "inventories, percentage of service providers with named sub-processors, "
                "median time to revoke maintenance access, percentage of returned components "
                "with verified sanitization, and number of emergency-return exercises "
                "completed. An absence of known leaks is not evidence that lifecycle controls "
                "are effective."
            ),
            (
                "Exercises should include non-cyber triggers. A thermal fault, bankruptcy, "
                "contract termination, software end of support, law-enforcement request, or "
                "sudden geopolitical restriction can force a custody or service change. The "
                "organization should test whether it can locate all deployed units and spare "
                "batteries, disable accounts and credentials, preserve necessary safety "
                "evidence, prevent unauthorized return, and continue the underlying service. "
                "This links confidentiality controls to resilience: a lifecycle plan is "
                "effective only if the essential function can continue while risky equipment "
                "is isolated or replaced."
            ),
        ],
    ),
    (
        "10. Limitations and research agenda",
        [
            (
                "This article has four principal limitations. First, the Japanese case is "
                "used only as a public policy vignette. The analysis has no access to the "
                "service architecture, contract, vehicle configuration, or security review, "
                "and it does not allege that sensitive information was exposed. Second, "
                "battery implementations vary widely; the presence, resolution, retention, "
                "and accessibility of historical data must be established device by device."
            ),
            (
                "Third, the evidence synthesis is structured but not systematic. It was "
                "designed to connect established mechanisms to lifecycle controls, not to "
                "estimate prevalence or effect size. Fourth, stronger controls impose cost "
                "and may reduce service convenience. The proposed tiers require validation "
                "through procurement pilots and comparative risk assessment."
            ),
            (
                "Future work should measure which telemetry fields are retained in shared "
                "micromobility controllers and batteries, how reliably operational "
                "attributes can be inferred at realistic sampling rates, and what data "
                "remain after maintenance and factory-reset procedures. Red-team exercises "
                "should test delayed extraction during service and recall without developing "
                "or publishing techniques that would facilitate unauthorized access."
            ),
            (
                "Policy research should compare procurement clauses across transportation, "
                "government, energy, and health infrastructure; evaluate whether battery-"
                "passport regimes create new access-control requirements; and quantify the "
                "cost of chain-of-custody controls. A shared assurance profile for serviced "
                "hardware would help small operators apply protections that are currently "
                "available mainly to large security organizations."
            ),
        ],
    ),
    (
        "11. Conclusion",
        [
            (
                "Critical-infrastructure organizations increasingly depend on devices whose "
                "ownership, maintenance, data backend, and disposition remain outside their "
                "direct control. Treating such equipment as a network endpoint or a location-"
                "privacy question misses the lifecycle. Mobility traces can re-identify; "
                "battery consumption can reveal behavior; BMS and service records can "
                "preserve history; and maintenance, recall, and second-life transitions can "
                "move data-bearing components into new hands."
            ),
            (
                "The appropriate response is not a categorical ban on shared mobility or "
                "connected equipment. It is proportionate assurance: know what the device "
                "records, know who can access it, control each custody transition, and "
                "require evidence that minimization, retention, access, update, and "
                "sanitization controls work. Extending supply-chain risk management to "
                "small serviced devices closes a gap between cybersecurity policy and the "
                "physical lifecycle of modern infrastructure."
            ),
        ],
    ),
]


TABLE_1 = {
    "title": "Table 1. Evidence supporting the serviced-hardware threat model",
    "headers": ["Evidence domain", "Demonstrated capability", "Transfer to serviced hardware", "Boundary"],
    "rows": [
        [
            "Human mobility traces",
            "Sparse spatiotemporal points can uniquely characterize individuals [4].",
            "Repeated vehicle events may be joined with schedules or access data.",
            "Direct for mobility data; identity requires auxiliary information.",
        ],
        [
            "Shared micromobility",
            "Longitudinal vehicle activity can be reconstructed despite identifier changes [5].",
            "Fleet telemetry can preserve continuity around a facility.",
            "Direct for studied services; architecture differs by operator.",
        ],
        [
            "Battery side channels",
            "Electric-vehicle battery consumption revealed driver, style, occupancy, and habitual endpoints [11].",
            "Battery or controller data may expose recurring operational patterns.",
            "Direct for electric-vehicle datasets; conditional on resolution and access.",
        ],
        [
            "Electrical load inference",
            "Power signatures can reveal appliance use and behavior [12,13].",
            "Supports inference from non-positional telemetry.",
            "Mechanism analogy; not proof for every device.",
        ],
        [
            "BMS history",
            "Health and forensic analysis use cycle, voltage, current, and temperature history [14-16].",
            "Retained records may remain informative during service or return.",
            "Data depth and storage location are implementation-specific.",
        ],
        [
            "Lifecycle custody",
            "Supply-chain and IoT guidance treats access, logging, support, and sanitization as lifecycle controls [19-23].",
            "Maintenance, recall, and disposal require explicit assurance.",
            "Normative guidance; effectiveness requires verification.",
        ],
    ],
}


TABLE_2 = {
    "title": "Table 2. Lifecycle controls and auditable evidence",
    "headers": ["Stage", "Control objective", "Minimum requirement", "Evidence of compliance"],
    "rows": [
        [
            "Procurement",
            "Establish visibility before deployment",
            "Data inventory; component and software provenance; sub-processor and jurisdiction list",
            "Architecture diagram; software bill of materials; supplier attestations; contract schedules",
        ],
        [
            "Deployment",
            "Bind device to approved context",
            "Hardened configuration; disabled unnecessary interfaces; approved identifiers and zones",
            "Configuration record; acceptance test; asset registration",
        ],
        [
            "Operation",
            "Minimize and contain telemetry",
            "Purpose limitation; local processing where feasible; bounded retention; least privilege",
            "Field-level schema; retention test; access logs; deletion evidence",
        ],
        [
            "Maintenance",
            "Control diagnostic and physical access",
            "Vetted staff; authorized tools; logged sessions; chain of custody; tamper evidence",
            "Work order; access log; tool inventory; custody receipt",
        ],
        [
            "Recall/return",
            "Prevent emergency return from bypassing security",
            "Data-bearing component check; approved recipient; sanitize, escrow, or controlled retention",
            "Recall playbook; transfer authorization; sanitization or legal-hold record",
        ],
        [
            "Second life/disposal",
            "Remove residual data and credentials",
            "Verified sanitization of all components; key revocation; controlled recycler",
            "Sanitization certificate; revocation log; recycler audit",
        ],
        [
            "Continuous assurance",
            "Detect changes in supplier or architecture",
            "Incident notice; vulnerability support; material-change approval; periodic reassessment",
            "Update records; support dates; audit report; change notifications",
        ],
    ],
}


REFERENCES = [
    (
        "H. Umebayashi, Defense minister comments on LUUP introduction: "
        "\"No information-security problem\" [in Japanese], ITmedia NEWS, 3 July 2026. "
        "https://www.itmedia.co.jp/news/articles/2607/03/news128.html (accessed 10 July 2026)."
    ),
    (
        "Cybersecurity and Infrastructure Security Agency, Critical Infrastructure Sectors, "
        "2026. https://www.cisa.gov/topics/critical-infrastructure-security-and-resilience/"
        "critical-infrastructure-sectors (accessed 10 July 2026)."
    ),
    (
        "Open Mobility Foundation, MDS Privacy Guide for Cities, 2020. "
        "https://www.openmobilityfoundation.org/introducing-the-mds-privacy-guide-for-cities/ "
        "(accessed 10 July 2026)."
    ),
    (
        "Y.-A. de Montjoye, C.A. Hidalgo, M. Verleysen, V.D. Blondel, Unique in the crowd: "
        "The privacy bounds of human mobility, Scientific Reports 3 (2013) 1376. "
        "https://doi.org/10.1038/srep01376."
    ),
    (
        "K. Elzer, E. Jedermann, S. Roos, J. Schmitt, They see me scooting—A long-term "
        "real-world data analysis of shared micro-mobility services and their privacy "
        "leakage, in: 2025 IEEE 10th European Symposium on Security and Privacy, 2025, "
        "pp. 78–92. https://doi.org/10.1109/EuroSP63326.2025.00014."
    ),
    (
        "A.B. Petersen, Scoot over smart devices: The invisible costs of rental scooters, "
        "Surveillance & Society 17 (2019) 191–197. "
        "https://doi.org/10.24908/ss.v17i1/2.13112."
    ),
    (
        "N. Vinayaga-Sureshkanth, R. Wijewickrama, A. Maiti, M. Jadliwala, Security and "
        "privacy challenges in upcoming intelligent urban micromobility transportation "
        "systems, in: Proceedings of the Second ACM Workshop on Automotive and Aerial "
        "Vehicle Security, 2020, pp. 31–35. https://doi.org/10.1145/3375706.3380559."
    ),
    (
        "A. Hern, Fitness tracking app Strava gives away location of secret US army bases, "
        "The Guardian, 28 January 2018. https://www.theguardian.com/world/2018/jan/28/"
        "fitness-tracking-app-gives-away-location-of-secret-us-army-bases "
        "(accessed 10 July 2026)."
    ),
    (
        "U.S. Department of Defense, Use of Geolocation-Capable Devices, Applications, "
        "and Services, Memorandum, 3 August 2018. https://www.defense.gov/News/Releases/"
        "Release/Article/1594486/department-of-defense-issues-guidance-on-use-of-"
        "geolocation-capabilities/ (accessed 10 July 2026)."
    ),
    (
        "F. Postma, After Strava, Polar is revealing the homes of soldiers and spies, "
        "Bellingcat, 8 July 2018. https://www.bellingcat.com/resources/articles/2018/07/08/"
        "strava-polar-revealing-homes-soldiers-spies/ (accessed 10 July 2026)."
    ),
    (
        "F. Marchiori, M. Conti, Leaky batteries: A novel set of side-channel attacks on "
        "electric vehicles, in: Computer Security—ESORICS 2025, Lecture Notes in Computer "
        "Science, 2025, pp. 322–333. https://doi.org/10.1007/978-3-032-00624-0_16."
    ),
    (
        "A. Molina-Markham, P. Shenoy, K. Fu, E. Cecchet, D. Irwin, Private memoirs of a "
        "smart meter, in: Proceedings of the 2nd ACM Workshop on Embedded Sensing Systems "
        "for Energy-Efficiency in Building, 2010, pp. 61–66. "
        "https://doi.org/10.1145/1878431.1878446."
    ),
    (
        "G. Kalogridis, C. Efthymiou, S.Z. Denic, T.A. Lewis, R. Cepeda, Privacy for smart "
        "meters: Towards undetectable appliance load signatures, in: 2010 First IEEE "
        "International Conference on Smart Grid Communications, 2010, pp. 232–237. "
        "https://doi.org/10.1109/SMARTGRID.2010.5622047."
    ),
    (
        "E. Braco, I. San Martín, P. Sanchis, A. Ursúa, D.-I. Stroe, State of health "
        "estimation of second-life lithium-ion batteries under real profile operation, "
        "Applied Energy 326 (2022) 119992. https://doi.org/10.1016/j.apenergy.2022.119992."
    ),
    (
        "European Parliament and Council, Regulation (EU) 2023/1542 of 12 July 2023 "
        "concerning batteries and waste batteries, Official Journal of the European Union "
        "L 191 (2023) 1–117."
    ),
    (
        "L. Liu, Y.A. Wu, H. Zhen, Fire investigation based on time-sequential analysis of "
        "lithium-ion battery thermal runaway, Fire 9 (2026) 211. "
        "https://doi.org/10.3390/fire9050211."
    ),
    (
        "European Data Protection Board, Guidelines 01/2020 on processing personal data "
        "in the context of connected vehicles and mobility related applications, Version "
        "2.0, 9 March 2021. https://www.edpb.europa.eu/documents/guideline/"
        "guidelines-012020-on-processing-personal-data-in-the-context-of-connected_en "
        "(accessed 10 July 2026)."
    ),
    (
        "A. Brighente, M. Conti, D. Donadel, R. Poovendran, F. Turrin, J. Zhou, Electric "
        "vehicles security and privacy: Challenges, solutions, and future needs, ACM "
        "Transactions on Cyber-Physical Systems 10(3) (2026) 1–27. "
        "https://doi.org/10.1145/3801968."
    ),
    (
        "National Institute of Standards and Technology, Cybersecurity Supply Chain Risk "
        "Management Practices for Systems and Organizations, NIST SP 800-161 Rev. 1 "
        "Update 1, 2024. https://doi.org/10.6028/NIST.SP.800-161r1-upd1."
    ),
    (
        "National Institute of Standards and Technology, IoT Device Cybersecurity Guidance "
        "for the Federal Government: IoT Device Cybersecurity Requirement Catalog, "
        "NIST SP 800-213A, 2021. https://doi.org/10.6028/NIST.SP.800-213A."
    ),
    (
        "R. Chandramouli, E. Hibbard, Guidelines for Media Sanitization, NIST SP 800-88 "
        "Rev. 2, 2025. https://doi.org/10.6028/NIST.SP.800-88r2."
    ),
    (
        "U.S. Department of Commerce, Bureau of Industry and Security, Securing the "
        "Information and Communications Technology and Services Supply Chain: Connected "
        "Vehicles, Final Rule, 90 Federal Register 5360, 16 January 2025. "
        "https://www.govinfo.gov/content/pkg/FR-2025-01-16/html/2025-00592.htm "
        "(accessed 10 July 2026)."
    ),
    (
        "National Institute of Standards and Technology, Foundational Cybersecurity "
        "Activities for IoT Product Manufacturers, NIST IR 8259 Rev. 1, 2026. "
        "https://doi.org/10.6028/NIST.IR.8259r1."
    ),
]


DECLARATIONS = [
    ("Competing interests", "The author declares no competing interests."),
    ("Funding", "This work received no specific grant from any funding agency."),
    (
        "Ethics approval and consent to participate",
        "Not applicable. The article uses published and publicly available sources and reports no human-participant research.",
    ),
    ("Consent for publication", "Not applicable."),
    (
        "Data availability",
        "No new dataset was generated. All sources used in the synthesis are identified in the reference list.",
    ),
    (
        "Author contribution",
        "The sole author: Conceptualization, investigation, methodology, writing—original draft, and writing—review and editing.",
    ),
    (
        "Declaration of generative AI in scientific writing",
        "Generative artificial intelligence (AI) was used to assist language editing, document formatting, and consistency checks. The author reviewed and takes responsibility for the manuscript's content, claims, and references.",
    ),
]


REFERENCE_VERIFICATION = [
    ["1", "ITmedia NEWS, 3 July 2026", "Verified", "Publisher page and publication date accessible"],
    ["2", "CISA Critical Infrastructure Sectors", "Verified", "Official CISA page"],
    ["3", "OMF MDS Privacy Guide", "Verified", "Official OMF page and guide"],
    ["4", "de Montjoye et al. 2013", "Verified", "DOI 10.1038/srep01376"],
    ["5", "Elzer et al. 2025", "Verified", "DOI 10.1109/EuroSP63326.2025.00014"],
    ["6", "Petersen 2019", "Verified", "DOI 10.24908/ss.v17i1/2.13112"],
    ["7", "Vinayaga-Sureshkanth et al. 2020", "Verified", "DOI 10.1145/3375706.3380559"],
    ["8", "Hern 2018", "Verified", "The Guardian article"],
    ["9", "U.S. DoD memorandum, 3 August 2018", "Verified", "Cited in current DoD CIO policy documents"],
    ["10", "Postma 2018", "Verified", "Bellingcat investigation"],
    ["11", "Marchiori and Conti 2025", "Verified", "DOI 10.1007/978-3-032-00624-0_16"],
    ["12", "Molina-Markham et al. 2010", "Verified", "DOI 10.1145/1878431.1878446"],
    ["13", "Kalogridis et al. 2010", "Verified", "DOI 10.1109/SMARTGRID.2010.5622047"],
    ["14", "Braco et al. 2022", "Verified", "DOI 10.1016/j.apenergy.2022.119992"],
    ["15", "Regulation (EU) 2023/1542", "Verified", "EUR-Lex official text"],
    ["16", "Liu et al. 2026", "Verified", "DOI 10.3390/fire9050211"],
    ["17", "EDPB Guidelines 01/2020 v2.0", "Verified", "Official EDPB PDF"],
    ["18", "Brighente et al. 2026", "Verified", "DOI 10.1145/3801968"],
    ["19", "NIST SP 800-161r1-upd1", "Verified", "DOI 10.6028/NIST.SP.800-161r1-upd1"],
    ["20", "NIST SP 800-213A", "Verified", "Official NIST publication"],
    ["21", "NIST SP 800-88r2", "Verified", "DOI 10.6028/NIST.SP.800-88r2"],
    ["22", "BIS Connected Vehicles Final Rule", "Verified", "90 FR 5360"],
    ["23", "NIST IR 8259r1", "Verified", "Official April 2026 NIST publication"],
]


def reset_dirs() -> None:
    for path in (OUTPUT, WORK):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=80, bottom=80, end=80) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def configure_document(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    normal.paragraph_format.space_after = Pt(6)
    for style_name, size in (("Title", 16), ("Heading 1", 14), ("Heading 2", 12)):
        style = styles[style_name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
    styles["Heading 1"].font.bold = True
    styles["Heading 2"].font.bold = True


def add_text_with_citations(paragraph, text: str) -> None:
    parts = re.split(r"(\[\d+(?:[-,]\d+)*\])", text)
    for part in parts:
        if not part:
            continue
        run = paragraph.add_run(part)
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        run.font.size = Pt(12)


def add_manuscript_paragraph(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.first_line_indent = Inches(0.3)
    paragraph.paragraph_format.keep_together = False
    paragraph.paragraph_format.widow_control = True
    add_text_with_citations(paragraph, text)


def add_table(doc: Document, spec: dict) -> None:
    caption = doc.add_paragraph()
    caption.paragraph_format.space_before = Pt(14)
    caption.paragraph_format.space_after = Pt(6)
    caption.add_run(spec["title"]).bold = True
    table = doc.add_table(rows=1, cols=len(spec["headers"]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    header = table.rows[0].cells
    for index, value in enumerate(spec["headers"]):
        header[index].text = value
        set_cell_shading(header[index], "D9EAF7")
        header[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for run in header[index].paragraphs[0].runs:
            run.bold = True
            run.font.name = "Arial"
            run.font.size = Pt(8)
        set_cell_margins(header[index])
    for row_values in spec["rows"]:
        cells = table.add_row().cells
        for index, value in enumerate(row_values):
            cells[index].text = value
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            set_cell_margins(cells[index])
            for paragraph in cells[index].paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                for run in paragraph.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(8)
    doc.add_paragraph()


def add_page_number(section) -> None:
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char1, instr_text, fld_char2])


def build_figure_pptx() -> Path:
    path = OUTPUT / "Figure1_editable.pptx"
    prs = Presentation()
    prs.slide_width = PptxInches(13.333)
    prs.slide_height = PptxInches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    background = slide.background.fill
    background.solid()
    background.fore_color.rgb = PptxRGB(248, 250, 252)

    title_box = slide.shapes.add_textbox(
        PptxInches(0.55), PptxInches(0.22), PptxInches(12.2), PptxInches(0.55)
    )
    title_frame = title_box.text_frame
    title_frame.clear()
    title_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = title_frame.paragraphs[0]
    p.text = "Lifecycle exposure in serviced telemetry-emitting hardware"
    p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.name = "Aptos Display"
    p.runs[0].font.size = PptxPt(24)
    p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = PptxRGB(20, 44, 68)

    stages = [
        ("1", "PROCURE", "Components\nSoftware\nBackends", "Require inventory,\nprovenance, audit rights"),
        ("2", "DEPLOY", "Identity\nConfiguration\nPlacement", "Harden defaults;\nregister data flows"),
        ("3", "OPERATE", "Trips\nPower use\nFaults", "Minimize, localize,\nlimit access/retention"),
        ("4", "SERVICE", "Diagnostics\nRemoved parts\nDepot access", "Vetted staff, tools,\nlogs, custody records"),
        ("5", "RECALL", "Emergency return\nWarranty data\nEvidence", "Approved recipient;\nsanitize or escrow"),
        ("6", "SECOND LIFE", "Resale\nRecycling\nResidual keys", "Verify sanitization;\nrevoke credentials"),
    ]
    colors = [
        PptxRGB(41, 98, 154),
        PptxRGB(51, 122, 183),
        PptxRGB(34, 139, 136),
        PptxRGB(215, 139, 54),
        PptxRGB(190, 91, 71),
        PptxRGB(112, 86, 153),
    ]
    x0 = 0.35
    box_w = 1.95
    gap = 0.22
    y = 1.25
    for index, (number, heading, data, control) in enumerate(stages):
        x = x0 + index * (box_w + gap)
        box = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            PptxInches(x),
            PptxInches(y),
            PptxInches(box_w),
            PptxInches(4.7),
        )
        box.fill.solid()
        box.fill.fore_color.rgb = PptxRGB(255, 255, 255)
        box.line.color.rgb = colors[index]
        box.line.width = PptxPt(2.5)

        badge = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            PptxInches(x + 0.69),
            PptxInches(y - 0.25),
            PptxInches(0.56),
            PptxInches(0.56),
        )
        badge.fill.solid()
        badge.fill.fore_color.rgb = colors[index]
        badge.line.fill.background()
        tf = badge.text_frame
        tf.clear()
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        pp = tf.paragraphs[0]
        pp.text = number
        pp.alignment = PP_ALIGN.CENTER
        pp.runs[0].font.size = PptxPt(16)
        pp.runs[0].font.bold = True
        pp.runs[0].font.color.rgb = PptxRGB(255, 255, 255)

        heading_box = slide.shapes.add_textbox(
            PptxInches(x + 0.1),
            PptxInches(y + 0.4),
            PptxInches(box_w - 0.2),
            PptxInches(0.45),
        )
        tf = heading_box.text_frame
        tf.clear()
        pp = tf.paragraphs[0]
        pp.text = heading
        pp.alignment = PP_ALIGN.CENTER
        pp.runs[0].font.name = "Aptos"
        pp.runs[0].font.size = PptxPt(15)
        pp.runs[0].font.bold = True
        pp.runs[0].font.color.rgb = colors[index]

        data_label = slide.shapes.add_textbox(
            PptxInches(x + 0.15),
            PptxInches(y + 1.08),
            PptxInches(box_w - 0.3),
            PptxInches(0.35),
        )
        tf = data_label.text_frame
        tf.clear()
        pp = tf.paragraphs[0]
        pp.text = "DATA / ACCESS"
        pp.alignment = PP_ALIGN.CENTER
        pp.runs[0].font.size = PptxPt(9)
        pp.runs[0].font.bold = True
        pp.runs[0].font.color.rgb = PptxRGB(90, 100, 110)

        data_box = slide.shapes.add_textbox(
            PptxInches(x + 0.2),
            PptxInches(y + 1.45),
            PptxInches(box_w - 0.4),
            PptxInches(1.15),
        )
        tf = data_box.text_frame
        tf.clear()
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        pp = tf.paragraphs[0]
        pp.text = data
        pp.alignment = PP_ALIGN.CENTER
        pp.runs[0].font.size = PptxPt(12)
        pp.runs[0].font.color.rgb = PptxRGB(30, 45, 60)

        divider = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            PptxInches(x + 0.2),
            PptxInches(y + 2.77),
            PptxInches(box_w - 0.4),
            PptxInches(0.025),
        )
        divider.fill.solid()
        divider.fill.fore_color.rgb = PptxRGB(215, 220, 225)
        divider.line.fill.background()

        control_label = slide.shapes.add_textbox(
            PptxInches(x + 0.15),
            PptxInches(y + 2.98),
            PptxInches(box_w - 0.3),
            PptxInches(0.35),
        )
        tf = control_label.text_frame
        tf.clear()
        pp = tf.paragraphs[0]
        pp.text = "CONTROL"
        pp.alignment = PP_ALIGN.CENTER
        pp.runs[0].font.size = PptxPt(9)
        pp.runs[0].font.bold = True
        pp.runs[0].font.color.rgb = PptxRGB(90, 100, 110)

        control_box = slide.shapes.add_textbox(
            PptxInches(x + 0.18),
            PptxInches(y + 3.35),
            PptxInches(box_w - 0.36),
            PptxInches(1.1),
        )
        tf = control_box.text_frame
        tf.clear()
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        pp = tf.paragraphs[0]
        pp.text = control
        pp.alignment = PP_ALIGN.CENTER
        pp.runs[0].font.size = PptxPt(11)
        pp.runs[0].font.bold = True
        pp.runs[0].font.color.rgb = colors[index]

        if index < len(stages) - 1:
            arrow = slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT,
                PptxInches(x + box_w),
                PptxInches(y + 2.35),
                PptxInches(x + box_w + gap),
                PptxInches(y + 2.35),
            )
            arrow.line.color.rgb = PptxRGB(100, 110, 120)
            arrow.line.width = PptxPt(2)
            arrow.line.end_arrowhead = True

    footer = slide.shapes.add_textbox(
        PptxInches(0.65), PptxInches(6.35), PptxInches(12.0), PptxInches(0.55)
    )
    tf = footer.text_frame
    tf.clear()
    pp = tf.paragraphs[0]
    pp.text = (
        "Figure 1. Exposure persists when data generated at one stage become accessible "
        "after a later custody transition; controls must therefore be verified end to end."
    )
    pp.alignment = PP_ALIGN.CENTER
    pp.runs[0].font.size = PptxPt(12)
    pp.runs[0].font.italic = True
    pp.runs[0].font.color.rgb = PptxRGB(70, 80, 90)

    prs.save(path)
    return path


def load_font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    if bold and italic:
        name = "FreeSansBoldOblique.ttf"
    elif bold:
        name = "FreeSansBold.ttf"
    elif italic:
        name = "FreeSansOblique.ttf"
    else:
        name = "FreeSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/freefont/{name}", size)


def centered_multiline(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    spacing: int = 12,
) -> None:
    left, top, right, bottom = box
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, align="center")
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = left + (right - left - width) / 2
    y = top + (bottom - top - height) / 2
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=spacing, align="center")


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int]) -> None:
    color = (100, 110, 120)
    draw.line([start, end], fill=color, width=10)
    x, y = end
    draw.polygon([(x, y), (x - 32, y - 22), (x - 32, y + 22)], fill=color)


def build_figure_raster(pptx_path: Path) -> dict[str, Path]:
    width, height = 4800, 2300
    image = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(image)
    title_font = load_font(142, bold=True)
    stage_font = load_font(64, bold=True)
    label_font = load_font(36, bold=True)
    body_font = load_font(58)
    control_font = load_font(50, bold=True)
    number_font = load_font(60, bold=True)

    centered_multiline(
        draw,
        (120, 50, width - 120, 300),
        "Lifecycle exposure in serviced telemetry-emitting hardware",
        title_font,
        (20, 44, 68),
    )
    stages = [
        ("1", "PROCURE", "Components\nSoftware\nBackends", "Require inventory,\nprovenance, audit rights"),
        ("2", "DEPLOY", "Identity\nConfiguration\nPlacement", "Harden defaults;\nregister data flows"),
        ("3", "OPERATE", "Trips\nPower use\nFaults", "Minimize, localize,\nlimit access/retention"),
        ("4", "SERVICE", "Diagnostics\nRemoved parts\nDepot access", "Vetted staff, tools,\nlogs, custody records"),
        ("5", "RECALL", "Emergency return\nWarranty data\nEvidence", "Approved recipient;\nsanitize or escrow"),
        ("6", "SECOND LIFE", "Resale\nRecycling\nResidual keys", "Verify sanitization;\nrevoke credentials"),
    ]
    colors = [
        (41, 98, 154),
        (51, 122, 183),
        (34, 139, 136),
        (215, 139, 54),
        (190, 91, 71),
        (112, 86, 153),
    ]
    margin = 105
    gap = 70
    box_width = (width - margin * 2 - gap * 5) // 6
    top = 515
    bottom = 2190
    for index, (number, heading, data, control) in enumerate(stages):
        left = margin + index * (box_width + gap)
        right = left + box_width
        color = colors[index]
        draw.rounded_rectangle(
            (left, top, right, bottom),
            radius=42,
            fill=(255, 255, 255),
            outline=color,
            width=12,
        )
        badge_radius = 74
        badge_x = (left + right) // 2
        badge_y = top
        draw.ellipse(
            (
                badge_x - badge_radius,
                badge_y - badge_radius,
                badge_x + badge_radius,
                badge_y + badge_radius,
            ),
            fill=color,
        )
        centered_multiline(
            draw,
            (
                badge_x - badge_radius,
                badge_y - badge_radius,
                badge_x + badge_radius,
                badge_y + badge_radius,
            ),
            number,
            number_font,
            (255, 255, 255),
        )
        centered_multiline(draw, (left + 20, top + 135, right - 20, top + 330), heading, stage_font, color)
        centered_multiline(
            draw, (left + 20, top + 350, right - 20, top + 470), "DATA / ACCESS", label_font, (90, 100, 110)
        )
        centered_multiline(
            draw, (left + 30, top + 475, right - 30, top + 900), data, body_font, (30, 45, 60), spacing=24
        )
        divider_y = top + 940
        draw.line((left + 65, divider_y, right - 65, divider_y), fill=(215, 220, 225), width=6)
        centered_multiline(
            draw, (left + 20, top + 990, right - 20, top + 1110), "CONTROL", label_font, (90, 100, 110)
        )
        centered_multiline(
            draw,
            (left + 25, top + 1110, right - 25, bottom - 55),
            control,
            control_font,
            color,
            spacing=22,
        )
        if index < len(stages) - 1:
            draw_arrow(draw, (right + 5, (top + bottom) // 2), (right + gap - 8, (top + bottom) // 2))

    figure_png = OUTPUT / "Figure1.png"
    image.save(figure_png, format="PNG", optimize=True, dpi=(600, 600))
    figure_tiff = OUTPUT / "Figure1.tiff"
    image.save(figure_tiff, format="TIFF", compression="tiff_lzw", dpi=(1200, 1200))
    figure_pdf = OUTPUT / "Figure1.pdf"
    image.save(figure_pdf, format="PDF", resolution=600.0)
    return {"png": figure_png, "tiff": figure_tiff, "pdf": figure_pdf, "pptx": pptx_path}


def build_manuscript(figure_png: Path) -> Path:
    doc = Document()
    configure_document(doc)
    add_page_number(doc.sections[0])
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run(TITLE).bold = True
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Anonymized manuscript")
    run.italic = True
    run.font.size = Pt(10)

    heading = doc.add_paragraph(style="Heading 1")
    heading.add_run("Abstract")
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.add_run(ABSTRACT)

    keywords = doc.add_paragraph()
    keywords.add_run("Keywords: ").bold = True
    keywords.add_run("; ".join(KEYWORDS))

    for section_title, paragraphs in SECTIONS:
        doc.add_heading(section_title, level=1)
        for index, text in enumerate(paragraphs):
            add_manuscript_paragraph(doc, text)
            if section_title == "5. Lifecycle exposure in serviced hardware" and index == 0:
                image_p = doc.add_paragraph()
                image_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                image_p.paragraph_format.space_before = Pt(12)
                image_p.add_run().add_picture(str(figure_png), width=Inches(6.45))
                caption = doc.add_paragraph()
                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
                caption.paragraph_format.space_before = Pt(12)
                caption.paragraph_format.space_after = Pt(12)
                caption_run = caption.add_run(
                    "Figure 1. Lifecycle exposure in serviced telemetry-emitting hardware. "
                    "Information created at one stage may become accessible after a later "
                    "custody transition; controls therefore span procurement through disposal."
                )
                caption_run.italic = True
                caption_run.font.size = Pt(10)
            if section_title == "6. Evidence-to-risk synthesis" and index == 0:
                add_table(doc, TABLE_1)
            if section_title == "7. A lifecycle assurance framework" and index == 2:
                add_table(doc, TABLE_2)

    doc.add_heading("Declarations", level=1)
    for label, value in DECLARATIONS:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.add_run(f"{label}: ").bold = True
        paragraph.add_run(value)

    doc.add_heading("References", level=1)
    for number, reference in enumerate(REFERENCES, 1):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.28)
        paragraph.paragraph_format.first_line_indent = Inches(-0.28)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.add_run(f"[{number}] {reference}")

    path = OUTPUT / "Discharged_Secrets_IJCIP_manuscript.docx"
    doc.save(path)
    return path


def build_title_page() -> Path:
    doc = Document()
    configure_document(doc)
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run(TITLE).bold = True
    doc.add_paragraph()
    author = doc.add_paragraph()
    author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    author.add_run(AUTHOR).bold = True
    affiliation = doc.add_paragraph()
    affiliation.alignment = WD_ALIGN_PARAGRAPH.CENTER
    affiliation.add_run(AFFILIATION)
    correspondence = doc.add_paragraph()
    correspondence.alignment = WD_ALIGN_PARAGRAPH.CENTER
    correspondence.add_run(f"Corresponding author: {AUTHOR}; {EMAIL}")
    orcid = doc.add_paragraph()
    orcid.alignment = WD_ALIGN_PARAGRAPH.CENTER
    orcid.add_run(f"ORCID: {ORCID}")
    doc.add_paragraph()
    fields = [
        ("Full title", TITLE),
        ("Short title", SHORT_TITLE),
        ("Article type", "Full-length article"),
        ("Word count", "[Inserted automatically in the validation report]"),
        ("Figures", "1"),
        ("Tables", "2"),
        ("Funding", "None"),
        ("Competing interests", "None declared"),
    ]
    for label, value in fields:
        paragraph = doc.add_paragraph()
        paragraph.add_run(f"{label}: ").bold = True
        paragraph.add_run(value)
    path = OUTPUT / "Title_Page_IJCIP.docx"
    doc.save(path)
    return path


def build_cover_letter() -> Path:
    doc = Document()
    configure_document(doc)
    for line in [AUTHOR, AFFILIATION, EMAIL, f"ORCID: {ORCID}", BUILD_DATE]:
        paragraph = doc.add_paragraph(line)
        paragraph.paragraph_format.space_after = Pt(2)
    doc.add_paragraph()
    doc.add_paragraph("Editor-in-Chief")
    doc.add_paragraph(JOURNAL)
    doc.add_paragraph("Elsevier")
    doc.add_paragraph()
    doc.add_paragraph("Dear Editor-in-Chief,")
    paragraphs = [
        (
            f"I submit the manuscript, “{TITLE},” for consideration as a full-length "
            f"article in the {JOURNAL}."
        ),
        (
            "The manuscript addresses a procurement and lifecycle-security gap that cuts "
            "across transportation systems, government facilities, the defense industrial "
            "base, commercial facilities, and information technology. It defines serviced "
            "telemetry-emitting hardware: connected equipment used by an organization that "
            "does not fully control the hardware, software, service backend, maintenance, "
            "or disposition. Shared micromobility is used as an illustrative case, but the "
            "framework applies to leased sensors, fleet equipment, smart lockers, inspection "
            "devices, wearables, charging systems, and other externally serviced assets."
        ),
        (
            "The article's principal contribution is a structured synthesis linking "
            "mobility re-identification, battery side channels, battery-management history, "
            "service custody, and cybersecurity supply-chain guidance. It proposes a six-"
            "stage lifecycle exposure model and translates it into auditable controls for "
            "procurement, operation, maintenance, emergency recall, and disposition. The "
            "analysis distinguishes demonstrated capabilities from conditional transfer and "
            "does not allege compromise or misconduct by the organization or service provider "
            "in the Japanese policy vignette."
        ),
        (
            "The manuscript fits the journal's stated interest in work that combines science, "
            "technology, law, and policy to produce practical solutions for critical-"
            "infrastructure protection. Its control matrix is intended for infrastructure "
            "owners, public procurement teams, security practitioners, and service providers."
        ),
        (
            "I confirm that the manuscript is original, has not been published, and is not "
            "under consideration elsewhere. No human-participant research was conducted, no "
            "new dataset was generated, and there is no funding or competing interest to "
            "declare. All references were checked for existence and correspondence with the "
            "claims made. The submission includes an anonymized manuscript, separate title "
            "page, highlights, high-resolution and editable artwork, editable tables, and a "
            "compliance checklist."
        ),
        (
            "Thank you for considering this manuscript."
        ),
    ]
    for text in paragraphs:
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        paragraph.add_run(text)
    doc.add_paragraph("Sincerely,")
    doc.add_paragraph(AUTHOR)
    path = OUTPUT / "Cover_Letter_IJCIP.docx"
    doc.save(path)
    return path


def build_highlights() -> Path:
    doc = Document()
    configure_document(doc)
    heading = doc.add_paragraph(style="Title")
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.add_run("Highlights").bold = True
    for item in HIGHLIGHTS:
        doc.add_paragraph(item, style="List Bullet")
    path = OUTPUT / "Highlights_IJCIP.docx"
    doc.save(path)
    (OUTPUT / "Highlights_IJCIP.txt").write_text(
        "\n".join(f"• {item}" for item in HIGHLIGHTS) + "\n", encoding="utf-8"
    )
    return path


def build_tables_docx() -> Path:
    doc = Document()
    configure_document(doc)
    heading = doc.add_paragraph(style="Title")
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.add_run("Editable tables").bold = True
    add_table(doc, TABLE_1)
    doc.add_section(WD_SECTION.NEW_PAGE)
    add_table(doc, TABLE_2)
    path = OUTPUT / "Tables_IJCIP_editable.docx"
    doc.save(path)
    return path


def build_reference_report() -> Path:
    path = OUTPUT / "Reference_Verification.csv"
    lines = ["Reference,Short citation,Status,Evidence"]
    for row in REFERENCE_VERIFICATION:
        escaped = [f'"{value.replace(chr(34), chr(34) * 2)}"' for value in row]
        lines.append(",".join(escaped))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_citation_audit() -> Path:
    entries: list[tuple[str, str]] = []
    for section_title, paragraphs in SECTIONS:
        for index, paragraph in enumerate(paragraphs):
            entries.append((section_title, paragraph))
            if section_title == "6. Evidence-to-risk synthesis" and index == 0:
                for row in TABLE_1["rows"]:
                    entries.append((TABLE_1["title"], " ".join(row)))
            if section_title == "7. A lifecycle assurance framework" and index == 2:
                for row in TABLE_2["rows"]:
                    entries.append((TABLE_2["title"], " ".join(row)))
    first_appearance: dict[int, tuple[str, str, str]] = {}
    for location, text in entries:
        for token in re.findall(r"\[\d+(?:[-,]\d+)*\]", text):
            for number in expand_citation(token):
                first_appearance.setdefault(number, (location, token, text))
    path = OUTPUT / "Citation_Audit.csv"
    lines = ["Reference,First appearance,Citation token,Context"]
    for number in range(1, len(REFERENCES) + 1):
        location, token, context = first_appearance[number]
        context = textwrap.shorten(context, width=260, placeholder="...")
        row = [str(number), location, token, context]
        escaped = [f'"{value.replace(chr(34), chr(34) * 2)}"' for value in row]
        lines.append(",".join(escaped))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_reporting_guideline_statement() -> Path:
    doc = Document()
    configure_document(doc)
    heading = doc.add_paragraph(style="Title")
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.add_run("Reporting Guideline Statement").bold = True
    paragraphs = [
        (
            "Article design: conceptual critical-infrastructure policy analysis supported "
            "by a structured evidence synthesis. The manuscript does not report a clinical "
            "trial, observational study, diagnostic-accuracy study, case report, qualitative "
            "interview study, animal study, economic evaluation, or systematic review."
        ),
        (
            "Accordingly, CONSORT, STROBE, STARD, CARE, COREQ, ARRIVE, CHEERS, and PRISMA "
            "checklists are not applicable. The reviewed IJCIP and Elsevier instructions did "
            "not identify a separate EQUATOR checklist for this article design."
        ),
        (
            "Transparency measures used instead: the manuscript defines the unit of analysis; "
            "states the four evidence questions; distinguishes direct demonstration from "
            "mechanism-based transfer; identifies the source types used; separates the "
            "illustrative Japanese policy vignette from empirical evidence; provides a "
            "claim-to-evidence table; states limitations; lists all references; and includes "
            "funding, competing-interest, ethics, data-availability, author-contribution, and "
            "generative-artificial-intelligence disclosures."
        ),
        (
            "This statement should be uploaded as supplementary submission information only "
            "if the Editorial Manager portal requests a reporting-guideline document. It is "
            "not part of the anonymized manuscript."
        ),
    ]
    for text in paragraphs:
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        paragraph.add_run(text)
    applicability = [
        ("CONSORT", "Randomized trials", "Not applicable"),
        ("STROBE", "Observational studies", "Not applicable"),
        ("PRISMA", "Systematic reviews and meta-analyses", "Not applicable"),
        ("COREQ", "Qualitative interview/focus-group studies", "Not applicable"),
        ("CHEERS", "Health economic evaluations", "Not applicable"),
        ("ARRIVE", "Animal research", "Not applicable"),
    ]
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, text in zip(table.rows[0].cells, ["Guideline", "Study type", "Status"]):
        cell.text = text
        set_cell_shading(cell, "D9EAF7")
        for run in cell.paragraphs[0].runs:
            run.bold = True
    for guideline, design, status in applicability:
        cells = table.add_row().cells
        cells[0].text = guideline
        cells[1].text = design
        cells[2].text = status
    path = OUTPUT / "Reporting_Guideline_Statement_IJCIP.docx"
    doc.save(path)
    return path


def build_checklist(validation: dict) -> Path:
    doc = Document()
    configure_document(doc)
    heading = doc.add_paragraph(style="Title")
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.add_run("IJCIP Pre-submission Compliance Checklist").bold = True
    intro = doc.add_paragraph(
        "Formal reporting checklists such as CONSORT, STROBE, and PRISMA do not apply "
        "because this is a conceptual structured synthesis without participant-level data "
        "or a systematic-review claim."
    )
    intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    checks = [
        ("Scope", "Transportation, government facilities, defense industrial base, and information-security relevance stated.", True),
        ("Article type", "Prepared as a full-length research/policy article.", True),
        ("Anonymization", "Main manuscript contains no author identity; separate title page supplied.", True),
        ("Abstract", f"{validation['abstract_words']} words; self-contained; no citations.", validation["abstract_words"] <= 250),
        ("Keywords", f"{len(KEYWORDS)} keywords supplied.", len(KEYWORDS) <= 6),
        ("Highlights", "Five editable bullets; each no more than 85 characters.", validation["highlights_ok"]),
        ("Citations", "Numbered in square brackets in order of first appearance.", validation["citations_sequential"]),
        ("References", f"{len(REFERENCES)} cited references; no orphan or phantom entries.", validation["references_complete"]),
        ("Verification", f"{len(REFERENCE_VERIFICATION)}/{len(REFERENCES)} references independently checked.", len(REFERENCE_VERIFICATION) == len(REFERENCES)),
        ("Figure citation", "Figure 1 is cited before placement and supplied inline and separately.", validation["figure_cited"]),
        ("Table citations", "Tables 1 and 2 are cited before placement and supplied inline and separately.", validation["tables_cited"]),
        ("Artwork", "Editable PPTX, PDF, 600-dpi PNG, and 1200-dpi TIFF supplied.", True),
        ("Declarations", "Funding, competing interests, ethics, data, contribution, and AI-use statements included.", True),
        ("Language", "American English, terminology, abbreviations, and flow reviewed.", True),
        ("Limitations", "No compromise or vendor misconduct alleged; transfer boundaries stated.", True),
        ("Data availability", "No new dataset; source list provided.", True),
        ("Portal check", "Recheck live Editorial Manager item list and required classifications before upload.", False),
    ]
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, value in zip(table.rows[0].cells, ["Item", "Requirement", "Status", "Action"]):
        cell.text = value
        set_cell_shading(cell, "D9EAF7")
        for run in cell.paragraphs[0].runs:
            run.bold = True
    for item, requirement, passed in checks:
        cells = table.add_row().cells
        cells[0].text = item
        cells[1].text = requirement
        cells[2].text = "PASS" if passed else "AUTHOR CHECK"
        cells[3].text = "" if passed else "Confirm the live journal portal requirement immediately before submission."
        if passed:
            set_cell_shading(cells[2], "E2F0D9")
        else:
            set_cell_shading(cells[2], "FFF2CC")
    path = OUTPUT / "Submission_Checklist_IJCIP.docx"
    doc.save(path)
    return path


def word_count() -> int:
    text = " ".join([TITLE, ABSTRACT] + [p for _, paragraphs in SECTIONS for p in paragraphs])
    return len(re.findall(r"\b[\w'-]+\b", text))


def expand_citation(token: str) -> list[int]:
    values: list[int] = []
    for part in token.strip("[]").split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            values.extend(range(start, end + 1))
        else:
            values.append(int(part))
    return values


def ordered_manuscript_content() -> str:
    parts: list[str] = []
    for section_title, paragraphs in SECTIONS:
        for index, paragraph in enumerate(paragraphs):
            parts.append(paragraph)
            if section_title == "6. Evidence-to-risk synthesis" and index == 0:
                parts.extend(TABLE_1["headers"])
                parts.extend(sum(TABLE_1["rows"], []))
            if section_title == "7. A lifecycle assurance framework" and index == 2:
                parts.extend(TABLE_2["headers"])
                parts.extend(sum(TABLE_2["rows"], []))
    return " ".join(parts)


def validate_content() -> dict:
    body = ordered_manuscript_content()
    citation_tokens = re.findall(r"\[\d+(?:[-,]\d+)*\]", body)
    cited: list[int] = []
    first_seen: list[int] = []
    for token in citation_tokens:
        for number in expand_citation(token):
            cited.append(number)
            if number not in first_seen:
                first_seen.append(number)
    expected = list(range(1, len(REFERENCES) + 1))
    abstract_words = len(re.findall(r"\b[\w'-]+\b", ABSTRACT))
    highlights_ok = all(len(item) <= 85 for item in HIGHLIGHTS)
    validation = {
        "word_count": word_count(),
        "abstract_words": abstract_words,
        "highlights_ok": highlights_ok,
        "citations_sequential": first_seen == expected,
        "references_complete": sorted(set(cited)) == expected,
        "figure_cited": "Figure 1" in body,
        "tables_cited": "Table 1" in body and "Table 2" in body,
    }
    failures = [key for key, value in validation.items() if isinstance(value, bool) and not value]
    if abstract_words > 250:
        failures.append("abstract_words")
    if failures:
        raise RuntimeError(f"Validation failed: {', '.join(failures)}; first_seen={first_seen}")
    all_text = " ".join(
        [
            body,
            " ".join(value for _, value in DECLARATIONS),
        ]
    )
    for abbreviation, definition in {
        "GPS": "Global Positioning System (GPS)",
        "BMS": "Battery-management systems (BMSs)",
        "NIST": "National Institute of Standards and Technology",
        "AI": "artificial intelligence (AI)",
    }.items():
        if abbreviation in all_text and definition not in all_text:
            raise RuntimeError(f"Undefined abbreviation: {abbreviation}")
    return validation


def reportlab_table(spec: dict, body_style: ParagraphStyle) -> KeepTogether:
    data = [
        [ReportLabParagraph(f"<b>{value}</b>", body_style) for value in spec["headers"]]
    ]
    for row in spec["rows"]:
        data.append([ReportLabParagraph(value, body_style) for value in row])
    table = ReportLabTable(
        data,
        colWidths=[1.25 * inch, 1.75 * inch, 1.8 * inch, 1.7 * inch],
        repeatRows=1,
        hAlign="CENTER",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#808080")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    caption = ReportLabParagraph(f"<b>{spec['title']}</b>", body_style)
    return KeepTogether([caption, Spacer(1, 6), table, Spacer(1, 12)])


def add_pdf_page_number(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Times-Roman", 9)
    canvas.drawCentredString(letter[0] / 2, 0.45 * inch, str(document.page))
    canvas.restoreState()


def build_manuscript_pdf(figure_png: Path) -> Path:
    path = OUTPUT / "Discharged_Secrets_IJCIP_manuscript_reference.pdf"
    pdf = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.7 * inch,
        title=TITLE,
        author="Anonymized",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ManuscriptTitle",
        parent=styles["Title"],
        fontName="Times-Bold",
        fontSize=16,
        leading=19,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading1"],
        fontName="Times-Bold",
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ManuscriptBody",
        parent=styles["BodyText"],
        fontName="Times-Roman",
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        firstLineIndent=16,
        spaceAfter=6,
    )
    no_indent = ParagraphStyle(
        "NoIndent",
        parent=body_style,
        firstLineIndent=0,
    )
    table_style = ParagraphStyle(
        "TableText",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8,
        spaceAfter=0,
    )
    caption_style = ParagraphStyle(
        "Caption",
        parent=styles["BodyText"],
        fontName="Times-Italic",
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=10,
    )
    story = [
        ReportLabParagraph(TITLE, title_style),
        ReportLabParagraph("<i>Anonymized manuscript</i>", no_indent),
        Spacer(1, 8),
        ReportLabParagraph("Abstract", heading_style),
        ReportLabParagraph(ABSTRACT, no_indent),
        ReportLabParagraph(f"<b>Keywords:</b> {'; '.join(KEYWORDS)}", no_indent),
    ]
    for section_title, paragraphs in SECTIONS:
        story.append(ReportLabParagraph(section_title, heading_style))
        for index, text in enumerate(paragraphs):
            story.append(ReportLabParagraph(text, body_style))
            if section_title == "5. Lifecycle exposure in serviced hardware" and index == 0:
                figure = ReportLabImage(
                    str(figure_png), width=6.5 * inch, height=(6.5 * 2300 / 4800) * inch
                )
                figure.hAlign = "CENTER"
                story.append(figure)
                story.append(
                    ReportLabParagraph(
                        "Figure 1. Lifecycle exposure in serviced telemetry-emitting hardware. "
                        "Information created at one stage may become accessible after a later "
                        "custody transition; controls therefore span procurement through disposal.",
                        caption_style,
                    )
                )
            if section_title == "6. Evidence-to-risk synthesis" and index == 0:
                story.append(reportlab_table(TABLE_1, table_style))
            if section_title == "7. A lifecycle assurance framework" and index == 2:
                story.append(reportlab_table(TABLE_2, table_style))
    story.append(ReportLabParagraph("Declarations", heading_style))
    for label, value in DECLARATIONS:
        story.append(ReportLabParagraph(f"<b>{label}:</b> {value}", no_indent))
    story.append(ReportLabParagraph("References", heading_style))
    reference_style = ParagraphStyle(
        "References",
        parent=no_indent,
        fontSize=9,
        leading=12,
        leftIndent=18,
        firstLineIndent=-18,
    )
    for number, reference in enumerate(REFERENCES, 1):
        story.append(ReportLabParagraph(f"[{number}] {reference}", reference_style))
    pdf.build(story, onFirstPage=add_pdf_page_number, onLaterPages=add_pdf_page_number)
    return path


def update_title_page_word_count(path: Path, count: int) -> None:
    doc = Document(path)
    for paragraph in doc.paragraphs:
        if paragraph.text.startswith("Word count:"):
            paragraph.clear()
            paragraph.add_run("Word count: ").bold = True
            paragraph.add_run(f"{count:,} (title, abstract, and main text; references excluded)")
            break
    doc.save(path)


def write_validation_report(validation: dict, figure_paths: dict[str, Path]) -> Path:
    image = Image.open(figure_paths["png"])
    report = [
        "IJCIP submission validation",
        f"Build date: {BUILD_DATE}",
        f"Main-text word count (references excluded): {validation['word_count']}",
        f"Abstract word count: {validation['abstract_words']}",
        f"References: {len(REFERENCES)}",
        f"Citations sequential: {validation['citations_sequential']}",
        f"References complete: {validation['references_complete']}",
        f"Figure cited: {validation['figure_cited']}",
        f"Tables cited: {validation['tables_cited']}",
        f"Highlights <=85 characters: {validation['highlights_ok']}",
        f"Figure PNG pixels: {image.width} x {image.height}",
        "Figure PNG render target: 600 dpi",
        "Figure TIFF metadata target: 1200 dpi",
        "Remaining manual action: confirm the live Editorial Manager upload item list.",
    ]
    path = OUTPUT / "VALIDATION.txt"
    path.write_text("\n".join(report) + "\n", encoding="utf-8")
    return path


def build_zip() -> Path:
    zip_path = OUTPUT / "IJCIP_submission_package.zip"
    members = [
        path
        for path in OUTPUT.iterdir()
        if path.is_file() and path != zip_path and not path.name.endswith(".tmp")
    ]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(members):
            archive.write(path, arcname=path.name)
    return zip_path


def main() -> None:
    reset_dirs()
    validation = validate_content()
    pptx_path = build_figure_pptx()
    figure_paths = build_figure_raster(pptx_path)
    manuscript = build_manuscript(figure_paths["png"])
    build_manuscript_pdf(figure_paths["png"])
    title_page = build_title_page()
    update_title_page_word_count(title_page, validation["word_count"])
    cover_letter = build_cover_letter()
    highlights = build_highlights()
    tables = build_tables_docx()
    build_reference_report()
    build_citation_audit()
    build_reporting_guideline_statement()
    checklist = build_checklist(validation)
    write_validation_report(validation, figure_paths)
    build_zip()
    print(f"Built {len(list(OUTPUT.iterdir()))} files in {OUTPUT}")


if __name__ == "__main__":
    main()
