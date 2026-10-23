# Write-up: Support Ticket Triage Agent

## 1. Architecture decisions

- **Agent loop, not a fixed pipeline.** Not every ticket needs every tool, and if/else routing can't cover every case, so the model picks its tools. To keep it bounded, the loop is capped at 5 rounds and the final answer is forced into a `TriageResult` schema (structured output).
- **Mocked tools behind real interfaces.** KB search, customer profile, and system status read JSON in `data/`, but their schemas match real services. In production only the implementation changes (vector DB, CRM, status API); prompt and loop stay the same.
- **Keyword KB search.** 3 articles come from the brief, plus 5 synthetic ones to test tickets beyond the samples. At 8 articles, keyword scoring (English + Thai) is enough and easy to debug.
- **FastAPI + plain OpenAI SDK.** An API is closer to real integration than a CLI; no agent framework, so the whole loop is visible with no hidden logic.

## 2. What could go wrong

- **Urgency underestimated (most dangerous):** a critical ticket gets auto-responded and no human sees it. *Fix:* a rule layer that can only raise urgency, never lower it, plus a second check before any auto-respond.
- **Wrong information in auto-responses:** from bad retrieval or the model adding facts. *Fix:* auto-respond only on a confident KB match and require cited article ids.
- **Prompt injection:** customer text tries to override instructions. *Fix:* treat customer text as delimited data; tools are read-only; the rule layer ignores manipulated urgency.
- **LLM outage or timeout:** *Fix:* retry with backoff, fall back to another provider (`OPENAI_BASE_URL`), and route to a human queue if all fail.

These safeguards are next steps; the current code keeps the core agent simple.

## 3. Evaluating in production

- **Before launch:** a labeled eval set from real tickets; measure urgency and action accuracy, with critical-ticket recall as the key metric.
- **Rollout:** shadow mode first (agent suggests, human decides); enable auto-respond for low-urgency tickets only once agreement passes a threshold.
- **After launch:** track human override rate, CSAT and reopen rate, latency, cost, and KB no-match rate; add every failure to the eval set.
