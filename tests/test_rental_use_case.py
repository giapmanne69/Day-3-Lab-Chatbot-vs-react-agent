import os
import sys
from typing import Dict, Any, Optional, Generator, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.tools.rental_tools import RentalSearchTools


class ScriptedLLM(LLMProvider):
    def __init__(self, responses: List[str]):
        super().__init__(model_name="scripted")
        self._responses = responses[:]

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        content = self._responses.pop(0) if self._responses else "Final Answer: No response"
        return {
            "content": content,
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            "latency_ms": 1,
            "provider": "scripted",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        yield ""


class FailingLLM(LLMProvider):
    def __init__(self):
        super().__init__(model_name="failing")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        raise RuntimeError("503 UNAVAILABLE")

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        yield ""


def test_find_max_price_requires_find_flat_first():
    tools = RentalSearchTools()
    result = tools.find_max_price(3)

    assert isinstance(result, list)
    assert result[0].get("error") == "find_flat must be called first"


def test_react_agent_runs_find_flat_then_find_max_price():
    tools = RentalSearchTools()
    llm = ScriptedLLM(
        responses=[
            'Thought: Tim nha truoc.\nAction: find_flat("VinUni", 3)',
            "Thought: Loc theo gia.\nAction: find_max_price(3)",
            "Final Answer: Da tim xong nha tro phu hop.",
        ]
    )

    agent = ReActAgent(llm=llm, tools=tools.build_tool_specs(), max_steps=5)
    final_answer = agent.run("Tim nha tro gan VinUni, cach toi da 3km, gia toi da 3 trieu/thang")

    assert "Da tim xong" in final_answer
    assert tools.call_history == ["find_flat", "find_max_price"]


def test_react_agent_handles_llm_provider_error_gracefully():
    tools = RentalSearchTools()
    agent = ReActAgent(llm=FailingLLM(), tools=tools.build_tool_specs(), max_steps=3)

    final_answer = agent.run("Tim nha tro gan PTIT trong 3 km, gia toi da 3 trieu/thang")

    assert final_answer == "LLM provider unavailable right now. Please retry in a moment."


TEST_CASES = [
    ("VinUni", 3, 3, ["Ecohome Dang Xa", "Vinhomes Ocean Park Studio"]),
    ("HUST", 5, 2, ["Bach Khoa Dorm", "Minh Khai Apartment"]),
    ("HAUI", 8, 1.5, ["Dien Student House", "Nhon Co-living"]),
    ("PTIT", 4, 3, ["Trieu Khuc Room"]),
    ("UET", 5, 2.5, ["Mai Dich Room", "Xuan Thuy Studio"]),
]


def test_five_required_cases():
    for destination, distance, price, expected_names in TEST_CASES:
        tools = RentalSearchTools()
        nearby = tools.find_flat(destination, distance)
        selected = tools.find_max_price(price)
        names = [item["name"] for item in selected]
        prices = [item["price_million"] for item in selected]

        assert nearby, f"Expected non-empty nearby list for {destination}"
        assert tools.call_history == ["find_flat", "find_max_price"]
        assert all(p < price for p in prices)
        assert prices == sorted(prices)
        assert names == expected_names
