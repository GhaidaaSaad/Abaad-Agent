import argparse
import os
from loguru import logger
from dotenv import load_dotenv

from graph.workflow import build_workflow


def run_demo():
    prompt = "An emotional fantasy forest adventure with glowing trees and gentle music."
    logger.info("Starting demo run")
    app = build_workflow()
    state = {"prompt": prompt}
    result = app.invoke(state)
    logger.info(f"Job finished. Zip: {result.get('zip_path')}")
    print(result.get("zip_path", ""))


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="ABAAD-Agent MVP runner")
    parser.add_argument("--demo", action="store_true", help="Run a demo generation")
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        print("Usage: python main.py --demo  (or run the FastAPI app in api/app.py)")


if __name__ == "__main__":
    main()


