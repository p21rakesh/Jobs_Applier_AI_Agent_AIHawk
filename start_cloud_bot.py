import os
import importlib

if __name__ == "__main__":
    print("Searching for the AIHawk Cloud Automation Engine...")
    
    # Check all files inside the src directory
    src_dir = "src"
    if os.path.exists(src_dir):
        files = os.listdir(src_dir)
        print(f"Files found in src/: {files}")
        
        # Look for manager or runner files
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                module_name = f"src.{file[:-3]}"
                try:
                    mod = importlib.import_module(module_name)
                    # List classes inside each module to spot the worker engine
                    classes = [x for x in dir(mod) if not x.startswith("_")]
                    print(f"Module {module_name} contains internal tools: {classes}")
                except Exception as e:
                    pass
