import argparse
import json
import os
import pathlib
from typing import List

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError # type: ignore

DEFAULT_MODEL = "gpt-4o-mini"

BANNER = "-----" 

def read_messages(path: pathlib.Path) -> List[str]:
    """Return non‑empty, stripped lines from *path*."""
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def build_prompt(template: str, message: str) -> str:
    """Combine template and message into a single prompt string."""
    return f"{template}\n\n{BANNER}\nMessage:\n{message}\n{BANNER}"


def write_json(path: pathlib.Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("messages_file", type=pathlib.Path, help="Path to val.txt with one message per line.")
    p.add_argument("template_file", type=pathlib.Path, help="Path to prompt template (e.g. short_prompt.txt).")
    p.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI chat model (default: %(default)s).")
    p.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("outputs"), help="Directory for JSON results.")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing JSON files.")
    args = p.parse_args()

    # API key setup
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found (set env var or .env file).")

    client = OpenAI(api_key=api_key)

    template_text = args.template_file.read_text(encoding="utf-8").rstrip()
    messages = read_messages(args.messages_file)
    if not messages:
        raise ValueError("No messages found in messages_file.")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for idx, message in enumerate(messages, 1):
        prompt = build_prompt(template_text, message)
        out_path = args.output_dir / f"example_{idx:05d}.json"
        if out_path.exists() and not args.overwrite:
            continue

        try:
            response = client.chat.completions.create(
                model=args.model,
                messages=[{"role": "user", "content": prompt}],
            )
            assistant_content = response.choices[0].message.content
            data = {
                "message": message,
                "prompt": prompt,
                "response": assistant_content,
            }
        except OpenAIError as e:
            print(f"[ERROR] ({idx}) {e}")

        write_json(out_path, data)


if __name__ == "__main__":
    main()
