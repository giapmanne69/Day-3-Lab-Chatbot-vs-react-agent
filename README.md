# Lab 3: Chatbot vs ReAct Agent (Industry Edition)

Welcome to Phase 3 of the Agentic AI course! This lab focuses on moving from a simple LLM Chatbot to a sophisticated **ReAct Agent** with industry-standard monitoring.

## 🚀 Getting Started

### 1. Setup Environment
Copy the `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Directory Structure
- `src/tools/`: Extension point for your custom tools.

## 🏠 Running with Local Models (CPU)

If you don't want to use OpenAI or Gemini, you can run open-source models (like Phi-3) directly on your CPU using `llama-cpp-python`.

### 1. Download the Model
Download the **Phi-3-mini-4k-instruct-q4.gguf** (approx 2.2GB) from Hugging Face:
- [Phi-3-mini-4k-instruct-GGUF](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)
- Direct Download: [phi-3-mini-4k-instruct-q4.gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf)

### 2. Place Model in Project
Create a `models/` folder in the root and move the downloaded `.gguf` file there.

### 3. Update `.env`
Change your `DEFAULT_PROVIDER` and set the path:
```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

## 🎯 Lab Objectives

1.  **Baseline Chatbot**: Observe the limitations of a standard LLM when faced with multi-step reasoning.
2.  **ReAct Loop**: Implement the `Thought-Action-Observation` cycle in `src/agent/agent.py`.
3.  **Provider Switching**: Swap between OpenAI and Gemini seamlessly using the `LLMProvider` interface.
4.  **Failure Analysis**: Use the structured logs in `logs/` to identify why the agent fails (hallucinations, parsing errors).
5.  **Grading & Bonus**: Follow the [SCORING.md](file:///Users/tindt/personal/ai-thuc-chien/day03-lab-agent/SCORING.md) to maximize your points and explore bonus metrics.

## 🛠️ How to Use This Baseline
The code is designed as a **Production Prototype**. It includes:
- **Telemetry**: Every action is logged in JSON format for later analysis.
- **Robust Provider Pattern**: Easily extendable to any LLM API.
- **Clean Skeletons**: Focus on the logic that matters—the agent's reasoning process.

---

*Happy Coding! Let's build agents that actually work.*

---

## Lab 3 Clarified Use Case (Rental Search)

### User Story
Find rental houses that are:
- Within `distance` km from `destination`.
- At most `price` million VND per month.

### Baseline Chatbot Flow
1. Customer asks a question.
2. LLM reasons directly from the prompt (no explicit tools).
3. LLM returns an answer.

### ReAct Agent Flow and Tools
Required tools:
- `find_flat(destination, distance)`: Return all rentals where `distance_km <= distance` for a specific destination.
- `find_max_price(price)`: Filter by monthly rent from the last `find_flat` result.

Required execution order:
1. Run `find_flat` first.
2. Store returned list.
3. Run `find_max_price` with the stored list and input `price`.
4. Return final matched destinations/rentals.

### Required 5 Test Cases

| STT | Destination | Distance (km) | Price (million/month) | Expected Result |
| :-- | :---------- | :------------ | :-------------------- | :-------------- |
| 1 | VinUni | 3 | 3 | Ecohome Dang Xa, Vinhomes Ocean Park Studio |
| 2 | HUST | 5 | 2 | Bach Khoa Dorm, Minh Khai Apartment |
| 3 | HAUI | 8 | 1.5 | Dien Student House, Nhon Co-living |
| 4 | PTIT | 4 | 3 | Trieu Khuc Room |
| 5 | UET | 5 | 2.5 | Mai Dich Room, Xuan Thuy Studio |

### Flowchart

```mermaid
flowchart TD
	A[User query: destination, distance, price] --> B[ReAct Thought]
	B --> C[Action: find_flat(destination, distance)]
	C --> D[Observation: nearby rentals]
	D --> E[ReAct Thought]
	E --> F[Action: find_max_price(price)]
	F --> G[Observation: rentals filtered by budget]
	G --> H[Final Answer: list matched rentals]
```

### Quick Validation

Run the new test suite:

```bash
pytest -q tests/test_rental_use_case.py
```

Run baseline chatbot:

```bash
python -m src.run_rental_chatbot
```

Run ReAct agent for rental use case:

```bash
python -m src.agent.agent
```
