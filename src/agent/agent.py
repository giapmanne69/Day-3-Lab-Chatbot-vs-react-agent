import re
import json
import ast
import os
from typing import List, Dict, Any, Optional
import dotenv
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []
        self._tool_map = {tool["name"]: tool for tool in tools}

    def get_system_prompt(self) -> str:
        """
        TODO: Implement the system prompt that instructs the agent to follow ReAct.
        Should include:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
You are an intelligent assistant that must follow ReAct format exactly.

You have access to these tools:
{tool_descriptions}

Strict rules:
1. If you need external information, you MUST call exactly one tool in each step.
2. When calling a tool, output only one line in this exact format:
    Action: tool_name(arg1, arg2)
3. Use plain arguments (numbers or quoted strings).
4. If you can answer, output:
    Final Answer: <your answer>
5. Never invent tools outside the list.

Required response format per step:
Thought: <reasoning>
Action: <tool_name(arguments)> OR Final Answer: <answer>
        """

    def run(self, user_input: str) -> str:
        """
        TODO: Implement the ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        scratchpad: List[str] = []
        steps = 0
        final_answer = "I reached max steps without a final answer."

        while steps < self.max_steps:
            steps += 1
            current_prompt = self._build_prompt(user_input, scratchpad)
            try:
                llm_result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            except Exception as ex:
                self._print_step_header(steps)
                print(f"Think: Model call failed at step {steps}.", flush=True)
                print(f"Observation: LLM error -> {ex}", flush=True)
                logger.log_event(
                    "LLM_ERROR",
                    {
                        "step": steps,
                        "model": self.llm.model_name,
                        "error": str(ex),
                    },
                )
                final_answer = "LLM provider unavailable right now. Please retry in a moment."
                break
            content = (llm_result.get("content") or "").strip()
            thought = self._extract_thought(content)

            tracker.track_request(
                provider=llm_result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=llm_result.get("usage", {}),
                latency_ms=llm_result.get("latency_ms", 0),
            )

            logger.log_event("AGENT_STEP", {"step": steps, "response": content})
            self.history.append({"step": steps, "model_output": content})

            answer = self._extract_final_answer(content)
            if answer is not None:
                self._print_step_header(steps)
                if thought:
                    print(f"Think: {thought}", flush=True)
                print(f"Final Answer: {answer}", flush=True)
                final_answer = answer
                break

            parsed_action = self._extract_action(content)
            if parsed_action is None:
                self._print_step_header(steps)
                if thought:
                    print(f"Think: {thought}", flush=True)
                print(f"Observation: {content or 'No actionable output from model.'}", flush=True)
                final_answer = content or "No actionable output from model."
                break

            tool_name, raw_args = parsed_action
            self._print_step_header(steps)
            if thought:
                print(f"Think: {thought}", flush=True)
            print(f"Action: {tool_name}({raw_args})", flush=True)
            observation = self._execute_tool(tool_name, raw_args)
            print(f"Observation: {self._preview(observation)}", flush=True)
            scratchpad.append(content)
            scratchpad.append(f"Observation: {observation}")

            logger.log_event(
                "TOOL_EXECUTED",
                {
                    "step": steps,
                    "tool": tool_name,
                    "args": raw_args,
                    "observation": observation,
                },
            )

        logger.log_event("AGENT_END", {"steps": steps, "final_answer": final_answer})
        return final_answer

    def _build_prompt(self, user_input: str, scratchpad: List[str]) -> str:
        if not scratchpad:
            return f"User Input: {user_input}"
        trace = "\n".join(scratchpad)
        return f"User Input: {user_input}\n\n{trace}\n\nContinue with next Thought/Action or Final Answer."

    def _extract_action(self, content: str) -> Optional[tuple[str, str]]:
        action_match = re.search(r"Action\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)", content, flags=re.DOTALL)
        if not action_match:
            return None
        return action_match.group(1), action_match.group(2).strip()

    def _extract_thought(self, content: str) -> Optional[str]:
        thought_match = re.search(r"Thought\s*:\s*(.*?)(?:\nAction\s*:|\nFinal\s*Answer\s*:|$)", content, flags=re.DOTALL)
        if not thought_match:
            return None
        thought = thought_match.group(1).strip()
        return thought or None

    def _extract_final_answer(self, content: str) -> Optional[str]:
        final_match = re.search(r"Final\s*Answer\s*:\s*(.*)", content, flags=re.DOTALL)
        if not final_match:
            return None
        return final_match.group(1).strip()

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Helper method to execute tools by name.
        """
        tool = self._tool_map.get(tool_name)
        if tool is None:
            return f"Tool {tool_name} not found."

        func = tool.get("function")
        if not callable(func):
            return f"Tool {tool_name} has no callable function."

        try:
            positional_args, keyword_args = self._parse_tool_args(args)
            result = func(*positional_args, **keyword_args)
            if isinstance(result, (dict, list)):
                return json.dumps(result, ensure_ascii=False)
            return str(result)
        except Exception as ex:
            logger.log_event("TOOL_ERROR", {"tool": tool_name, "error": str(ex)})
            return f"Tool execution error: {ex}"

    def _parse_tool_args(self, args: str) -> tuple[List[Any], Dict[str, Any]]:
        cleaned = args.strip()
        if not cleaned:
            return [], {}

        if cleaned.startswith("{") and cleaned.endswith("}"):
            parsed_obj = json.loads(cleaned)
            if isinstance(parsed_obj, dict):
                return [], parsed_obj
            if isinstance(parsed_obj, list):
                return parsed_obj, {}

        wrapped = f"({cleaned},)" if "," not in cleaned and "=" not in cleaned else f"({cleaned})"
        try:
            parsed = ast.parse(wrapped, mode="eval")
            if isinstance(parsed.body, ast.Tuple):
                values = [self._safe_literal_eval(node) for node in parsed.body.elts]
                return values, {}
        except Exception:
            pass

        # Fallback: pass raw argument string as a single positional argument.
        return [cleaned.strip('"\'')], {}

    def _safe_literal_eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            # Allow True/False/None values represented as names
            if node.id in {"True", "False", "None"}:
                return ast.literal_eval(node.id)
        return ast.literal_eval(node)

    def _print_step_header(self, step: int) -> None:
        print(f"\n[Step {step}]", flush=True)

    def _preview(self, observation: str, limit: int = 280) -> str:
        text = observation.replace("\n", " ").strip()
        if len(text) <= limit:
            return text
        return f"{text[:limit]}... (truncated)"


def _build_rental_agent(model: str) -> ReActAgent:
    dotenv.load_dotenv()
    model = (model or "").strip().lower()

    if model == "openai":
        from src.core.openai_provider import OpenAIProvider

        llm = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
    elif model == "google":
        from src.core.google_provider import GoogleProvider

        llm = GoogleProvider(api_key=os.getenv("STUDIO_API_KEY"))
    else:
        raise ValueError("Only 'openai' or 'google' is supported in this runner.")

    from src.tools.rental_tools import RentalSearchTools

    rental_tools = RentalSearchTools()
    return ReActAgent(llm=llm, tools=rental_tools.build_tool_specs(), max_steps=6)


def main():
    model = input("Use provider (openai/google): ")
    agent = _build_rental_agent(model)

    print("\nNhap yc theo mau: Tim nha tro gan <destination> trong <distance> km, gia toi da <price> trieu/thang")
    print("Nhap 'exit' de thoat.\n")

    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        answer = agent.run(user_input)
        print(f"Agent: {answer}\n")


if __name__ == "__main__":
    main()
