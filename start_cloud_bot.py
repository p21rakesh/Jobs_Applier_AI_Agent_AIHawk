import os
from src.job import Job

# Force configuration to run without showing any user interface menu prompts
if __name__ == "__main__":
    print("Initializing AIHawk Headless Application Engine...")
    
    # Fire up the main background automation bot directly
    bot = Job()
    bot.start_applying()
