"""
TrustLayer AI — SVG Diagram Generator
Produces three diagrams:
  1. End User Flow
  2. HLD Architecture
  3. LLD Architecture
"""

# ── palette ──────────────────────────────────────────────────────────────────
BG      = "#0F172A"
CARD    = "#1E293B"
CARD2   = "#162132"
BLUE    = "#0066FF"
DBLUE   = "#003388"
TEAL    = "#00B894"
RED     = "#E74C3C"
ORANGE  = "#F39C12"
PURPLE  = "#8E44AD"
GREEN   = "#27AE60"
WHITE   = "#FFFFFF"
GRAY    = "#94A3B8"
LGRAY   = "#CBD5E1"
LBLUE   = "#E8F4FD"

FONT = "font-family=\"Segoe UI,Arial,sans-serif\""


# ── low-level SVG primitives ──────────────────────────────────────────────────

def rect(x, y, w, h, fill, rx=8, stroke=None, sw=1.5, opacity=1):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" rx="{rx}"'
    if stroke: s += f' stroke="{stroke}" stroke-width="{sw}"'
    if opacity != 1: s += f' opacity="{opacity}"'
    return s + "/>"

def esc(s):
    """Escape XML special characters in SVG text content."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def text(x, y, content, fill=WHITE, size=14, bold=False, anchor="middle", dy=0):
    w = "font-weight=\"bold\"" if bold else ""
    return (f'<text x="{x}" y="{y}" {FONT} font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" dominant-baseline="middle" {w} dy="{dy}">'
            f'{esc(content)}</text>')

def arrow(x1, y1, x2, y2, color=BLUE, dashed=False, label=None, lx=None, ly=None):
    dash = 'stroke-dasharray="6,4"' if dashed else ""
    line = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="2" marker-end="url(#arr_{color[1:]})" {dash}/>')
    parts = [line]
    if label:
        lx = lx or (x1 + x2) // 2 + 8
        ly = ly or (y1 + y2) // 2
        parts.append(text(lx, ly, label, GRAY, 11, anchor="start"))
    return "\n".join(parts)

def arrow_path(d, color=BLUE, dashed=False):
    dash = 'stroke-dasharray="6,4"' if dashed else ""
    return (f'<path d="{d}" stroke="{color}" stroke-width="2" fill="none" '
            f'marker-end="url(#arr_{color[1:]})" {dash}/>')

def defs(*colors):
    """Arrow marker defs for given hex colors (without #)."""
    out = ["<defs>",
           '<filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">',
           '  <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000" flood-opacity="0.4"/>',
           '</filter>']
    for c in colors:
        out.append(
            f'<marker id="arr_{c}" markerWidth="8" markerHeight="8" '
            f'refX="7" refY="3" orient="auto">'
            f'<path d="M0,0 L0,6 L8,3 z" fill="#{c}"/></marker>')
    out.append("</defs>")
    return "\n".join(out)

def wrap(content, width, height, title="TrustLayer AI"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f'<title>{title}</title>\n'
            f'<rect width="{width}" height="{height}" fill="{BG}"/>\n'
            + content + "\n</svg>")

def badge(x, y, w, h, label, color=BLUE):
    return (rect(x, y, w, h, color, rx=4) +
            text(x + w//2, y + h//2, label, WHITE, 10, bold=True))

def node(x, y, w, h, title, subtitle=None, color=BLUE, icon=None):
    """A card-style node with a colored top bar."""
    parts = [rect(x, y, w, h, CARD, rx=10, stroke=color, sw=1.5),
             rect(x, y, w, 6, color, rx=0)]
    if icon:
        parts.append(text(x + 28, y + h//2, icon, color, 22))
        parts.append(text(x + w//2 + 10, y + h//2 - (8 if subtitle else 0),
                          title, WHITE, 13, bold=True))
    else:
        parts.append(text(x + w//2, y + h//2 - (8 if subtitle else 0),
                          title, WHITE, 13, bold=True))
    if subtitle:
        parts.append(text(x + w//2, y + h//2 + 14, subtitle, GRAY, 10))
    return "\n".join(parts)

def section_label(x, y, label, color=GRAY):
    return (f'<text x="{x}" y="{y}" {FONT} font-size="11" fill="{color}" '
            f'text-anchor="start" font-weight="bold" letter-spacing="1.5">{esc(label)}</text>')


# ═════════════════════════════════════════════════════════════════════════════
# DIAGRAM 1 — END USER FLOW
# ═════════════════════════════════════════════════════════════════════════════

def diagram_end_user_flow():
    W, H = 900, 1700
    CX = W // 2  # center x

    arrow_colors = ["0066FF", "00B894", "E74C3C", "F39C12", "27AE60"]

    d = defs(*arrow_colors)

    # ── Title ─────────────────────────────────────────────────────────────────
    d += rect(0, 0, W, 64, DBLUE, rx=0)
    d += text(CX, 32, "TrustLayer AI — End-to-End User Flow", WHITE, 20, bold=True)

    # ── Row y positions ───────────────────────────────────────────────────────
    y_user      = 90
    y_app       = 210
    y_gateway   = 340
    y_llm       = 480
    y_det       = 480
    y_raw       = 620
    y_score     = 760
    y_diamond   = 900
    y_actions   = 1050
    y_outcomes  = 1200
    y_audit     = 1420
    y_final     = 1560

    NW = 320   # node width
    NH = 80    # node height

    # ── NODE: User ─────────────────────────────────────────────────────────────
    d += node(CX - NW//2, y_user, NW, NH, "End User / Application", "Chat · API · Copilot · Portal", BLUE)
    d += arrow(CX, y_user + NH, CX, y_app - 10, BLUE, label="User Query")

    # ── NODE: Enterprise App ──────────────────────────────────────────────────
    d += node(CX - NW//2, y_app, NW, NH, "Enterprise Application Layer",
              "Chatbot · Internal Tool · Customer Portal", DBLUE)
    d += arrow(CX, y_app + NH, CX, y_gateway - 10, BLUE)

    # ── NODE: TrustLayer API Gateway ──────────────────────────────────────────
    d += rect(CX - 200, y_gateway, 400, 90, BLUE, rx=10)
    d += text(CX, y_gateway + 32, "TrustLayer API Gateway", WHITE, 14, bold=True)
    d += text(CX, y_gateway + 54, "Zero-code interception · LLM-agnostic routing", WHITE, 10)
    d += text(CX, y_gateway + 73, "Latency overhead: < 2ms", LBLUE, 10)

    # ── Two arrows from gateway ────────────────────────────────────────────────
    # Left → LLM
    d += arrow_path(f"M {CX-100} {y_gateway+90} L {CX-230} {y_llm}", BLUE)
    # Right → Detection Engine
    d += arrow_path(f"M {CX+100} {y_gateway+90} L {CX+230} {y_det}", ORANGE)

    # ── NODE: LLM Provider (left) ─────────────────────────────────────────────
    lx = CX - 430
    d += node(lx, y_llm, 200, NH, "LLM Provider", "OpenAI · Anthropic · Google · Azure", PURPLE)
    d += text(lx + 100, y_llm - 20, "Query forwarded", GRAY, 10)

    # ── NODE: Detection Engine (right) ────────────────────────────────────────
    rx = CX + 230
    d += rect(rx, y_det, 220, 260, CARD, rx=10, stroke=ORANGE, sw=1.5)
    d += rect(rx, y_det, 220, 6, ORANGE, rx=0)
    d += text(rx + 110, y_det + 28, "Detection Engine", WHITE, 13, bold=True)
    d += text(rx + 110, y_det + 46, "8 algorithms in parallel", GRAY, 10)

    algos = [
        ("Semantic Entropy",   BLUE),
        ("Self-Consistency",   DBLUE),
        ("Citation Verify",    TEAL),
        ("Enterprise Grounding", GREEN),
        ("Claim Extraction",   ORANGE),
        ("Pattern Recognition",PURPLE),
        ("Temporal Check",     BLUE),
        ("Numerical Validation",RED),
    ]
    for i, (name, col) in enumerate(algos):
        row = i % 4
        col_n = i // 4
        ax = rx + 8 + col_n * 108
        ay = y_det + 62 + row * 48
        d += rect(ax, ay, 103, 38, CARD2, rx=6, stroke=col, sw=1)
        d += text(ax + 51, ay + 19, name, WHITE, 9)

    # ── LLM response arrow ────────────────────────────────────────────────────
    d += arrow_path(f"M {lx+100} {y_llm+NH} L {CX-50} {y_raw}", PURPLE)
    d += text(lx + 130, y_llm + NH + 30, "Raw LLM response", GRAY, 10, anchor="start")

    # ── Detection results arrow ───────────────────────────────────────────────
    d += arrow_path(f"M {rx+110} {y_det+260} L {CX+50} {y_raw}", ORANGE)

    # ── NODE: Scoring Model ───────────────────────────────────────────────────
    d += node(CX - NW//2, y_score, NW, NH,
              "Ensemble Scoring Model",
              "Confidence Score (0-100)  ·  Risk Score (0-100)", TEAL)
    d += arrow(CX, y_raw - 10, CX, y_score - 10, TEAL, label="Scores aggregated")

    # invisible join node at y_raw
    d += rect(CX - 160, y_raw - 30, 320, 30, CARD, rx=6, stroke=GRAY, sw=1)
    d += text(CX, y_raw - 15, "Raw response + 8 technique scores converge", GRAY, 10)

    d += arrow(CX, y_score + NH, CX, y_diamond - 40, TEAL)

    # ── DECISION DIAMOND ──────────────────────────────────────────────────────
    dcy = y_diamond
    d += (f'<polygon points="{CX},{dcy} {CX+110},{dcy+60} {CX},{dcy+120} {CX-110},{dcy+60}" '
          f'fill="{CARD}" stroke="{WHITE}" stroke-width="2"/>')
    d += text(CX, dcy + 60, "Decision Engine", WHITE, 13, bold=True)

    # ── Three action paths ────────────────────────────────────────────────────
    AW, AH = 200, 80

    # PASS (left)
    px = CX - 370
    d += arrow_path(f"M {CX-110} {dcy+60} L {px+AW//2} {y_actions}", GREEN)
    d += rect(px, y_actions, AW, AH, GREEN, rx=10)
    d += text(px + AW//2, y_actions + 26, "PASS", WHITE, 20, bold=True)
    d += text(px + AW//2, y_actions + 52, "Confidence ≥ 75%", WHITE, 10)
    d += text(px + AW//2, y_actions + 66, "Risk < 30", WHITE, 10)

    # FLAG (center)
    d += arrow(CX, dcy + 120, CX, y_actions, ORANGE)
    d += rect(CX - AW//2, y_actions, AW, AH, ORANGE, rx=10)
    d += text(CX, y_actions + 26, "FLAG", WHITE, 20, bold=True)
    d += text(CX, y_actions + 52, "Confidence 50–74%", WHITE, 10)
    d += text(CX, y_actions + 66, "Risk 30–59", WHITE, 10)

    # BLOCK (right)
    bx = CX + 170
    d += arrow_path(f"M {CX+110} {dcy+60} L {bx+AW//2} {y_actions}", RED)
    d += rect(bx, y_actions, AW, AH, RED, rx=10)
    d += text(bx + AW//2, y_actions + 26, "BLOCK", WHITE, 20, bold=True)
    d += text(bx + AW//2, y_actions + 52, "Confidence < 50%", WHITE, 10)
    d += text(bx + AW//2, y_actions + 66, "Risk ≥ 60", WHITE, 10)

    # ── Outcome nodes ─────────────────────────────────────────────────────────
    OW, OH = 200, 80

    # PASS outcome
    d += arrow(px + AW//2, y_actions + AH, px + OW//2, y_outcomes, GREEN)
    d += rect(px, y_outcomes, OW, OH, CARD, rx=8, stroke=GREEN, sw=2)
    d += text(px + OW//2, y_outcomes + 22, "Response Delivered", GREEN, 12, bold=True)
    d += text(px + OW//2, y_outcomes + 42, "to User", GREEN, 12, bold=True)
    d += text(px + OW//2, y_outcomes + 60, "Full audit logged", GRAY, 10)

    # FLAG outcome
    d += arrow(CX, y_actions + AH, CX, y_outcomes, ORANGE)
    d += rect(CX - OW//2, y_outcomes, OW, OH, CARD, rx=8, stroke=ORANGE, sw=2)
    d += text(CX, y_outcomes + 22, "Human Review", ORANGE, 12, bold=True)
    d += text(CX, y_outcomes + 42, "Queue (SLA tracked)", ORANGE, 12, bold=True)
    d += text(CX, y_outcomes + 60, "Reviewer notified", GRAY, 10)

    # BLOCK outcome
    d += arrow(bx + AW//2, y_actions + AH, bx + OW//2, y_outcomes, RED)
    d += rect(bx, y_outcomes, OW, OH, CARD, rx=8, stroke=RED, sw=2)
    d += text(bx + OW//2, y_outcomes + 22, "Fallback Delivered", RED, 12, bold=True)
    d += text(bx + OW//2, y_outcomes + 42, "Incident Logged", RED, 12, bold=True)
    d += text(bx + OW//2, y_outcomes + 60, "Specialist routed", GRAY, 10)

    # FLAG → user after review
    d += arrow(CX, y_outcomes + OH, CX, y_audit - 20, ORANGE, dashed=True,
               label="After approval")

    # ── All paths → Audit ─────────────────────────────────────────────────────
    d += rect(CX - 270, y_audit - 10, 540, 70, CARD, rx=10, stroke=TEAL, sw=1.5)
    d += rect(CX - 270, y_audit - 10, 540, 6, TEAL, rx=0)
    d += text(CX, y_audit + 24, "Immutable Audit Log + Compliance Documentation", WHITE, 13, bold=True)
    d += text(CX, y_audit + 46, "Every interaction logged · EU AI Act tags · Dashboard updated · Alerts fired", GRAY, 10)

    # three lines to audit
    for ox in [px + OW//2, bx + OW//2]:
        d += arrow(ox, y_outcomes + OH, ox, y_audit - 10, TEAL, dashed=True)

    # ── Key stats bar ─────────────────────────────────────────────────────────
    d += rect(0, y_final, W, 80, DBLUE, rx=0)
    stats = [("92%", "Catch Rate"), ("<100ms", "Latency"), ("<3%", "False Pos."),
             ("99.9%", "Uptime"), (">400%", "ROI")]
    for i, (val, lbl) in enumerate(stats):
        sx = 80 + i * 168
        d += text(sx, y_final + 28, val, WHITE, 20, bold=True)
        d += text(sx, y_final + 56, lbl, LBLUE, 11)

    return wrap(d, W, H, "TrustLayer AI — End User Flow")


# ═════════════════════════════════════════════════════════════════════════════
# DIAGRAM 2 — HLD ARCHITECTURE
# ═════════════════════════════════════════════════════════════════════════════

def diagram_hld():
    W, H = 1400, 940

    arrow_colors = ["0066FF", "00B894", "E74C3C", "F39C12", "27AE60", "8E44AD"]
    d = defs(*arrow_colors)

    # ── Title bar ─────────────────────────────────────────────────────────────
    d += rect(0, 0, W, 60, DBLUE, rx=0)
    d += text(W//2, 30, "TrustLayer AI — High-Level Design (HLD) Architecture", WHITE, 22, bold=True)

    # ── Layer backgrounds ─────────────────────────────────────────────────────
    # Layer 1: Enterprise
    d += rect(20, 75, W - 40, 120, "#0A1528", rx=10, stroke="#1E3A5F", sw=1)
    d += section_label(40, 98, "LAYER 1 — ENTERPRISE APPLICATIONS", BLUE)

    # Layer 2: TrustLayer Platform (main)
    d += rect(20, 215, W - 40, 420, "#0A2018", rx=10, stroke=TEAL, sw=1.5)
    d += section_label(40, 238, "LAYER 2 — TRUSTLAYER AI PLATFORM", TEAL)

    # Layer 3: External Services
    d += rect(20, 655, W - 40, 200, "#1A0F25", rx=10, stroke=PURPLE, sw=1)
    d += section_label(40, 678, "LAYER 3 — EXTERNAL SERVICES & DATA SOURCES", PURPLE)

    # ── Enterprise Apps (Layer 1) ─────────────────────────────────────────────
    apps = [
        ("Customer Chatbot",   "Web / Mobile"),
        ("Internal Copilot",   "Employee tools"),
        ("API Consumers",      "Partner integrations"),
        ("Document AI",        "Contract / Reports"),
        ("Decision Support",   "Analytics"),
    ]
    for i, (name, sub) in enumerate(apps):
        ax = 40 + i * 265
        d += node(ax, 110, 240, 70, name, sub, BLUE)

    # ── TrustLayer Platform components (Layer 2) ──────────────────────────────
    # API Gateway
    d += rect(40, 260, 300, 100, CARD, rx=10, stroke=TEAL, sw=1.5)
    d += rect(40, 260, 300, 6, TEAL, rx=0)
    d += text(190, 295, "API Gateway", WHITE, 15, bold=True)
    d += text(190, 318, "FastAPI · Load Balancer · Rate Limiter", GRAY, 10)
    d += text(190, 334, "Zero-code integration mode", LGRAY, 10)
    d += text(190, 350, "Latency: <2ms", TEAL, 10)

    # Detection Engine (center, large)
    d += rect(380, 260, 540, 350, CARD, rx=10, stroke=ORANGE, sw=1.5)
    d += rect(380, 260, 540, 6, ORANGE, rx=0)
    d += text(650, 292, "Detection Engine (8 Parallel Algorithms)", WHITE, 14, bold=True)
    d += text(650, 310, "Ensemble scoring · <80ms pipeline", GRAY, 10)

    det_items = [
        ("Semantic Entropy",   BLUE,   450, 340),
        ("Self-Consistency",   DBLUE,  640, 340),
        ("Citation Verify",    TEAL,   830, 340),
        ("Enterprise Grounding",GREEN,  450, 415),
        ("Claim Extraction",   ORANGE, 640, 415),
        ("Pattern Recognition",PURPLE, 830, 415),
        ("Temporal Check",     BLUE,   450, 490),
        ("Numerical Validation",RED,   640, 490),
    ]
    for name, col, dx, dy in det_items:
        d += rect(dx, dy, 165, 55, CARD2, rx=8, stroke=col, sw=1)
        d += text(dx + 82, dy + 20, name, WHITE, 11, bold=True)
        d += text(dx + 82, dy + 38, "Independent algorithm", GRAY, 9)

    # Scoring & Decision
    d += rect(960, 260, 200, 100, CARD, rx=10, stroke=TEAL, sw=1.5)
    d += rect(960, 260, 200, 6, TEAL, rx=0)
    d += text(1060, 295, "Scoring Model", WHITE, 13, bold=True)
    d += text(1060, 315, "Weighted ensemble", GRAY, 10)
    d += text(1060, 333, "Confidence + Risk", TEAL, 10)
    d += text(1060, 350, "Scores 0–100", LGRAY, 10)

    # Action Policy
    d += rect(960, 390, 200, 100, CARD, rx=10, stroke=BLUE, sw=1.5)
    d += rect(960, 390, 200, 6, BLUE, rx=0)
    d += text(1060, 425, "Action Policy", WHITE, 13, bold=True)
    d += text(1060, 445, "PASS / FLAG / BLOCK", BLUE, 11, bold=True)
    d += text(1060, 464, "Threshold engine", GRAY, 10)
    d += text(1060, 480, "Configurable per industry", LGRAY, 10)

    # Audit & Compliance
    d += rect(1200, 260, 180, 350, CARD, rx=10, stroke=GREEN, sw=1.5)
    d += rect(1200, 260, 180, 6, GREEN, rx=0)
    d += text(1290, 310, "Audit &", WHITE, 13, bold=True)
    d += text(1290, 330, "Compliance", WHITE, 13, bold=True)
    d += text(1290, 360, "Immutable log", GRAY, 10)
    d += text(1290, 380, "EU AI Act tags", GRAY, 10)
    d += text(1290, 400, "NIST mapping", GRAY, 10)
    d += text(1290, 420, "ISO 42001", GRAY, 10)
    d += text(1290, 440, "SOC 2 Type II", GRAY, 10)
    d += text(1290, 468, "Auto-reports", TEAL, 10)
    d += text(1290, 488, "Dashboard", TEAL, 10)
    d += text(1290, 508, "Alerting", TEAL, 10)

    # ── Internal arrows (Layer 2) ─────────────────────────────────────────────
    d += arrow(340, 310, 380, 380, TEAL)                    # Gateway → Detection
    d += arrow(920, 430, 960, 295, ORANGE)                  # Detection → Scoring
    d += arrow(1060, 360, 1060, 390, TEAL)                  # Scoring → Action
    d += arrow(1160, 430, 1200, 430, BLUE)                  # Action → Audit
    d += arrow(380, 500, 960, 500, ORANGE, dashed=True)     # Detection → Action (shortcut)

    # ── External layer (Layer 3) ──────────────────────────────────────────────
    ext_groups = [
        ("LLM Providers", PURPLE,
         ["OpenAI GPT-4/4o", "Anthropic Claude 4", "Google Gemini", "Azure OpenAI", "AWS Bedrock"]),
        ("Enterprise Data", BLUE,
         ["Salesforce CRM", "SAP ERP", "Core Banking", "HRIS / ADP", "ServiceNow"]),
        ("Legal & Medical", TEAL,
         ["Westlaw", "LexisNexis", "FDA Databases", "PubMed", "CourtListener"]),
        ("Compliance DBs", GREEN,
         ["EU AI Act Registry", "NIST Framework", "Regulatory Updates", "Audit Repository", "SOC 2 Evidence"]),
        ("Infrastructure", ORANGE,
         ["Kubernetes (EKS)", "Redis Cache", "PostgreSQL", "TimescaleDB", "GitHub Actions"]),
    ]
    for i, (name, col, items) in enumerate(ext_groups):
        gx = 30 + i * 272
        d += rect(gx, 690, 252, 150, CARD, rx=8, stroke=col, sw=1.5)
        d += rect(gx, 690, 252, 6, col, rx=0)
        d += text(gx + 126, 716, name, WHITE, 12, bold=True)
        for j, item in enumerate(items):
            d += text(gx + 126, 740 + j * 22, item, GRAY, 10)

    # ── Vertical arrows (between layers) ─────────────────────────────────────
    # Enterprise → Gateway
    for i in range(5):
        ax = 160 + i * 265
        d += arrow(ax, 180, ax if ax < 340 else 340 if ax > 340 else ax,
                   260, BLUE, dashed=True)
    d += arrow(160, 180, 190, 260, BLUE)
    d += arrow(425, 180, 350, 260, BLUE)
    d += arrow(690, 180, 650, 260, BLUE)
    d += arrow(955, 180, 800, 260, BLUE)
    d += arrow(1220, 180, 960, 360, BLUE)

    # LLM ↕ Gateway
    d += arrow(156, 655, 156, 610, PURPLE)
    d += text(100, 640, "LLM response", GRAY, 9)
    d += arrow(190, 355, 190, 690, PURPLE, dashed=True)
    d += text(195, 672, "LLM query forwarded", GRAY, 9)

    # Enterprise Data → Detection
    d += arrow(396, 655, 650, 610, BLUE, dashed=True)
    # Legal → Detection
    d += arrow(666, 655, 750, 610, TEAL, dashed=True)
    # Compliance → Audit
    d += arrow(1026, 655, 1290, 610, GREEN, dashed=True)
    # Infra ↔ All
    d += arrow(1298, 655, 1298, 610, ORANGE, dashed=True)

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_items = [
        ("Query / Response flow", BLUE),
        ("Detection pipeline",    ORANGE),
        ("Compliance flow",       GREEN),
        ("Data grounding",        TEAL),
        ("External dependency",   PURPLE),
    ]
    d += rect(20, 870, W - 40, 55, CARD, rx=6)
    for i, (lbl, col) in enumerate(legend_items):
        lx = 60 + i * 268
        d += rect(lx, 888, 30, 4, col, rx=2)
        d += text(lx + 38, 892, lbl, GRAY, 11, anchor="start")

    return wrap(d, W, H, "TrustLayer AI — HLD Architecture")


# ═════════════════════════════════════════════════════════════════════════════
# DIAGRAM 3 — LLD ARCHITECTURE
# ═════════════════════════════════════════════════════════════════════════════

def diagram_lld():
    W, H = 1600, 1080

    arrow_colors = ["0066FF", "00B894", "E74C3C", "F39C12", "27AE60", "8E44AD", "003388", "CBD5E1"]
    d = defs(*arrow_colors)

    # ── Title ─────────────────────────────────────────────────────────────────
    d += rect(0, 0, W, 56, DBLUE, rx=0)
    d += text(W//2, 28, "TrustLayer AI — Low-Level Design (LLD) Architecture", WHITE, 22, bold=True)

    # ── Zone boxes ────────────────────────────────────────────────────────────
    # Client zone
    d += rect(10, 64, 220, 160, "#080F1E", rx=8, stroke="#1E3A5F", sw=1)
    d += section_label(22, 82, "CLIENT ZONE", BLUE)

    # Ingress zone
    d += rect(240, 64, 260, 160, "#070F1A", rx=8, stroke=BLUE, sw=1)
    d += section_label(252, 82, "INGRESS", BLUE)

    # Core processing zone
    d += rect(510, 64, 700, 580, "#06130E", rx=8, stroke=TEAL, sw=2)
    d += section_label(524, 82, "CORE PROCESSING  (Kubernetes Namespace: trustlayer-core)", TEAL)

    # Data zone
    d += rect(1220, 64, 370, 580, "#0D0A18", rx=8, stroke=PURPLE, sw=1)
    d += section_label(1232, 82, "DATA & PERSISTENCE", PURPLE)

    # External zone (bottom)
    d += rect(10, 660, 1580, 340, "#0D1020", rx=8, stroke=GRAY, sw=1)
    d += section_label(24, 678, "EXTERNAL INTEGRATIONS", GRAY)

    # Observability (right top)
    d += rect(1220, 654, 370, 346, "#0D1220", rx=8, stroke=ORANGE, sw=1)
    d += section_label(1232, 672, "OBSERVABILITY", ORANGE)

    # ── CLIENT ZONE ───────────────────────────────────────────────────────────
    d += rect(20, 95, 200, 50, CARD, rx=8, stroke=BLUE, sw=1)
    d += text(120, 120, "Web / Mobile Client", WHITE, 11, bold=True)

    d += rect(20, 155, 200, 50, CARD, rx=8, stroke=BLUE, sw=1)
    d += text(120, 180, "API Consumer / SDK", WHITE, 11, bold=True)

    # ── INGRESS ───────────────────────────────────────────────────────────────
    d += rect(250, 95, 240, 50, CARD, rx=8, stroke=BLUE, sw=1.5)
    d += text(370, 120, "TLS Termination", WHITE, 11, bold=True)
    d += text(370, 133, "nginx / AWS ALB", GRAY, 9)

    d += rect(250, 155, 240, 50, CARD, rx=8, stroke=TEAL, sw=1.5)
    d += text(370, 180, "FastAPI Gateway", WHITE, 11, bold=True)
    d += text(370, 193, "Rate limiter · Auth · Routing", GRAY, 9)

    # ── CORE PROCESSING ───────────────────────────────────────────────────────
    # Orchestrator pod
    d += rect(525, 95, 220, 65, CARD, rx=8, stroke=TEAL, sw=1.5)
    d += rect(525, 95, 220, 5, TEAL, rx=0)
    d += text(635, 120, "Detection Orchestrator", WHITE, 12, bold=True)
    d += text(635, 138, "asyncio · concurrent.futures", GRAY, 9)
    d += text(635, 152, "Manages parallel execution", GRAY, 9)

    # 8 detection pods
    det_pods = [
        ("Semantic\nEntropy", BLUE,   "HuggingFace\nTransformers", "87% · 45ms"),
        ("Self-\nConsistency", DBLUE, "LLM sampling\n+ embeddings",  "82% · 120ms"),
        ("Citation\nVerify",   TEAL,  "Westlaw/LexisNexis\nAPI client","95% · 200ms"),
        ("Enterprise\nGrounding",GREEN,"CRM / ERP\nConnector pool", "98% · 150ms"),
        ("Claim\nExtraction",  ORANGE,"spaCy NER\n+ classifier",    "91% · 35ms"),
        ("Pattern\nRecognition",PURPLE,"Fine-tuned\nRoBERTa",       "79% · 25ms"),
        ("Temporal\nCheck",    BLUE,  "Real-time\nfeed adapter",    "93% · 40ms"),
        ("Numerical\nValidation",RED, "Regex + NER\npipeline",      "96% · 80ms"),
    ]
    pods_per_row = 4
    for i, (name, col, tech, perf) in enumerate(det_pods):
        row = i // pods_per_row
        col_n = i % pods_per_row
        px = 525 + col_n * 170
        py = 185 + row * 140
        d += rect(px, py, 155, 120, CARD, rx=8, stroke=col, sw=1.5)
        d += rect(px, py, 155, 5, col, rx=0)
        d += text(px + 77, py + 28, name.replace("\n", " "), WHITE, 11, bold=True)
        d += text(px + 77, py + 52, tech.replace("\n", " / "), GRAY, 9)
        d += text(px + 77, py + 72, "──────────────", GRAY, 8)
        d += text(px + 77, py + 90, perf, col, 10, bold=True)
        d += text(px + 77, py + 108, "K8s Pod · HPA enabled", GRAY, 8)

    # Ensemble Scoring Service
    d += rect(525, 480, 340, 80, CARD, rx=8, stroke=TEAL, sw=1.5)
    d += rect(525, 480, 340, 5, TEAL, rx=0)
    d += text(695, 506, "Ensemble Scoring Service", WHITE, 13, bold=True)
    d += text(695, 526, "scikit-learn · Weighted average · grounding_multiplier", GRAY, 9)
    d += text(695, 544, "Output: confidence_score (0-100) + risk_score (0-100)", TEAL, 9)

    # Action Policy Engine
    d += rect(895, 480, 295, 80, CARD, rx=8, stroke=BLUE, sw=1.5)
    d += rect(895, 480, 295, 5, BLUE, rx=0)
    d += text(1042, 506, "Action Policy Engine", WHITE, 13, bold=True)
    d += text(1042, 526, "Rule engine · Threshold config · Industry weights", GRAY, 9)
    d += text(1042, 544, "PASS  |  FLAG  |  BLOCK", BLUE, 10, bold=True)

    # Fallback Handler
    d += rect(895, 580, 295, 60, CARD, rx=8, stroke=RED, sw=1)
    d += text(1042, 610, "Fallback Handler", WHITE, 11, bold=True)
    d += text(1042, 626, "Specialist routing · Message templating", GRAY, 9)

    # Arrows inside core
    d += arrow(635, 160, 635, 185, TEAL)
    # Orchestrator → each pod (simplified)
    for i in range(8):
        row = i // pods_per_row
        col_n = i % pods_per_row
        px = 525 + col_n * 170 + 77
        py = 185 + row * 140
        d += arrow(635, 160, px, py, TEAL, dashed=True)

    # Pods → Scoring
    d += arrow(695, 465, 695, 480, ORANGE)
    d += arrow(1042, 465, 870, 510, ORANGE, dashed=True)

    d += arrow(865, 520, 895, 520, TEAL)
    d += arrow(1042, 560, 1042, 580, RED, dashed=True)

    # ── DATA & PERSISTENCE ────────────────────────────────────────────────────
    data_services = [
        ("PostgreSQL 15", PURPLE,    "Audit log store\nAppend-only · Partitioned\nRetention: 7 years",    95),
        ("Redis 7",       ORANGE,    "Enterprise data cache\nTTL-based freshness\nHit rate: ~85%",        215),
        ("TimescaleDB",   TEAL,      "Time-series metrics\nDetection rate trends\nReal-time charts",       335),
        ("pgvector",      BLUE,      "Vector store\nSemantic similarity\nEmbedding search",               455),
        ("S3 / Blob",     GREEN,     "Compliance reports\nAudit exports\nPDF / JSON artifacts",          575),
    ]
    for name, col, desc, dy in data_services:
        d += rect(1230, dy, 350, 105, CARD, rx=8, stroke=col, sw=1.5)
        d += rect(1230, dy, 350, 5, col, rx=0)
        d += text(1405, dy + 28, name, WHITE, 12, bold=True)
        for j, line in enumerate(desc.split("\n")):
            d += text(1405, dy + 52 + j * 18, line, GRAY, 10)

    # ── OBSERVABILITY ─────────────────────────────────────────────────────────
    obs = [
        ("Prometheus", ORANGE, "Metrics scraping · Service health"),
        ("Grafana",    ORANGE, "Real-time dashboards · Alerting"),
        ("OpenTelemetry",GRAY, "Distributed tracing · Spans"),
        ("PagerDuty",  RED,    "On-call alerting · Incident mgmt"),
    ]
    for i, (name, col, desc) in enumerate(obs):
        d += rect(1230, 695 + i * 73, 350, 60, CARD, rx=6, stroke=col, sw=1)
        d += text(1405, 718 + i * 73, name, WHITE, 12, bold=True)
        d += text(1405, 736 + i * 73, desc, GRAY, 9)

    # ── EXTERNAL INTEGRATIONS ─────────────────────────────────────────────────
    ext = [
        ("OpenAI / Anthropic\n/ Google / Azure", PURPLE, "LLM Providers"),
        ("Salesforce · SAP\nWorkday · ServiceNow",BLUE,   "CRM / ERP / HRIS"),
        ("Westlaw · LexisNexis\nCourtListener",   TEAL,  "Legal Databases"),
        ("FDA APIs · Epic\nCerner · PubMed",      RED,   "Healthcare Data"),
        ("Bloomberg · Reuters\nCore Banking APIs",ORANGE,"Financial Data"),
        ("Active Directory\nOkta · Azure AD",     GREEN, "Identity Providers"),
    ]
    for i, (name, col, cat) in enumerate(ext):
        ex = 20 + i * 205
        d += rect(ex, 695, 190, 120, CARD, rx=8, stroke=col, sw=1.5)
        d += rect(ex, 695, 190, 5, col, rx=0)
        d += text(ex + 95, 720, cat, col, 11, bold=True)
        for j, line in enumerate(name.split("\n")):
            d += text(ex + 95, 748 + j * 20, line, GRAY, 10)

    # Connector hub
    d += rect(20, 835, 1190, 55, "#0A1020", rx=6, stroke=GRAY, sw=1)
    d += text(605, 862, "Connector Pool  ·  Read-only  ·  TTL-cached  ·  Least-privilege credentials  ·  Encrypted in transit", GRAY, 10)

    # ── KEY ARROWS across zones ───────────────────────────────────────────────
    # Client → TLS
    d += arrow(220, 120, 250, 120, BLUE)
    d += arrow(220, 180, 250, 180, BLUE)
    # TLS → FastAPI
    d += arrow(370, 145, 370, 155, BLUE)
    # FastAPI → Orchestrator
    d += arrow(490, 180, 525, 128, TEAL)
    # Action → Audit (PostgreSQL)
    d += arrow(1190, 510, 1230, 145, GREEN, dashed=True)
    # Action → Observability
    d += arrow(1190, 540, 1230, 720, ORANGE, dashed=True)
    # External → Grounding pod
    d += arrow(520, 835, 700, 465, TEAL, dashed=True)
    d += arrow(520, 835, 530, 280, TEAL, dashed=True)

    # ── Version / footer ──────────────────────────────────────────────────────
    d += text(W - 20, H - 12, "TrustLayer AI · Infosys Business Incubator Cohort 2 · v1.0", GRAY, 10, anchor="end")

    return wrap(d, W, H, "TrustLayer AI — LLD Architecture")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    files = [
        (r"C:\aiprojects\aitrust\diagram_1_end_user_flow.svg",  diagram_end_user_flow),
        (r"C:\aiprojects\aitrust\diagram_2_hld_architecture.svg", diagram_hld),
        (r"C:\aiprojects\aitrust\diagram_3_lld_architecture.svg", diagram_lld),
    ]
    for path, fn in files:
        svg = fn()
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"  Saved: {path}")
    print("\nAll 3 SVG diagrams generated.")
