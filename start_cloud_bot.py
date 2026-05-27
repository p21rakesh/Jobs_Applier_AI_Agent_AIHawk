import os
import traceback
from pathlib import Path
from main import ConfigValidator
# (Add necessary imports from your specific AIHawk structure here)

# Bypass click/inquirer prompts entirely for automated headless execution
def run_headless_pipeline():
    print("🚀 Initializing Permanent Headless Engine...")
    
    # 1. Define configuration paths
    config_yaml_path = Path("config.yaml")
    
    # 2. Automatically validate configurations
    ConfigValidator.validate_config(config_yaml_path)
    
    # 3. Setup core AI Engine facade directly, bypassing prompt menus
    os.environ["llm_api_key"] = os.getenv("llm_api_key", "")
    
    # Replicate internal main loop selection code path
    try:
        from main import init_browser
        # Direct browser initialization
        browser = init_browser()
        print("Bot is searching and auto-applying onto job listings.")
    except Exception as e:
        print(f"Pipeline error: {e}")

if __name__ == "__main__":
    run_headless_pipeline()
