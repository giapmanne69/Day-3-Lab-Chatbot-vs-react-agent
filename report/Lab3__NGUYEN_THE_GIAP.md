# Lab3__NGUYEN_THE_GIAP

## Submission Metadata
- Student Name: Nguyễn Thế Giáp
- Student ID: 2A202600912
- Team Size: 1
- Date: 2026-06-01
- Public Repository Link: https://github.com/giapmanne69/Day-3-Lab-Chatbot-vs-react-agent
- Personal Commit Evidence: [Add at least 1 commit hash by Nguyễn Thế Giáp]

---

## Part A - Group Report

### Team Information
- Team Name: Solo Builders
- Team Members: Nguyễn Thế Giáp (1 member)
- Deployment Date: 2026-06-01

### 1. Executive Summary
This project implements and compares a baseline chatbot versus a ReAct agent for a rental search use case:

Find rentals within `distance` km from `destination`, with monthly price lower than `price` and sorted from low to high.

- Success Rate: 100% on required suite (`4/4` tests passed in `tests/test_rental_use_case.py`).
- Key Outcome: ReAct agent reliably enforces tool order (`find_flat` then `find_max_price`) and handles multi-step filtering/sorting logic more deterministically than free-form chatbot reasoning.

### 2. System Architecture & Tooling
#### 2.1 ReAct Loop Implementation
The agent in `src/agent/agent.py` follows:
1. Generate Thought/Action from model.
2. Parse `Action: tool(args)`.
3. Execute tool and append `Observation`.
4. Repeat until `Final Answer` or `max_steps`.

#### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `find_flat` | `(destination: str, distance: float)` | Find all rentals with `distance_km <= distance`. |
| `find_max_price` | `(price: float)` | Filter from previous `find_flat` results by `price_million < price`, then sort ascending by `price_million`. |

#### 2.3 LLM Providers Used
- Primary for testing: scripted provider in tests (deterministic behavior).
- Runtime providers: `gemini-2.5-flash` and `openai/gpt-oss-120b:free` via provider abstraction.

### 3. Telemetry & Performance Dashboard
Collected from `logs/2026-06-01.log` and latest test run:

- Average Latency (scripted test run): ~1ms/request (`LLM_METRIC.latency_ms = 1`).
- Observed cloud latency (Gemini samples): ~1996ms and ~3375ms for first agent step (real run).
- Tokens (scripted test run): 2 tokens/request (mock usage in tests).
- Step count per solved trace: 3 steps (`find_flat` -> `find_max_price` -> `Final Answer`).
- Test validation: `pytest -q tests/test_rental_use_case.py` => `4 passed`.

### 4. Root Cause Analysis (RCA) - Failure Traces
#### Case Study A: Import Failure due to Indentation
- Input: Running test collection.
- Observation: `IndentationError` in `src/agent/agent.py` prevented test import.
- Root Cause: Mis-indented `tool_descriptions` line in `get_system_prompt`.
- Fix: Correct indentation and rerun test suite.

#### Case Study B: Business Rule Mismatch in `find_max_price`
- Input: Requirement clarification for rental need.
- Observation: Old logic used `<= price` and did not guarantee ascending order.
- Root Cause: Initial interpretation of "max price" lacked strict boundary and ranking behavior.
- Fix: Changed to strict `< price` and sorted ascending by `price_million`; updated tests and expected outputs.

#### Case Study C: Runtime Provider Failure (Google 503)
- Input: Real run with `python -m src.agent.agent` and provider `google`.
- Observation: `google.genai.errors.ServerError: 503 UNAVAILABLE` after first step in one run; baseline chatbot also hit the same provider error in interactive run.
- Root Cause: External API high-demand transient outage, not tool-chain logic error.
- Fix: Added runtime exception handling in both agent and baseline chatbot so the process does not crash and returns a retry-friendly message.

### 5. Ablation Studies & Experiments
#### Experiment 1: Rule change (`<=` -> `<`) + sorting
- Diff: `find_max_price` now returns only prices strictly lower than budget and sorted ascending.
- Result: Output aligns with realistic rental prioritization needs; test expectations updated and passed.

#### Experiment 2: Chatbot vs Agent (same use case)
| Case | Chatbot Baseline (no tools) | ReAct Agent (tool chain) | Winner |
| :--- | :--- | :--- | :--- |
| 1. VinUni, 3km, 3tr | Returned generic areas, not dataset-specific rental names | `Ecohome Dang Xa`, `Vinhomes Ocean Park Studio` | Agent |
| 2. HUST, 5km, 2tr | Runtime failed due provider 503 on second query | `Bach Khoa Dorm`, `Minh Khai Apartment` | Agent |
| 3. HAUI, 8km, 1.5tr | Not completed in same baseline session because provider outage interrupted flow | `Dien Student House`, `Nhon Co-living` | Agent |
| 4. PTIT, 4km, 3tr | Not completed in same baseline session because provider outage interrupted flow | `Trieu Khuc Room` | Agent |
| 5. UET, 5km, 2.5tr | Not completed in same baseline session because provider outage interrupted flow | `Mai Dich Room`, `Xuan Thuy Studio` | Agent |

### 6. Production Readiness Review
- Security: Validate/normalize tool inputs (destination string, numeric distance/price).
- Guardrails: `max_steps` limit is in place to avoid infinite loops and excess cost.
- Observability: JSON logs include `AGENT_START`, `AGENT_STEP`, `TOOL_EXECUTED`, `LLM_METRIC`, `AGENT_END`.
- Scalability: Move rental dataset to DB/API and add retry/fallback strategy across providers.

---

## Part B - Individual Report

### Student Information
- Student Name: Nguyễn Thế Giáp
- Student ID: 2A202600912
- Date: 2026-06-01

### I. Technical Contribution
- Modules Implemented/Updated:
  - `src/agent/agent.py`: completed ReAct loop, action/final parsing, tool execution, telemetry integration, and module runner.
  - `src/tools/rental_tools.py`: implemented rental dataset tools and enforced sequence dependency (`find_flat` -> `find_max_price`).
  - `tests/test_rental_use_case.py`: added required tests for tool order and 5 required destination cases.
  - `README.md`: documented use case, required cases, and flowchart.
- Code Highlights:
  - Dynamic tool execution by name map and parsed arguments in `ReActAgent`.
  - Strict business rule in `find_max_price`: `price_million < price`, sorted ascending.
  - Deterministic scripted LLM test for reliable validation of ReAct loop behavior.
  - Added graceful provider-error handling in both agent and baseline chatbot runtime loops.

### II. Debugging Case Study
- Problem Description: Tests failed at collection stage due to `IndentationError` in `src/agent/agent.py`.
- Log/Error Source: Pytest import error during `tests/test_rental_use_case.py` collection.
- Diagnosis: Mis-indented line inside `get_system_prompt` blocked module import, so no tests could execute.
- Solution: Fixed indentation and reran tests; suite passed after correction.

Additional requirement bug fixed:
- Old `find_max_price` returned `<= price` and unsorted output.
- Updated to strict `< price` and ascending sort; synchronized test expectations and README outputs.

Runtime reliability fix:
- Real execution hit `google.genai.errors.ServerError: 503 UNAVAILABLE`.
- Added try/except so runtime returns retry-friendly message instead of terminating process.

### III. Personal Insights: Chatbot vs ReAct
1. Reasoning:
- `Thought/Action` structure makes decision steps explicit and auditable.
- Baseline chatbot can answer fluently but does not guarantee deterministic step order.

2. Reliability:
- Agent can perform worse if parsing breaks or tool signatures are ambiguous.
- With strict prompt format and test coverage, reliability improves significantly.

3. Observation feedback:
- Observation is critical for chaining constraints (distance first, then budget).
- Without Observation, final answer often misses one of the constraints.

### IV. Future Improvements
- Scalability: Replace static rental list with persistent storage (SQL/API) and pagination.
- Safety: Add schema validation for tool arguments and fallback when no match is found.
- Performance: Add provider fallback and caching for repeated destination queries.

---

This single file combines both group and individual report sections, following requirement #4.
