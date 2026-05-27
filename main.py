import base64
import sys
import os
from pathlib import Path
import traceback
from typing import List, Optional, Tuple, Dict

import yaml
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import re

# Library imports
from src.libs.resume_and_cover_builder import ResumeFacade, ResumeGenerator, StyleManager
from src.resume_schemas.resume import Resume
from src.logging import logger
from src.utils.chrome_utils import init_browser
from src.utils.constants import (
    PLAIN_TEXT_RESUME_YAML,
    SECRETS_YAML,
    WORK_PREFERENCES_YAML,
)

# Uncommented these as they are required for the "Apply for Jobs" mode
from ai_hawk.bot_facade import AIHawkBotFacade

class ConfigError(Exception):
    """Custom exception for configuration-related errors."""
    pass

class ConfigValidator:
    """Validates configuration and secrets YAML files."""
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    REQUIRED_CONFIG_KEYS = {
        "remote": bool,
        "experience_level": dict,
        "job_types": dict,
        "date": dict,
        "positions": list,
        "locations": list,
        "location_blacklist": list,
        "distance": int,
        "company_blacklist": list,
        "title_blacklist": list,
    }
    EXPERIENCE_LEVELS = ["internship", "entry", "associate", "mid_senior_level", "director", "executive"]
    JOB_TYPES = ["full_time", "contract", "part_time", "temporary", "internship", "other", "volunteer"]
    DATE_FILTERS = ["all_time", "month", "week", "24_hours"]
    APPROVED_DISTANCES = {0, 5, 10, 25, 50, 100}

    @staticmethod
    def load_yaml(yaml_path: Path) -> dict:
        try:
            with open(yaml_path, "r") as stream:
                return yaml.safe_load(stream)
        except Exception as exc:
            raise ConfigError(f"Error reading YAML file {yaml_path}: {exc}")

    @classmethod
    def validate_config(cls, config_yaml_path: Path) -> dict:
        parameters = cls.load_yaml(config_yaml_path)
        for key, expected_type in cls.REQUIRED_CONFIG_KEYS.items():
            if key not in parameters:
                parameters[key] = [] if "blacklist" in key else None
            elif not isinstance(parameters[key], expected_type):
                if "blacklist" in key and parameters[key] is None:
                    parameters[key] = []
                else:
                    raise ConfigError(f"Invalid type for key '{key}'")
        return parameters

    @staticmethod
    def validate_secrets(secrets_yaml_path: Path) -> str:
        secrets = ConfigValidator.load_yaml(secrets_yaml_path)
        if "llm_api_key" not in secrets or not secrets["llm_api_key"]:
            raise ConfigError("Missing or empty 'llm_api_key' in secrets.yaml")
        return secrets["llm_api_key"]

class FileManager:
    REQUIRED_FILES = [SECRETS_YAML, WORK_PREFERENCES_YAML, PLAIN_TEXT_RESUME_YAML]

    @staticmethod
    def validate_data_folder(app_data_folder: Path) -> Tuple[Path, Path, Path, Path]:
        if not app_data_folder.is_dir():
            raise FileNotFoundError(f"Data folder not found: {app_data_folder}")
        for file in FileManager.REQUIRED_FILES:
            if not (app_data_folder / file).exists():
                raise FileNotFoundError(f"Missing: {file}")
        output_folder = app_data_folder / "output"
        output_folder.mkdir(exist_ok=True)
        return (app_data_folder / SECRETS_YAML, app_data_folder / WORK_PREFERENCES_YAML, 
                app_data_folder / PLAIN_TEXT_RESUME_YAML, output_folder)

    @staticmethod
    def get_uploads(plain_text_resume_file: Path) -> Dict[str, Path]:
        return {"plainTextResume": plain_text_resume_file}

def run_job_application(parameters: dict, llm_api_key: str):
    """
    Automated job application logic (Headless).
    """
    try:
        logger.info("Starting automated job application process...")
        bot_facade = AIHawkBotFacade(llm_api_key, parameters)
        bot_facade.apply_jobs()
    except Exception as e:
        logger.exception(f"Error during job application: {e}")
        raise

def create_tailored_resume_headless(parameters: dict, llm_api_key: str, job_url: str):
    """
    Generates a tailored resume without interactive prompts.
    """
    try:
        logger.info(f"Generating tailored resume for: {job_url}")
        with open(parameters["uploads"]["plainTextResume"], "r", encoding="utf-8") as file:
            plain_text_resume = file.read()

        style_manager = StyleManager()
        # Hardcoding "default" style
        style_manager.set_selected_style("default")
        
        resume_generator = ResumeGenerator()
        resume_object = Resume(plain_text_resume)
        driver = init_browser() # Ensure this is configured for headless in your src/utils
        
        resume_facade = ResumeFacade(            
            api_key=llm_api_key,
            style_manager=style_manager,
            resume_generator=resume_generator,
            resume_object=resume_object,
            output_path=parameters["outputFileDirectory"],
        )
        resume_facade.set_driver(driver)
        resume_facade.link_to_job(job_url)
        
        result_base64, suggested_name = resume_facade.create_resume_pdf_job_tailored()         
        pdf_data = base64.b64decode(result_base64)
        
        output_dir = Path(parameters["outputFileDirectory"]) / suggested_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "resume_tailored.pdf"
        with open(output_path, "wb") as file:
            file.write(pdf_data)
        logger.info(f"Resume saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate resume: {e}")
        raise

def main():
    """Main entry point - Headless Version"""
    try:
        # 1. Setup paths
        data_folder = Path("data_folder")
        secrets_file, config_file, resume_file, output_folder = FileManager.validate_data_folder(data_folder)

        # 2. Load Config
        config = ConfigValidator.validate_config(config_file)
        llm_api_key = ConfigValidator.validate_secrets(secrets_file)
        config["uploads"] = FileManager.get_uploads(resume_file)
        config["outputFileDirectory"] = output_folder

        # 3. Headless Logic Selection
        # If a URL is passed as an argument, we tailor a resume for that URL.
        # Otherwise, we run the full Job Applier bot.
        if len(sys.argv) > 1:
            job_url = sys.argv[1]
            logger.info(f"URL detected. Mode: Tailor Resume/Cover Letter for {job_url}")
            create_tailored_resume_headless(config, llm_api_key, job_url)
        else:
            logger.info("No URL provided. Mode: Automated Job Application ('Apply for Jobs')")
            run_job_application(config, llm_api_key)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
