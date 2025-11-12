import argparse
import os
from loguru import logger
from dotenv import load_dotenv

from graph.workflow import build_workflow


EXAMPLE_PROMPTS = [
    "An emotional fantasy forest adventure with glowing trees and gentle music.",
    "A cyberpunk city with neon lights and flying cars at night.",
    "A serene underwater kingdom with bioluminescent creatures and coral castles.",
    "A steampunk Victorian era with brass gears and steam-powered machines.",
    "A mystical desert oasis with ancient ruins and magical sandstorms.",
]


def get_user_prompt() -> str:
    """Prompt user for input with validation and examples."""
    print("\n" + "=" * 60)
    print("ABAAD-Agent - Game Asset Generator")
    print("=" * 60)
    print("\nExample prompts:")
    for i, example in enumerate(EXAMPLE_PROMPTS, 1):
        print(f"  {i}. {example}")
    print("\n" + "-" * 60)
    
    while True:
        prompt = input("\nEnter your description: ").strip()
        
        if not prompt:
            print("❌ Error: Description cannot be empty. Please try again.")
            continue
        
        if len(prompt) < 10:
            print("❌ Error: Description must be at least 10 characters long. Please try again.")
            continue
        
        return prompt


def run_demo():
    """Run demo with user input."""
    try:
        prompt = get_user_prompt()
        logger.info(f"Starting demo run with prompt: {prompt[:50]}...")
        app = build_workflow()
        state = {"prompt": prompt}
        result = app.invoke(state)
        zip_path = result.get("zip_path")
        if zip_path:
            logger.info(f"Job finished. Zip: {zip_path}")
            print(f"\n✅ Success! Bundle saved to: {zip_path}")
        else:
            logger.error("Job finished but no zip path found")
            print("\n❌ Error: Generation completed but zip file not found.")
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation cancelled by user.")
        logger.info("Demo cancelled by user")
    except Exception as e:
        logger.exception("Demo failed")
        print(f"\n❌ Error: {e}")


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
