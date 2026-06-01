import os
import dotenv

from src.core.google_provider import GoogleProvider
from src.core.openai_provider import OpenAIProvider


def _build_provider(model: str):
    dotenv.load_dotenv()
    model = (model or "").strip().lower()

    if model == "openai":
        return OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
    if model == "google":
        return GoogleProvider(api_key=os.getenv("STUDIO_API_KEY"))
    raise ValueError("Only 'openai' or 'google' is supported in this runner.")


def main():
    provider_name = input("Use provider (openai/google): ")
    provider = _build_provider(provider_name)

    print("\nBaseline chatbot mode (no tools).")
    print("Nhap cau hoi nha tro tu do. Nhap 'exit' de thoat.\n")

    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        try:
            result = provider.generate(user_input)
            print(f"Chatbot: {result['content']}\n")
        except Exception as ex:
            print(f"Chatbot: Provider unavailable right now ({ex}). Please retry.\n")


if __name__ == "__main__":
    main()
