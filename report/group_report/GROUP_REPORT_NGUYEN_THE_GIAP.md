# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Solo Builders
- **Team Members**: Nguyễn Thế Giáp (1 member)
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

This project implements and compares a baseline chatbot versus a ReAct agent for a rental search use case:

"Find rentals within `distance` km from `destination`, with monthly price lower than `price` and sorted from low to high."

- **Success Rate**: 100% on required suite (`4/4` tests passed in `tests/test_rental_use_case.py`).
- **Key Outcome**: ReAct agent reliably enforces tool order (`find_flat` then `find_max_price`) and handles multi-step filtering/sorting logic more deterministically than free-form chatbot reasoning.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
The agent in `src/agent/agent.py` follows:
1. Generate Thought/Action from model.
2. Parse `Action: tool(args)`.
3. Execute tool and append `Observation`.
4. Repeat until `Final Answer` or `max_steps`.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `find_flat` | `(destination: str, distance: float)` | Find all rentals with `distance_km <= distance`. |
| `find_max_price` | `(price: float)` | Filter from previous `find_flat` results by `price_million < price`, then sort ascending by `price_million`. |

### 2.3 LLM Providers Used
- **Primary for testing**: scripted provider in tests (deterministic behavior).
- **Runtime providers**: `gemini-2.5-flash` and `openai/gpt-oss-120b:free` via provider abstraction.

---

## 3. Telemetry & Performance Dashboard

Collected from `logs/2026-06-01.log` and latest test run:

- **Average Latency (scripted test run)**: ~1ms/request (`LLM_METRIC.latency_ms = 1`).
- **Observed cloud latency (Gemini samples)**: ~1996ms and ~3375ms for first agent step (real run).
- **Tokens (scripted test run)**: 2 tokens/request (mock usage in tests).
- **Step count per solved trace**: 3 steps (`find_flat` -> `find_max_price` -> `Final Answer`).
- **Test validation**: `pytest -q tests/test_rental_use_case.py` => `4 passed`.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study A: Import Failure due to Indentation
- **Input**: Running test collection.
- **Observation**: `IndentationError` in `src/agent/agent.py` prevented test import.
- **Root Cause**: Mis-indented `tool_descriptions` line in `get_system_prompt`.
- **Fix**: Correct indentation and rerun test suite.

### Case Study B: Business Rule Mismatch in `find_max_price`
- **Input**: Requirement clarification for rental need.
- **Observation**: Old logic used `<= price` and did not guarantee ascending order.
- **Root Cause**: Initial interpretation of "max price" lacked strict boundary and ranking behavior.
- **Fix**: Changed to strict `< price` and sorted ascending by `price_million`; updated tests and expected outputs.

### Case Study C: Runtime Provider Failure (Google 503)
- **Input**: Real run with `python -m src.agent.agent` and provider `google`.
- **Observation**: `google.genai.errors.ServerError: 503 UNAVAILABLE` after first step in one run; baseline chatbot also hit the same provider error in interactive run.
- **Root Cause**: External API high-demand transient outage, not tool-chain logic error.
- **Fix**: Added runtime exception handling in both agent and baseline chatbot so the process does not crash and returns a retry-friendly message.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Rule change (`<=` -> `<`) + sorting
- **Diff**: `find_max_price` now returns only prices strictly lower than budget and sorted ascending.
- **Result**: Output aligns with realistic rental prioritization needs; test expectations updated and passed.

### Experiment 2: Chatbot vs Agent (same use case)
| Case | Chatbot Baseline (no tools) | ReAct Agent (tool chain) | Winner |
| :--- | :--- | :--- | :--- |
| 1. VinUni, 3km, 3tr | Returned generic areas, not dataset-specific rental names | `Ecohome Dang Xa`, `Vinhomes Ocean Park Studio` | **Agent** |
| 2. HUST, 5km, 2tr | Runtime failed due provider 503 on second query | `Bach Khoa Dorm`, `Minh Khai Apartment` | **Agent** |
| 3. HAUI, 8km, 1.5tr | Not completed in same baseline session because provider outage interrupted flow | `Dien Student House`, `Nhon Co-living` | **Agent** |
| 4. PTIT, 4km, 3tr | Not completed in same baseline session because provider outage interrupted flow | `Trieu Khuc Room` | **Agent** |
| 5. UET, 5km, 2.5tr | Not completed in same baseline session because provider outage interrupted flow | `Mai Dich Room`, `Xuan Thuy Studio` | **Agent** |

The agent outputs above are verified in deterministic test suite (`tests/test_rental_use_case.py`) with strict conditions: must call `find_flat` first, then `find_max_price`, enforce `price_million < price`, and return sorted ascending.

---

## 6. Production Readiness Review

- **Security**: Validate/normalize tool inputs (destination string, numeric distance/price).
- **Guardrails**: `max_steps` limit is in place to avoid infinite loops and excess cost.
- **Observability**: JSON logs include `AGENT_START`, `AGENT_STEP`, `TOOL_EXECUTED`, `LLM_METRIC`, `AGENT_END`.
- **Scalability**: Move rental dataset to DB/API and add retry/fallback strategy across providers.

---

> This report is for a 1-person team submission and reflects implemented code + verified results in this repository.
