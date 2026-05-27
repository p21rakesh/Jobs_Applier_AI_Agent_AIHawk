import os
from src.job import Job

if __name__ == "__main__":
    print("Initializing AIHawk Headless Application Engine...")
    
    # Initialize the main job object
    bot = Job()
    
    # Look through the object to find the method that starts the bot
    possible_methods = ['start_applying', 'apply', 'run', 'start', 'execute']
    executed = False
    
    for method_name in possible_methods:
        if hasattr(bot, method_name):
            print(f"Found automation method: {method_name}(). Running now...")
            getattr(bot, method_name)()
            executed = True
            break
            
    if not executed:
        # If none of the common names match, list everything inside the file so we can see it
        print("Could not find standard start method. Available internal functions are:")
        print([attr for attr in dir(bot) if not attr.startswith('_')])
