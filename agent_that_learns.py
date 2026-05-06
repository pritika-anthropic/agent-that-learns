"""
Build an AI Agent That Learns From Its Mistakes
================================================

A self-improving customer discovery agent built with Claude's API.

THE PATTERN:
1. Run an agent on real tasks (messy customer notes)
2. Grade its outputs automatically (Claude-as-Judge)
3. Identify recurring failure patterns
4. Generate an improved prompt targeting those failures
5. Generate new test cases that catch regressions
6. Rerun and measure the improvement

COST: ~$0.50 per full run | TIME: ~3 minutes | MODEL: Claude Sonnet 4.6

Built by Pritika Mehta (YC S20) | Anthropic Applied AI, Startups
"""

import anthropic
import json
import os
import time
import sys
from datetime import datetime

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


# ═══════════════════════════════════════════════════════════════
# TERMINAL COLORS
# ═══════════════════════════════════════════════════════════════

class C:
    BOLD = "\033[1m"; DIM = "\033[2m"; ITALIC = "\033[3m"; UNDERLINE = "\033[4m"
    RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"; BLUE = "\033[94m"
    MAGENTA = "\033[95m"; CYAN = "\033[96m"; WHITE = "\033[97m"; GRAY = "\033[90m"
    RESET = "\033[0m"
    @staticmethod
    def disable():
        for attr in dir(C):
            if attr.isupper() and not attr.startswith('_'): setattr(C, attr, "")

if not sys.stdout.isatty(): C.disable()


# ═══════════════════════════════════════════════════════════════
# HTML REPORT
# ═══════════════════════════════════════════════════════════════

class HTMLReport:
    def __init__(self):
        self.sections = []

    def add(self, html):
        self.sections.append(html)

    def save(self, filename="report.html"):
        body = ''.join(self.sections)
        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent That Learns — Results</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f0f0f;color:#e5e5e5;padding:2rem;max-width:900px;margin:0 auto;line-height:1.6}}
.hero{{text-align:center;padding:2rem 0 1.5rem;border-bottom:1px solid #2a2a2a;margin-bottom:2rem}}
.hero h1{{font-size:1.8rem;color:#fff;margin-bottom:.3rem}}
.hero p{{color:#888;font-size:.85rem}}
h2{{font-size:1.1rem;color:#fff;margin:2rem 0 1rem;padding:.5rem 0;border-bottom:1px solid #2a2a2a}}
.stats{{display:flex;gap:1.5rem;margin:1rem 0;flex-wrap:wrap}}
.stat{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;padding:16px 20px;flex:1;min-width:120px;text-align:center}}
.stat-val{{font-size:2rem;font-weight:700;color:#fff}}.stat-val span{{font-size:1rem;color:#888}}
.stat-lbl{{font-size:.7rem;color:#888;text-transform:uppercase;letter-spacing:.05em;margin-top:2px}}
.card{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;margin:.75rem 0;overflow:hidden}}
.card-h{{display:flex;align-items:center;gap:10px;padding:12px 16px;background:#151515;border-bottom:1px solid #2a2a2a;cursor:pointer}}
.card-h:hover{{background:#1f1f1f}}
.card-b{{padding:14px 16px;display:none}}
.card-b.open{{display:block}}
.badge{{font-size:.7rem;font-weight:600;padding:2px 8px;border-radius:12px}}
.b-hot{{background:#dc262620;color:#f87171;border:1px solid #dc262640}}
.b-warm{{background:#eab30820;color:#fbbf24;border:1px solid #eab30840}}
.b-cold{{background:#3b82f620;color:#60a5fa;border:1px solid #3b82f640}}
.b-dis{{background:#6b728020;color:#9ca3af;border:1px solid #6b728040}}
.b-pass{{background:#16a34a20;color:#4ade80;border:1px solid #16a34a40}}
.b-fail{{background:#dc262620;color:#f87171;border:1px solid #dc262640}}
.note-id{{font-weight:600;color:#fff;font-size:.8rem}}
.conf{{margin-left:auto;color:#888;font-size:.75rem}}
.field{{margin-bottom:10px}}.field label{{font-size:.7rem;font-weight:600;color:#888;text-transform:uppercase;display:block;margin-bottom:4px}}
.field p,.field li{{font-size:.8rem;color:#ccc}}
.field ul{{padding-left:1rem}}.green{{color:#4ade80}}.red{{color:#f87171}}.purple{{color:#a78bfa}}
.bar-row{{display:flex;align-items:center;gap:10px;margin:4px 0}}
.bar-name{{width:150px;font-size:.75rem;color:#aaa}}
.bar-bg{{flex:1;height:7px;background:#2a2a2a;border-radius:4px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:4px}}
.bar-score{{width:28px;font-size:.75rem;color:#fff;text-align:right}}
table{{width:100%;border-collapse:collapse;margin:.75rem 0}}
th{{text-align:left;padding:8px 12px;background:#151515;color:#888;font-size:.75rem;text-transform:uppercase;border-bottom:1px solid #2a2a2a}}
td{{padding:8px 12px;font-size:.8rem;border-bottom:1px solid #1f1f1f}}
.pos{{color:#4ade80;font-weight:600}}.neg{{color:#f87171;font-weight:600}}
.failure-item{{display:flex;justify-content:space-between;padding:5px 10px;background:#15151580;border-radius:5px;margin:3px 0;font-size:.8rem}}
.failure-mode{{color:#f87171}}.failure-count{{color:#888}}
.summary{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;padding:20px;margin:1rem 0;font-size:.85rem;color:#ccc;white-space:pre-line}}
</style>
<script>
function toggle(el){{var b=el.nextElementSibling;b.classList.toggle('open')}}
</script>
</head><body>
{body}
</body></html>"""
        with open(filename, 'w') as f:
            f.write(html)
        return filename


# ═══════════════════════════════════════════════════════════════
# PART 1: THE AGENT
# ═══════════════════════════════════════════════════════════════
# V1 prompt is DELIBERATELY simplified — it lacks nuanced
# instructions for handling enterprise stalls, scope creep,
# misleading enthusiasm, and unfunded founders. This ensures
# the agent fails on tricky notes, giving the feedback loop
# something to improve.

AGENT_SYSTEM_PROMPT_V1 = """You are a helpful customer discovery analyst for a startup.

Analyze the customer note and extract insights. Be encouraging — founders need motivation! Look for positive signals and opportunities.

Return ONLY valid JSON (no markdown, no code blocks):
{
    "note_id": "the note ID",
    "lead_quality": "hot | warm | cold | disqualify",
    "confidence": 0.0-1.0,
    "pain_points": ["pain points mentioned"],
    "pmf_signals": {
        "strong": ["positive signals"],
        "weak": ["concerns if any"]
    },
    "budget_indicators": {
        "existing_spend": "current spend",
        "willingness_to_pay": "pricing signals",
        "decision_timeline": "timeline"
    },
    "recommended_action": "next step",
    "what_not_to_build": "things to avoid building",
    "key_quote": "best quote"
}

If the customer expressed enthusiasm or interest, lean toward classifying them as warm or hot. Startups need pipeline!

Respond with ONLY the JSON object. No explanation, no markdown, no code blocks. Start your response with { and end with }."""


def run_agent(notes, system_prompt):
    results = []
    for note in notes:
        try:
            response = client.messages.create(
                model=MODEL, max_tokens=1500, temperature=0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Analyze this customer note:\n\n{json.dumps(note, indent=2)}"}
                ]
            )
            raw = response.content[0].text.strip()
            # Strip markdown wrapping if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw
                raw = raw.rsplit("```", 1)[0].strip()
            try:
                results.append(json.loads(raw))
            except json.JSONDecodeError:
                # Try to find JSON object in response
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start >= 0 and end > start:
                    try:
                        results.append(json.loads(raw[start:end]))
                    except:
                        results.append({"note_id": note["id"], "error": "json_parse_failed"})
                else:
                    results.append({"note_id": note["id"], "error": "json_parse_failed"})
        except Exception as e:
            results.append({"note_id": note["id"], "error": str(e)})
    return results


# ═══════════════════════════════════════════════════════════════
# PART 2: STRICT EVAL RUBRIC
# ═══════════════════════════════════════════════════════════════
# The rubric is INTENTIONALLY strict — it specifically penalizes:
# - Classifying enterprise stalls as "warm" (should be cold)
# - Missing scope creep red flags
# - Treating unfunded enthusiasm as "hot"
# - Generic recommendations that aren't time-bound
# - Missing the "what not to build" nuance

EVAL_RUBRIC = """You are an extremely strict evaluator. You have 15 years of YC startup experience. You grade HARD. Most analyses SHOULD fail.

SPECIFIC TRAPS TO CHECK — grade 1-2 on accuracy if agent misses these:
- note_002 (Mike, healthtech): MUST be COLD. He said "let me socialize internally," needs VP + legal approval, has 2-year competitor contract, budget not available until January. If agent scored warm or hot = accuracy 1.
- note_004 (Alex, DM): MUST be COLD or DISQUALIFY. He has 2 employees, launched 3 weeks ago, website is a landing page, no revenue, working on 2 other projects. Enthusiastic language masks zero ability to pay. If agent scored warm or hot = accuracy 1.
- note_007 (Raj, logistics): MUST be WARM at best, not HOT. He kept adding scope every 5 minutes and said "we'd want all of this working before we commit to paying." Classic scope creep stall. If agent scored hot = accuracy 2.
- note_009 (Maria, e-commerce): Should be WARM not HOT. Despite strong pain, she's evaluating 3 other vendors and the CFO was skeptical. If agent scored hot without flagging competition risk = accuracy 3.
- note_010 (Deepak, legal): Should be WARM not HOT. His cofounder wasn't on the call and is "cautious about switching." Missing co-founder buy-in is a blocker. If agent scored hot without flagging this = accuracy 3.

GENERAL RULES:
ACCURACY (1-5): Must nail classification. Enterprise stalls = COLD. Unfunded enthusiasm = COLD. Scope creep stalls = WARM at best. Missing stakeholder = WARM at best.
COMPLETENESS (1-5): Must catch ALL hidden red flags: competitor contracts, committee approvals, scope creep, runway concerns, missing stakeholders, competing vendors.
ACTIONABILITY (1-5): Must be executable in 2 HOURS. "Follow up" without WHO/WHAT/WHEN = score 2.
HONESTY (1-5): Must lead with blockers, not enthusiasm. If agent emphasized positive signals over structural blockers = score 2.
WHAT_NOT_TO_BUILD (1-5): Must identify specific distractions with reasoning. Generic = score 2. Must flag scope creep as a red flag.

OVERALL: Average the 5 scores. Pass = overall >= 4.0. Expect 40-60% of notes to FAIL.

Return ONLY valid JSON:
{
    "note_id": "from input",
    "scores": {
        "accuracy": {"score": 1-5, "reason": "one sentence"},
        "completeness": {"score": 1-5, "reason": "one sentence"},
        "actionability": {"score": 1-5, "reason": "one sentence"},
        "honesty": {"score": 1-5, "reason": "one sentence"},
        "what_not_to_build": {"score": 1-5, "reason": "one sentence"}
    },
    "overall_score": average of 5 scores rounded to nearest integer,
    "pass": true only if overall >= 4,
    "failure_mode": "null if passed. Use: over_optimistic_scoring | generic_recommendations | missed_red_flags | missed_scope_creep | missed_enterprise_stall | missed_funding_risk | weak_what_not_to_build | incomplete_extraction | missed_competing_vendors | missed_missing_stakeholder",
    "improvement_suggestion": "one surgical change to the agent's prompt"
}

Respond with ONLY the JSON object. No explanation, no markdown, no code blocks. Start your response with { and end with }."""


def evaluate_outputs(notes, agent_results):
    evals = []
    for note, result in zip(notes, agent_results):
        if "error" in result:
            evals.append({"note_id": note["id"], "overall_score": 0, "pass": False,
                          "failure_mode": "parse_error", "scores": {},
                          "improvement_suggestion": "Fix JSON formatting"})
            continue
        try:
            response = client.messages.create(
                model=MODEL, max_tokens=1000, temperature=0,
                system=EVAL_RUBRIC,
                messages=[
                    {"role": "user", "content": f"Original note:\n{json.dumps(note, indent=2)}\n\nAgent analysis:\n{json.dumps(result, indent=2)}"}
                ]
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw
                raw = raw.rsplit("```", 1)[0].strip()
            try:
                evals.append(json.loads(raw))
            except json.JSONDecodeError:
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start >= 0 and end > start:
                    try:
                        evals.append(json.loads(raw[start:end]))
                    except:
                        evals.append({"note_id": note["id"], "overall_score": 0, "pass": False, "failure_mode": "eval_parse_error"})
                else:
                    evals.append({"note_id": note["id"], "overall_score": 0, "pass": False, "failure_mode": "eval_parse_error"})
        except Exception as e:
            evals.append({"note_id": note["id"], "overall_score": 0, "pass": False, "failure_mode": "eval_error"})
    return evals


# ═══════════════════════════════════════════════════════════════
# PART 3: FEEDBACK LOOP
# ═══════════════════════════════════════════════════════════════

def analyze_failures(evals):
    failures = [e for e in evals if not e.get("pass", False)]
    if not failures:
        return {"status": "all_passed", "failure_patterns": [], "suggestions": []}
    failure_modes = {}
    suggestions = []
    low_dims = {d: [] for d in ['accuracy', 'completeness', 'actionability', 'honesty', 'what_not_to_build']}
    for f in failures:
        mode = f.get("failure_mode", "unknown")
        if mode and mode != "null": failure_modes[mode] = failure_modes.get(mode, 0) + 1
        s = f.get("improvement_suggestion", "")
        if s: suggestions.append(s)
        if "scores" in f:
            for dim, data in f["scores"].items():
                if isinstance(data, dict) and data.get("score", 5) <= 3:
                    low_dims[dim].append(data.get("reason", ""))
    return {
        "total_evaluated": len(evals), "total_passed": len(evals) - len(failures),
        "total_failed": len(failures),
        "pass_rate": f"{((len(evals) - len(failures)) / len(evals)) * 100:.0f}%",
        "failure_patterns": sorted(failure_modes.items(), key=lambda x: x[1], reverse=True),
        "weakest_dimensions": sorted([(d, len(r)) for d, r in low_dims.items() if r], key=lambda x: x[1], reverse=True),
        "suggestions": suggestions
    }


def generate_improved_prompt(original_prompt, failure_analysis, evals):
    failed = [e for e in evals if not e.get("pass", False)]
    response = client.messages.create(
        model=MODEL, max_tokens=3000, temperature=0.3,
        messages=[{"role": "user", "content": f"""You are a prompt engineering expert for customer discovery analysis.

CURRENT SYSTEM PROMPT (this is what the agent uses):
<current_prompt>{original_prompt}</current_prompt>

FAILURE ANALYSIS (patterns across all evaluations):
<failures>{json.dumps(failure_analysis, indent=2)}</failures>

SPECIFIC FAILED EVALUATIONS:
<failed>{json.dumps(failed, indent=2)}</failed>

Generate an IMPROVED system prompt that fixes EVERY identified failure.

Key improvements needed:
- If "over_optimistic_scoring" or "missed_enterprise_stall" appeared: add EXPLICIT rules for enterprise stall signals (checking with CTO, committee reviews, fiscal year timing = COLD)
- If "missed_scope_creep" appeared: add rules for detecting when leads pile on requirements before committing
- If "missed_funding_risk" appeared: add rules for evaluating founder credibility (revenue, funding, focus)
- If "generic_recommendations" appeared: add instruction that every recommendation must include WHO, WHAT, WHEN, and the exact message to send
- If "weak_what_not_to_build" appeared: add instruction to connect distractions to the startup's core value prop

RULES:
- Keep the SAME JSON output structure
- Be surgical — add specific rules targeting each failure mode
- Don't remove instructions that are already working
- The improved prompt should be comprehensive but not bloated

Return ONLY the improved system prompt. No explanation."""}]
    )
    return response.content[0].text


def generate_new_eval_cases(failure_analysis):
    response = client.messages.create(
        model=MODEL, max_tokens=2500, temperature=0.5,
        system="Respond with ONLY a valid JSON array. No markdown. Start with [ end with ].",
        messages=[{"role": "user", "content": f"""Generate 3 tricky customer notes that specifically test these failure patterns:
{json.dumps(failure_analysis, indent=2)}

Each note should contain SUBTLE signals that a weak agent would misclassify:
- Enterprise enthusiasm that masks structural blockers
- Founders who sound excited but have no funding or focus
- Leads with scope creep patterns disguised as interest
- Notes where the STATED sentiment contradicts the ACTUAL signals

Return: [{{"id":"eval_001","source":"user_interview","date":"2026-05-05","raw_text":"messy realistic note with typos and casual language","tests_failure_mode":"pattern","expected_lead_quality":"correct answer","expected_key_signal":"signal agent must catch"}}]"""}]
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"): raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try: return json.loads(raw)
    except:
        s, e = raw.find("["), raw.rfind("]") + 1
        if s >= 0 and e > s:
            try: return json.loads(raw[s:e])
            except: return []
        return []


# ═══════════════════════════════════════════════════════════════
# TERMINAL + HTML DISPLAY
# ═══════════════════════════════════════════════════════════════

def ph(t): print(f"\n{C.BOLD}{C.CYAN}{'═'*64}{C.RESET}\n  {C.BOLD}{C.WHITE}{t}{C.RESET}\n{C.CYAN}{'═'*64}{C.RESET}")
def ps(t): print(f"\n{C.DIM}{'─'*64}{C.RESET}\n  {C.BOLD}{t}{C.RESET}\n{C.DIM}{'─'*64}{C.RESET}")

def print_result(r, i):
    if "error" in r:
        print(f"\n  {C.RED}✗{C.RESET} {C.DIM}Note {r.get('note_id','?')}{C.RESET} — {C.RED}Error{C.RESET}")
        return
    colors = {"hot":C.RED,"warm":C.YELLOW,"cold":C.BLUE,"disqualify":C.GRAY}
    emoji = {"hot":"🔥","warm":"🟡","cold":"🔵","disqualify":"⛔"}
    q = r.get("lead_quality","?"); c = colors.get(q, C.WHITE)
    print(f"\n  {emoji.get(q,'❓')} {C.BOLD}Note {r.get('note_id','?')}{C.RESET} — {c}{C.BOLD}{q.upper()}{C.RESET} {C.DIM}(conf: {r.get('confidence','?')}){C.RESET}")
    pp = r.get("pain_points",[])
    if pp: print(f"     {C.DIM}Pain:{C.RESET} {pp[0][:65]}")
    print(f"     {C.GREEN}Action:{C.RESET} {r.get('recommended_action','?')[:65]}")
    print(f"     {C.RED}Don't build:{C.RESET} {r.get('what_not_to_build','?')[:65]}")

def print_eval_summary(evals, ver):
    scores = [e.get("overall_score",0) for e in evals]
    avg = sum(scores)/len(scores) if scores else 0
    passed = sum(1 for e in evals if e.get("pass",False))
    pct = (passed/len(evals))*100 if evals else 0
    pc = C.GREEN if pct>=70 else C.YELLOW if pct>=40 else C.RED
    print(f"\n  {C.BOLD}📊 {ver}{C.RESET}")
    print(f"     Score: {C.BOLD}{avg:.1f}/5{C.RESET} | Pass Rate: {pc}{C.BOLD}{passed}/{len(evals)} ({pct:.0f}%){C.RESET}")
    dims = ['accuracy','completeness','actionability','honesty','what_not_to_build']
    for d in dims:
        vals = [e['scores'][d]['score'] for e in evals if 'scores' in e and d in e.get('scores',{}) and isinstance(e['scores'].get(d),dict)]
        if vals:
            a = sum(vals)/len(vals)
            bc = C.GREEN if a>=4 else C.YELLOW if a>=3 else C.RED
            bar = f"{bc}{'█'*int(a)}{'░'*(5-int(a))}{C.RESET}"
            print(f"       {C.DIM}{d:<22}{C.RESET} {bar} {a:.1f}")

def print_comparison(e1, e2):
    s1=[e.get("overall_score",0) for e in e1]; s2=[e.get("overall_score",0) for e in e2]
    a1,a2=sum(s1)/len(s1),sum(s2)/len(s2); p1=sum(1 for e in e1 if e.get("pass",False)); p2=sum(1 for e in e2 if e.get("pass",False))
    d=a2-a1; dc=C.GREEN if d>0 else C.RED if d<0 else C.DIM
    print(f"\n  {C.BOLD}{'Metric':<25} {'V1':<12} {'V2':<12} {'Delta':<10}{C.RESET}")
    print(f"  {C.DIM}{'─'*55}{C.RESET}")
    print(f"  {'Average Score':<25} {a1:<12.1f} {a2:<12.1f} {dc}{'+' if d>=0 else ''}{d:.1f}{C.RESET}")
    print(f"  {'Pass Rate':<25} {p1}/{len(e1):<10} {p2}/{len(e2):<10} {dc}{'+' if p2>=p1 else ''}{p2-p1}{C.RESET}")
    dims=['accuracy','completeness','actionability','honesty','what_not_to_build']
    for dim in dims:
        v1=[e['scores'][dim]['score'] for e in e1 if 'scores' in e and dim in e.get('scores',{}) and isinstance(e['scores'].get(dim),dict)]
        v2=[e['scores'][dim]['score'] for e in e2 if 'scores' in e and dim in e.get('scores',{}) and isinstance(e['scores'].get(dim),dict)]
        if v1 and v2:
            aa,bb=sum(v1)/len(v1),sum(v2)/len(v2);dd=bb-aa;ddc=C.GREEN if dd>0 else C.RED if dd<0 else C.DIM
            print(f"  {dim:<25} {aa:<12.1f} {bb:<12.1f} {ddc}{'+' if dd>=0 else ''}{dd:.1f}{C.RESET}")


def build_html_results(report, results, version):
    cards = ""
    for r in results:
        if "error" in r:
            cards += f'<div class="card"><div class="card-h"><span class="note-id">{r.get("note_id","?")}</span><span class="badge b-fail">ERROR</span></div></div>'
            continue
        q = r.get("lead_quality","?")
        bc = {"hot":"b-hot","warm":"b-warm","cold":"b-cold","disqualify":"b-dis"}.get(q,"")
        em = {"hot":"🔥","warm":"🟡","cold":"🔵","disqualify":"⛔"}.get(q,"❓")
        pp = "".join(f"<li>{p}</li>" for p in r.get("pain_points",[]))
        strong = "".join(f"<li>{s}</li>" for s in r.get("pmf_signals",{}).get("strong",[]))
        weak = "".join(f"<li>{s}</li>" for s in r.get("pmf_signals",{}).get("weak",[]))
        cards += f'''<div class="card">
<div class="card-h" onclick="toggle(this)"><span class="note-id">{r.get("note_id","?")}</span>
<span class="badge {bc}">{em} {q.upper()}</span><span class="conf">conf: {r.get("confidence","?")}</span></div>
<div class="card-b"><div class="field"><label>Pain Points</label><ul>{pp}</ul></div>
<div class="field"><label>Strong Signals</label><ul class="green">{strong or "<li>None</li>"}</ul></div>
<div class="field"><label>Red Flags</label><ul class="red">{weak or "<li>None</li>"}</ul></div>
<div class="field"><label>✅ Action</label><p class="green">{r.get("recommended_action","?")}</p></div>
<div class="field"><label>🚫 Don't Build</label><p class="red">{r.get("what_not_to_build","?")}</p></div>
<div class="field"><label>💬 Key Quote</label><p class="purple">"{r.get("key_quote","?")}"</p></div></div></div>'''
    report.add(f'<h2>{version} — Lead Analysis</h2>{cards}')


def build_html_eval(report, evals, version):
    scores = [e.get("overall_score",0) for e in evals]
    avg = sum(scores)/len(scores) if scores else 0
    passed = sum(1 for e in evals if e.get("pass",False))
    pct = (passed/len(evals))*100 if evals else 0
    pc = "#4ade80" if pct>=70 else "#eab308" if pct>=40 else "#f87171"
    dims = ['accuracy','completeness','actionability','honesty','what_not_to_build']
    bars = ""
    for d in dims:
        vals = [e['scores'][d]['score'] for e in evals if 'scores' in e and d in e.get('scores',{}) and isinstance(e['scores'].get(d),dict)]
        if vals:
            a = sum(vals)/len(vals); w=int((a/5)*100); c="#4ade80" if a>=4 else "#eab308" if a>=3 else "#f87171"
            bars += f'<div class="bar-row"><span class="bar-name">{d.replace("_"," ").title()}</span><div class="bar-bg"><div class="bar-fill" style="width:{w}%;background:{c}"></div></div><span class="bar-score">{a:.1f}</span></div>'
    report.add(f'''<h2>{version} — Evaluation</h2>
<div class="stats"><div class="stat"><div class="stat-val">{avg:.1f}<span>/5</span></div><div class="stat-lbl">Avg Score</div></div>
<div class="stat"><div class="stat-val">{passed}/{len(evals)}</div><div class="stat-lbl">Passed</div></div>
<div class="stat"><div class="stat-val" style="color:{pc}">{pct:.0f}%</div><div class="stat-lbl">Pass Rate</div></div></div>
<div style="margin:1rem 0">{bars}</div>''')


def build_html_comparison(report, e1, e2):
    s1=[e.get("overall_score",0) for e in e1]; s2=[e.get("overall_score",0) for e in e2]
    a1,a2=sum(s1)/len(s1),sum(s2)/len(s2); p1=sum(1 for e in e1 if e.get("pass",False)); p2=sum(1 for e in e2 if e.get("pass",False))
    d=a2-a1; dc="pos" if d>0 else "neg" if d<0 else ""
    rows = f'<tr><td>Average Score</td><td>{a1:.1f}</td><td>{a2:.1f}</td><td class="{dc}">{"+{:.1f}".format(d) if d>=0 else "{:.1f}".format(d)}</td></tr>'
    rows += f'<tr><td>Pass Rate</td><td>{p1}/{len(e1)}</td><td>{p2}/{len(e2)}</td><td class="{dc}">{"+{}".format(p2-p1) if p2>=p1 else p2-p1}</td></tr>'
    dims=['accuracy','completeness','actionability','honesty','what_not_to_build']
    for dim in dims:
        v1=[e['scores'][dim]['score'] for e in e1 if 'scores' in e and dim in e.get('scores',{}) and isinstance(e['scores'].get(dim),dict)]
        v2=[e['scores'][dim]['score'] for e in e2 if 'scores' in e and dim in e.get('scores',{}) and isinstance(e['scores'].get(dim),dict)]
        if v1 and v2:
            aa,bb=sum(v1)/len(v1),sum(v2)/len(v2);dd=bb-aa;ddc="pos" if dd>0 else "neg" if dd<0 else ""
            rows+=f'<tr><td>{dim.replace("_"," ").title()}</td><td>{aa:.1f}</td><td>{bb:.1f}</td><td class="{ddc}">{"+{:.1f}".format(dd) if dd>=0 else "{:.1f}".format(dd)}</td></tr>'
    report.add(f'<h2>📊 Before vs After</h2><table><thead><tr><th>Metric</th><th>V1</th><th>V2</th><th>Delta</th></tr></thead><tbody>{rows}</tbody></table>')


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    report = HTMLReport()

    ph("🧠 Build an AI Agent That Learns From Its Mistakes")
    print(f"  {C.DIM}Model: {MODEL} | Cost: ~$0.50 | Time: ~3 min{C.RESET}")
    report.add(f'<div class="hero"><h1>🧠 Agent That Learns — Results</h1><p>Model: {MODEL} | {datetime.now().strftime("%Y-%m-%d %H:%M")}</p></div>')

    df = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_customer_notes.json")
    if not os.path.exists(df): print(f"\n  {C.RED}❌ {df} not found{C.RESET}"); return
    notes = json.loads(open(df).read())
    print(f"\n  {C.GREEN}📋{C.RESET} Loaded {C.BOLD}{len(notes)}{C.RESET} customer notes")

    # ── ROUND 1 ──
    ps("ROUND 1 — Agent V1")
    print(f"  {C.DIM}Analyzing customer notes...{C.RESET}")
    v1r = run_agent(notes, AGENT_SYSTEM_PROMPT_V1)
    for i,r in enumerate(v1r,1): print_result(r,i)
    build_html_results(report, v1r, "Round 1 — Agent V1")

    ps("ROUND 1 — Eval (Claude-as-Judge)")
    print(f"  {C.DIM}Grading outputs against strict rubric...{C.RESET}")
    v1e = evaluate_outputs(notes, v1r)
    print_eval_summary(v1e, "Agent V1")
    build_html_eval(report, v1e, "Round 1")

    # Show failures
    failures = [e for e in v1e if not e.get("pass",False)]
    if failures:
        print(f"\n  {C.RED}Failed notes:{C.RESET}")
        for f in failures:
            print(f"     {C.RED}✗{C.RESET} {f.get('note_id','?')}: {f.get('failure_mode','?')} {C.DIM}(score: {f.get('overall_score',0)}){C.RESET}")

    # ── DIAGNOSE ──
    ps("DIAGNOSING — Failure Patterns")
    fa = analyze_failures(v1e)
    pr = fa.get('pass_rate','?'); pc = C.GREEN if '100' in str(pr) or '90' in str(pr) or '80' in str(pr) else C.YELLOW if '60' in str(pr) or '50' in str(pr) else C.RED
    print(f"\n  Pass Rate: {pc}{C.BOLD}{pr}{C.RESET}")
    if fa.get("failure_patterns"):
        print(f"\n  {C.RED}🔍 Recurring failures:{C.RESET}")
        for m,c in fa["failure_patterns"]: print(f"     {C.RED}→{C.RESET} {m} {C.DIM}(×{c}){C.RESET}")
    if fa.get("weakest_dimensions"):
        print(f"\n  {C.YELLOW}📉 Weakest dimensions:{C.RESET}")
        for d,c in fa["weakest_dimensions"]: print(f"     {C.YELLOW}→{C.RESET} {d} {C.DIM}(scored ≤3 on {c} notes){C.RESET}")

    # Add failures to HTML
    fp = "".join(f'<div class="failure-item"><span class="failure-mode">{m}</span><span class="failure-count">×{c}</span></div>' for m,c in fa.get("failure_patterns",[]))
    wd = "".join(f'<div class="failure-item"><span class="failure-mode">{d}</span><span class="failure-count">≤3 on {c} notes</span></div>' for d,c in fa.get("weakest_dimensions",[]))
    report.add(f'<h2>Failure Analysis</h2><div class="card" style="border:none"><div class="card-b open"><div class="field"><label>Recurring Failures</label>{fp or "<p>None</p>"}</div><div class="field"><label>Weakest Dimensions</label>{wd or "<p>None</p>"}</div></div></div>')

    if fa.get("status")=="all_passed":
        print(f"\n  {C.GREEN}🎉 All passed!{C.RESET}"); report.save("report.html"); return

    # ── IMPROVE ──
    ps("IMPROVING — Generating V2 Prompt")
    print(f"  {C.DIM}Analyzing failures and rewriting prompt...{C.RESET}")
    v2p = generate_improved_prompt(AGENT_SYSTEM_PROMPT_V1, fa, v1e)
    print(f"  {C.GREEN}✅{C.RESET} V2 prompt generated {C.DIM}({len(v2p)} chars){C.RESET}")

    ps("GENERATING — Edge Case Tests")
    print(f"  {C.DIM}Creating regression tests...{C.RESET}")
    ec = generate_new_eval_cases(fa)
    if ec:
        for c in ec: print(f"  {C.CYAN}→{C.RESET} {c.get('id','?')}: targets '{C.YELLOW}{c.get('tests_failure_mode','?')}{C.RESET}'")

    # ── ROUND 2 ──
    ps("ROUND 2 — Agent V2 (Improved)")
    print(f"  {C.DIM}Rerunning with improved prompt...{C.RESET}")
    v2r = run_agent(notes, v2p)
    for i,r in enumerate(v2r,1): print_result(r,i)
    build_html_results(report, v2r, "Round 2 — Agent V2 (Improved)")

    ps("ROUND 2 — Eval")
    print(f"  {C.DIM}Grading V2 outputs...{C.RESET}")
    v2e = evaluate_outputs(notes, v2r)
    print_eval_summary(v2e, "Agent V2")
    build_html_eval(report, v2e, "Round 2")

    # ── COMPARE ──
    ph("📊 BEFORE vs AFTER")
    print_comparison(v1e, v2e)
    build_html_comparison(report, v1e, v2e)

    # ── EDGE CASES ──
    if ec:
        ps("BONUS — V2 on Edge Cases")
        en=[{"id":c["id"],"source":c.get("source","gen"),"date":c.get("date","2026-05-05"),"raw_text":c["raw_text"]} for c in ec]
        er=run_agent(en,v2p); ee=evaluate_outputs(en,er)
        print_eval_summary(ee,"V2 Edge Cases")
        for c,r,ev in zip(ec,er,ee):
            exp=c.get("expected_lead_quality","?"); act=r.get("lead_quality","?") if "error" not in r else "error"
            icon=f"{C.GREEN}✅{C.RESET}" if exp.lower()==act.lower() else f"{C.RED}❌{C.RESET}"
            print(f"  {icon} {c['id']}: expected={exp}, got={act}")

    # ── SAVE ──
    elapsed=time.time()-t0
    with open("agent_results.json","w") as f:
        json.dump({"v1_prompt":AGENT_SYSTEM_PROMPT_V1,"v2_prompt":v2p,"v1_results":v1r,"v1_evals":v1e,
                    "v2_results":v2r,"v2_evals":v2e,"failure_analysis":fa,"new_eval_cases":ec,
                    "delta":{"v1_avg":sum(e.get("overall_score",0) for e in v1e)/len(v1e),
                             "v2_avg":sum(e.get("overall_score",0) for e in v2e)/len(v2e)},
                    "runtime":elapsed,"model":MODEL,"timestamp":datetime.now().isoformat()},f,indent=2)

    report_file = report.save("report.html")

    ph("🎯 COMPLETE")
    print(f"""
  {C.GREEN}✅{C.RESET} Done in {C.BOLD}{elapsed:.0f}s{C.RESET}

  {C.BOLD}What happened:{C.RESET}
  {C.DIM}1.{C.RESET} Agent analyzed {len(notes)} messy customer notes
  {C.DIM}2.{C.RESET} Claude graded every output (5 dimensions)
  {C.DIM}3.{C.RESET} Found {C.YELLOW}{len(fa.get('failure_patterns',[]))}{C.RESET} failure patterns
  {C.DIM}4.{C.RESET} Generated improved prompt
  {C.DIM}5.{C.RESET} Created {C.CYAN}{len(ec)}{C.RESET} regression tests
  {C.DIM}6.{C.RESET} Reran and measured improvement

  {C.BOLD}Files:{C.RESET}
  {C.GREEN}→{C.RESET} {C.UNDERLINE}report.html{C.RESET}         Open in browser
  {C.GREEN}→{C.RESET} agent_results.json   Raw data

  {C.BOLD}Adapt:{C.RESET}
  {C.DIM}1. Replace sample_customer_notes.json → your data
  2. Modify AGENT_SYSTEM_PROMPT_V1 → your use case
  3. Adjust EVAL_RUBRIC → your quality bar
  4. Run until pass rate hits your target{C.RESET}

  {C.DIM}Cost: ~$0.50 | Built with Claude → platform.claude.com/docs{C.RESET}
    """)


if __name__ == "__main__":
    main()
