"""
Quick validation script for upgraded system
Run this to check if all components are configured correctly
"""

import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check_mark(condition, message):
    if condition:
        print(f"{GREEN}✅ {message}{RESET}")
        return True
    else:
        print(f"{RED}❌ {message}{RESET}")
        return False

def warning(message):
    print(f"{YELLOW}⚠️  {message}{RESET}")

print("\n" + "="*60)
print("🔍 System Validation - Config & Logging Upgrade")
print("="*60 + "\n")

all_checks_passed = True

# 1. Check if .env exists
env_exists = Path(".env").exists()
all_checks_passed &= check_mark(env_exists, ".env file exists")
if not env_exists:
    warning("  Create .env from .env.example and fill in your credentials")

# 2. Check if config.py can be imported
try:
    from config import (
        MQTT_BROKER, MQTT_PORT, MQTT_TOPIC,
        DATABASE_PATH, EMAIL_SENDER, EMAIL_PASSWORD,
        Thresholds, get_config_summary, validate_config
    )
    check_mark(True, "config.py imports successfully")
    
    # 3. Validate configuration
    try:
        validate_config()
        check_mark(True, "Configuration validation passed")
    except ValueError as e:
        check_mark(False, f"Configuration validation failed: {e}")
        all_checks_passed = False
        
    # 4. Display configuration summary
    print("\n📋 Configuration Summary:")
    for key, value in get_config_summary().items():
        if 'password' in key.lower():
            value = "***" if value else "NOT_SET"
        print(f"   • {key}: {value}")
        
    # 5. Check email credentials
    email_configured = bool(EMAIL_SENDER and EMAIL_PASSWORD)
    if not email_configured:
        warning("Email credentials not configured in .env")
        print("   Set EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER in .env")
    else:
        check_mark(True, f"Email configured: {EMAIL_SENDER}")
        
except ImportError as e:
    check_mark(False, f"Failed to import config.py: {e}")
    all_checks_passed = False

# 6. Check if logger.py can be imported
try:
    from logger import (
        setup_logger, get_gateway_logger, 
        get_dashboard_logger, get_simulator_logger
    )
    check_mark(True, "logger.py imports successfully")
    
    # 7. Check if logs directory exists
    logs_dir = Path("logs")
    if logs_dir.exists():
        check_mark(True, f"logs/ directory exists")
        
        # List log files
        log_files = list(logs_dir.glob("*.log"))
        if log_files:
            print(f"   📄 Log files found: {len(log_files)}")
            for log_file in log_files:
                size_kb = log_file.stat().st_size / 1024
                print(f"      • {log_file.name} ({size_kb:.1f} KB)")
        else:
            warning("No log files yet (will be created when components run)")
    else:
        warning("logs/ directory doesn't exist (will be created automatically)")
        
except ImportError as e:
    check_mark(False, f"Failed to import logger.py: {e}")
    all_checks_passed = False

# 8. Check if database exists
try:
    from config import DATABASE_PATH
    db_path = Path(DATABASE_PATH)
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        check_mark(True, f"Database exists: {db_path.name} ({size_mb:.2f} MB)")
    else:
        warning(f"Database not found at {db_path}")
        warning("Will be created when gateway starts")
except Exception as e:
    warning(f"Could not check database: {e}")

# 9. Check if model files exist
print("\n🤖 ML Models:")
try:
    from config import MODEL_PATHS, BASE_DIR
    models_dir = BASE_DIR / "models"
    
    if models_dir.exists():
        for param, model_name in [
            ("temperature", "model_Temperature_6h.pkl"),
            ("ph", "model_pH_6h.pkl"),
            ("do", "model_Dissolved_Oxygen_6h.pkl"),
            ("turbidity", "model_Turbidity_6h.pkl")
        ]:
            model_path = models_dir / model_name
            scaler_name = model_name.replace("_6h.pkl", ".pkl").replace("model_", "scaler_")
            scaler_path = models_dir / scaler_name
            
            model_exists = model_path.exists()
            scaler_exists = scaler_path.exists()
            
            if model_exists and scaler_exists:
                print(f"   {GREEN}✅{RESET} {param}: model + scaler found")
            elif model_exists:
                print(f"   {YELLOW}⚠️{RESET}  {param}: model found, scaler missing")
            else:
                print(f"   {RED}❌{RESET} {param}: model missing")
                all_checks_passed = False
    else:
        check_mark(False, "models/ directory not found")
        all_checks_passed = False
        
except Exception as e:
    warning(f"Could not check models: {e}")

# 10. Check if python-dotenv is installed
try:
    import dotenv
    check_mark(True, "python-dotenv package installed")
except ImportError:
    check_mark(False, "python-dotenv not installed")
    all_checks_passed = False
    print(f"   {YELLOW}Run: pip install python-dotenv{RESET}")

# 11. Check if .gitignore exists and contains .env
gitignore = Path(".gitignore")
if gitignore.exists():
    content = gitignore.read_text()
    if ".env" in content:
        check_mark(True, ".gitignore protects .env file")
    else:
        check_mark(False, ".env not in .gitignore - SECURITY RISK!")
        all_checks_passed = False
else:
    check_mark(False, ".gitignore file missing - SECURITY RISK!")
    all_checks_passed = False

# Final result
print("\n" + "="*60)
if all_checks_passed:
    print(f"{GREEN}🎉 All checks passed! System is ready.{RESET}")
    print("\nNext steps:")
    print("  1. Run gateway: python gateway/gateway_sqlite.py")
    print("  2. Run simulator: python gateway/simulator_publish.py")
    print("  3. Run dashboard: streamlit run dashboard/app_simple_sqlite.py")
else:
    print(f"{RED}⚠️  Some checks failed. Please fix issues above.{RESET}")
    print("\nFor help, see:")
    print("  • CONFIG_LOGGING_README.md")
    print("  • UPGRADE_SUMMARY.md")

print("="*60 + "\n")
