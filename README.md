# 🧠 Build an AI Agent That Learns From Its Mistakes

**Most AI agents work once. This one gets better every time it runs.**

A self-improving customer discovery agent built with Claude's API. Run it, grade it, find failure patterns, improve the prompt, rerun, measure the difference. In 3 minutes.

---

## The Problem

Every YC startup builds an AI agent in week 1. It works great in the demo. Then you ship it to real users and notice: it keeps making the same mistakes. It over-classifies leads as "hot." It misses obvious red flags. It gives generic advice instead of specific next steps.

You tweak the prompt. It fixes one problem, breaks another. You have no systematic way to know if your agent is getting better or worse.

**This repo solves that.**

---

## What This Does

A complete feedback loop that turns a mediocre agent into a reliable one:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   1. RUN        → Agent analyzes messy customer notes   │
│   2. GRADE      → Claude evaluates every output         │
│   3. DIAGNOSE   → System finds recurring failures       │
│   4. IMPROVE    → Claude rewrites the prompt            │
│   5. TEST       → New eval cases target weak spots      │
│   6. RERUN      → Measure the improvement               │
│                                                         │
│   Repeat until your agent consistently passes.          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

The example uses **customer discovery** — the agent reads messy interview notes, Slack messages, and founder DMs, then extracts:

- Lead quality (hot / warm / cold / disqualify)
- Pain points and PMF signals
- Budget indicators and decision timelines
- Specific recommended actions
- What NOT to build (feature requests that would distract you)

But the pattern works for **any agent** you're building.

---

## Quick Start

```bash
git clone https://github.com/pritika-anthropic/agent-that-learns.git
cd agent-that-learns
pip install anthropic
export ANTHROPIC_API_KEY="your-key-here"
python agent_that_learns.py
```

Get your API key at [console.anthropic.com](https://console.anthropic.com). Takes about 3 minutes to run. Costs ~$0.50.

---

## What You'll See

```
════════════════════════════════════════════════════════════
  🧠 Build an AI Agent That Learns From Its Mistakes
════════════════════════════════════════════════════════════

  📋 Loaded 10 customer notes

  ROUND 1: Running Agent V1
  ✅ Agent analyzed 10 notes

  ROUND 1: Evaluating Agent V1 Outputs
  📊 V1 Results:
     Average Score: 3.2/5
     Pass Rate: 4/10 (40%)

  ROUND 1: Analyzing Failure Patterns
  🔍 Recurring Failure Modes:
     → over_optimistic_lead_scoring (3x)
     → generic_action_items (2x)
     → missed_budget_signals (1x)

  IMPROVING: Generating V2 Prompt
  ✅ Generated improved prompt targeting failure modes

  ROUND 2: Running Agent V2 (Improved)
  📊 V2 Results:
     Average Score: 4.1/5
     Pass Rate: 8/10 (80%)

  📊 BEFORE vs AFTER COMPARISON
  Metric                    V1 (Before)     V2 (After)      Change
  ─────────────────────────────────────────────────────────────────
  Average Score             3.2             4.1             +0.9
  Pass Rate                 4/10            8/10            +4
  accuracy                  3.4             4.3             +0.9
  actionability             2.8             4.0             +1.2
  honesty                   3.5             4.2             +0.7
```

Your agent went from 40% pass rate to 80% — automatically. No manual prompt tweaking. No guesswork.

---

## The Three Components

### 1. The Agent (`run_agent`)

A customer discovery analyst that reads messy notes and outputs structured JSON. The prompt defines:
- What to extract (pain points, PMF signals, budget indicators)
- How to classify (hot/warm/cold/disqualify)
- What to flag (distracting feature requests)
- How to be honest (avoid over-optimism)

### 2. The Eval System (`evaluate_outputs`)

Claude-as-Judge. A separate Claude call grades every agent output on 5 dimensions:
- **Accuracy** — did it get the assessment right?
- **Completeness** — did it catch everything?
- **Actionability** — can a founder act on this today?
- **Honesty** — did it avoid sugar-coating?
- **What-not-to-build** — did it flag distractions?

Each dimension is scored 1-5. Overall 4+ = pass.

### 3. The Feedback Loop (`analyze_failures` → `generate_improved_prompt`)

The system:
1. Collects all failed evaluations
2. Groups them by failure mode (e.g., "over_optimistic_lead_scoring")
3. Feeds the failure patterns + original prompt to Claude
4. Claude generates a surgically improved prompt
5. Generates new test cases that target the specific failures
6. Reruns and measures the delta

---

## Why Claude?

This workflow specifically showcases where Claude is strongest:

**Structured output reliability** — Every step returns JSON. Claude follows the schema consistently. The entire pipeline depends on predictable output formatting — if one step returns malformed JSON, the whole loop breaks. Claude doesn't break it.

**Long-context reasoning** — The eval step processes the original note + the agent's full analysis. The prompt improvement step processes the original prompt + all failure data + all eval results. This requires genuine reasoning across long, complex context.

**Self-evaluation quality** — The Claude-as-Judge pattern only works if the judge is good. Claude's evaluations are nuanced — it catches subtle issues like "over-optimistic about a lead that showed classic enterprise stall signals" rather than generic "the analysis was incomplete."

**Instruction following under complexity** — The improved prompt generation step requires Claude to understand the original prompt, the failure patterns, and generate a surgical improvement without breaking what already works. This is hard. Claude handles it.

---

## Adapt This For Your Startup

The customer discovery example is just the demo. Here's how to use this pattern for your actual product:

### Support Agent
- Replace sample notes with support tickets
- Change the eval rubric to grade: resolution accuracy, tone, escalation decisions
- Run the loop until your agent handles edge cases correctly

### Sales Research Agent
- Replace notes with prospect data
- Grade on: research accuracy, personalization quality, relevance of talking points
- Target failure mode: generic outreach that doesn't reference specific prospect details

### Code Review Agent
- Replace notes with pull requests
- Grade on: bug detection accuracy, false positive rate, actionability of suggestions
- Target failure mode: flagging style issues while missing logic bugs

### Compliance Agent
- Replace notes with documents to review
- Grade on: extraction accuracy, risk identification, false negatives
- Target failure mode: missing critical clauses or misinterpreting regulatory language

**The pattern is always the same:**
1. Define what "good" looks like (eval rubric)
2. Run your agent
3. Grade the outputs
4. Find what's broken
5. Fix the prompt
6. Prove it's better

---

## Project Structure

```
agent-that-learns/
├── agent_that_learns.py      # Main script — agent + eval + feedback loop
├── sample_customer_notes.json # 10 realistic messy customer notes
├── README.md                  # This file
└── agent_results.json         # Generated after running — full results
```

---

## Cost & Performance

- **API cost per run:** ~$0.50 (10 notes × 2 rounds × eval)
- **Runtime:** ~3 minutes
- **Model:** Claude Sonnet 4.6 (best balance of speed, cost, and quality)
- **Typical improvement:** 20-40% pass rate increase from V1 → V2

---

## About

Built by [Pritika Mehta](https://www.linkedin.com/in/pritikam/) — YC S20 alum, founder of Butternut AI & SockSoho. Now on Anthropic's Applied AI team for startups.

I've watched hundreds of startups build AI agents. The ones that succeed don't have better models — they have better feedback loops. This repo is the pattern I wish every founder would start with.

**Start building on Claude →** [platform.claude.com/docs](https://platform.claude.com/docs)
