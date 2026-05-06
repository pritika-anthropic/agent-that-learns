# 🧠 Build an AI Agent That Learns From Its Mistakes

A self-improving customer discovery agent built with Claude's API. Run it, grade it, find failure patterns, improve the prompt, rerun, measure the difference.

**[Read the full blog post →](https://foregoing-belief-b65.notion.site/Build-an-AI-Agent-That-Learns-From-its-Mistakes-3580895db35c80e2a194c0a2f3d4c0d2)**

---

## Quick Start

```bash
git clone https://github.com/pritika-anthropic/agent-that-learns.git
cd agent-that-learns
pip install anthropic
export ANTHROPIC_API_KEY="your-key-here"
python3 agent_that_learns.py
```

Then open `report.html` in your browser for the visual report.

Runs in ~3 minutes. Costs ~$0.50.

---

## What Happens When You Run It

```
ROUND 1 — Agent V1 (naive prompt)
→ Analyzes 10 messy customer notes
→ Scores 3.0/5, 50% pass rate
→ Fails on: over-optimistic scoring, missed red flags

DIAGNOSING
→ Finds recurring failure patterns
→ Identifies weakest dimensions (accuracy, honesty)

IMPROVING
→ Claude rewrites the prompt targeting each failure
→ Generates 3 regression test cases

ROUND 2 — Agent V2 (improved prompt)
→ Scores 4.9/5, 90% pass rate
→ +1.9 average score improvement in one cycle
```

---

## How It Works

| Step | What happens | Claude feature used |
|---|---|---|
| **Run** | Agent analyzes messy customer notes | Structured output, instruction following |
| **Grade** | Claude-as-Judge scores every output (5 dimensions) | Reasoning depth, eval quality |
| **Diagnose** | Aggregate failures into patterns | Pattern recognition |
| **Improve** | Claude rewrites the prompt targeting failures | 1M context window, long-context reasoning |
| **Test** | Generate edge cases targeting weak spots | Test case generation |
| **Rerun** | Measure the improvement | Consistency, structured output |

---

## Adapt For Your Startup

This uses customer discovery as the example. The pattern works for any agent:

1. Replace `sample_customer_notes.json` with your data
2. Modify `AGENT_SYSTEM_PROMPT_V1` for your use case
3. Adjust `EVAL_RUBRIC` for your quality bar
4. Run until pass rate hits your target

---

## Files

| File | What it is |
|---|---|
| `agent_that_learns.py` | Main script. Agent + eval + feedback loop |
| `sample_customer_notes.json` | 10 realistic messy customer notes |
| `report.html` | Generated after running. Visual report |
| `agent_results.json` | Generated after running. Raw data |

---

Built by [Pritika Mehta](https://www.linkedin.com/in/pritikam/) | YC S20 | Applied AI @ Anthropic

Built with Claude → [platform.claude.com/docs](https://platform.claude.com/docs)
