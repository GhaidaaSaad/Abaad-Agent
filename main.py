import argparse
from loguru import logger
from dotenv import load_dotenv

from graph.workflow import build_workflow


def run_demo():
    """Run demo with user input."""
    try:
        print("\n" + "=" * 60)
        print("ABAAD-Agent - Unity Game Asset Generator")
        print("=" * 60)
        print("\nDescribe your game and required assets:")
        print("Example: 'Dark fantasy RPG. Need 3 character sprites, castle 3D model, dungeon music, 5 combat SFX. Style: dark, moody, gothic'")
        print("-" * 60)
        
        while True:
            prompt = input("\nDescription: ").strip()
            
            if not prompt:
                print("❌ Error: Description cannot be empty. Please try again.")
                continue
            
            if len(prompt) < 10:
                print("❌ Error: Description must be at least 10 characters long. Please try again.")
                continue
            
            break
        
        logger.info(f"Starting demo run with prompt: {prompt[:50]}...")
        app = build_workflow()
        state = {"prompt": prompt}  # No preferences!
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


