# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thế Giáp
- **Student ID**: 2A202600912
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

- **Modules Implemented/Updated**:
  - `src/agent/agent.py`: completed ReAct loop, action/final parsing, tool execution, telemetry integration, and module runner.
  - `src/tools/rental_tools.py`: implemented rental dataset tools and enforced sequence dependency (`find_flat` -> `find_max_price`).
  - `tests/test_rental_use_case.py`: added required tests for tool order and 5 required destination cases.
  - `README.md`: documented use case, required cases, and flowchart.

- **Code Highlights**:
  - Dynamic tool execution by name map and parsed arguments in `ReActAgent`.
  - Strict business rule in `find_max_price`: `price_million < price`, sorted ascending.
  - Deterministic scripted LLM test for reliable validation of ReAct loop behavior.
  - Added graceful provider-error handling in both agent and baseline chatbot runtime loops.

- **How it interacts with ReAct loop**:
  1. Agent receives user task.
  2. Agent requests tool action from LLM.
  3. Tool result is injected as Observation.
  4. Next action uses Observation context.
  5. Agent emits Final Answer.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Tests failed at collection stage due to `IndentationError` in `src/agent/agent.py`.
- **Log/Error Source**: Pytest import error during `tests/test_rental_use_case.py` collection.
- **Diagnosis**: Mis-indented line inside `get_system_prompt` blocked module import, so no tests could execute.
- **Solution**: Fixed indentation and reran tests; suite passed after correction.

Additional requirement bug fixed:
- Old `find_max_price` returned `<= price` and unsorted output.
- Updated to strict `< price` and ascending sort; synchronized test expectations and README outputs.

Runtime reliability fix:
- Real execution hit `google.genai.errors.ServerError: 503 UNAVAILABLE`.
- Added try/except so runtime returns retry-friendly message instead of terminating process.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:
   - `Thought/Action` structure makes decision steps explicit and auditable.
   - Baseline chatbot can answer fluently but does not guarantee deterministic step order.

2. **Reliability**:
   - Agent can perform worse if parsing breaks or tool signatures are ambiguous.
   - With strict prompt format and test coverage, reliability improves significantly.

3. **Observation feedback**:
   - Observation is critical for chaining constraints (distance first, then budget).
   - Without Observation, final answer often misses one of the constraints.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Replace static rental list with persistent storage (SQL/API) and pagination.
- **Safety**: Add schema validation for tool arguments and fallback when no match is found.
- **Performance**: Add provider fallback and caching for repeated destination queries.

---

> Submission prepared for a solo team setup (group size = 1).
