"""
Requirements verification script

This script checks if all required packages are installed and importable.
Run this before starting the server to ensure all dependencies are met.

Usage:
    python check_requirements.py
"""

import sys
import importlib
from typing import List, Tuple

def check_package(package_name: str, import_name: str = None) -> Tuple[str, bool, str]:
    """Check if a package is installed and importable"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        if hasattr(module, '__version__'):
            version = getattr(module, '__version__')
        else:
            version = "unknown"
        return (package_name, True, version)
    except ImportError as e:
        return (package_name, False, str(e))

def main():
    """Check all required packages"""
    print("🔍 Checking Python package requirements...")
    print("=" * 50)
    
    # List of required packages
    packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("python-multipart", "multipart"),
        ("pymupdf", "fitz"),
        ("langchain", "langchain"),
        ("sentence-transformers", "sentence_transformers"),
        ("openai", "openai"),
        ("python-dotenv", "dotenv"),
        ("youtube-transcript-api", "youtube_transcript_api"),
        ("qdrant-client", "qdrant_client"),
        ("numpy", "numpy"),
        ("pydantic", "pydantic"),
        ("requests", "requests")  # For test script
    ]
    
    results = []
    for package_name, import_name in packages:
        package_name, success, version = check_package(package_name, import_name)
        results.append((package_name, success, version))
        
        if success:
            print(f"✅ {package_name:20} - v{version}")
        else:
            print(f"❌ {package_name:20} - NOT FOUND")
    
    print("\n" + "=" * 50)
    
    # Summary
    installed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"📊 Summary: {installed}/{total} packages installed")
    
    if installed == total:
        print("🎉 All required packages are installed!")
        print("\n✅ You can start the server with:")
        print("   uvicorn app.main:app --reload")
    else:
        print("⚠️  Some packages are missing. Install them with:")
        print("   pip install -r requirements.txt")
        
        missing = [name for name, success, _ in results if not success]
        print(f"\n❌ Missing packages: {', '.join(missing)}")
    
    # Environment check
    print("\n🔧 Environment Check:")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    
    # Check .env file
    import os
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ Found {env_file} file")
        
        # Check for required environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT", 
            "AZURE_OPENAI_DEPLOYMENT_NAME",
            "QDRANT_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("   Update your .env file with the required values")
        else:
            print("✅ All required environment variables are set")
    else:
        print(f"❌ No {env_file} file found")
        print("   Create a .env file with your configuration")

if __name__ == "__main__":
    main()
