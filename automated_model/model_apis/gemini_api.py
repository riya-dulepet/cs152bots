import argparse
import json
import os
import pathlib
from typing import List

import google.generativeai as genai # type: ignore
from dotenv import load_dotenv

DEFAULT_MODEL = "models/gemini-1.5-flash"

BANNER = "-----"

def read_messages(path: pathlib.Path) -> List[str]:
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

def build_prompt(template: str, message: str) -> str:
    return f"{template}\n\n{BANNER}\nMessage:\n{message}\n{BANNER}"

def write_json(path: pathlib.Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("messages_file", type=pathlib.Path, help="Path to val.txt with one message per line.")
    p.add_argument("template_file", type=pathlib.Path, help="Path to prompt template (e.g. short_prompt.txt).")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model (default: %(default)s).")
    p.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("outputs"), help="Directory for JSON results.")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing JSON files.")
    args = p.parse_args()

    # Load API key
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found (set env var or .env file).")

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(model_name=args.model)

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
            response = model.generate_content(prompt)
            content = response.text
            data = {
                "message": message,
                "prompt": prompt,
                "response": content,
            }
        except Exception as e:
            print(f"[ERROR] ({idx}) {e}")
            continue

        write_json(out_path, data)

if __name__ == "__main__":
    main()