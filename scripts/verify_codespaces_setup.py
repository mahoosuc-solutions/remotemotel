#!/usr/bin/env python3
"""
Comprehensive verification script for Codespaces setup.
Checks all components and reports status.
"""

import asyncio
import os
import subprocess
import sys
from typing import Tuple


def run_command(cmd: str) -> Tuple[bool, str]:
    """Run a shell command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (result.returncode == 0, result.stdout + result.stderr)
    except Exception as e:
        return (False, str(e))


async def check_database():
    """Check database connectivity and data."""
    print("Checking database...")

    # Check container
    success, output = run_command(
        "docker compose -f docker-compose.postgres.yml ps | grep Up"
    )
    if not success:
        return (False, "PostgreSQL container not running")

    # Check connectivity
    success, output = run_command(
        "docker compose -f docker-compose.postgres.yml exec -T postgres "
        + "psql -U stayhive -d stayhive -c 'SELECT 1'"
    )
    if not success:
        return (False, "Cannot connect to database")

    # Check seeded data
    success, output = run_command(
        "docker compose -f docker-compose.postgres.yml exec -T postgres "
        + "psql -U stayhive -d stayhive -t -c 'SELECT COUNT(*) FROM rooms'"
    )
    if not success or int(output.strip()) == 0:
        return (False, "Database not seeded")

    return (True, f"✓ {output.strip()} rooms seeded")


async def check_knowledge_base():
    """Check knowledge base ingestion."""
    print("Checking knowledge base...")

    # Check if OpenAI key is set
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key in ["${OPENAI_API_KEY}", "your-openai-api-key-here"]:
        return (False, "OpenAI API key not configured")

    try:
        from packages.knowledge.service import KnowledgeService

        service = KnowledgeService()
        docs = await service.list_documents("remotemotel", limit=50)

        if len(docs) == 0:
            return (False, "No documents ingested")

        return (True, f"✓ {len(docs)} documents ingested")
    except Exception as e:
        return (False, f"Error: {str(e)}")


async def check_environment():
    """Check environment variables."""
    print("Checking environment variables...")

    required = ["DATABASE_URL", "OPENAI_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        return (False, f"Missing: {', '.join(missing)}")

    return (True, "✓ All required variables set")


async def check_migrations():
    """Check database migrations."""
    print("Checking database migrations...")

    success, output = run_command(
        "docker compose -f docker-compose.postgres.yml exec -T postgres "
        + "psql -U stayhive -d stayhive -c \"\\dt\" | grep -E 'rooms|bookings|voice_calls'"
    )
    if not success:
        return (False, "Migrations not applied (tables missing)")

    return (True, "✓ Database tables created")


async def check_virtual_env():
    """Check virtual environment."""
    print("Checking virtual environment...")

    if not os.path.exists(".venv/bin/python"):
        return (False, "Virtual environment not created")

    # Check if key packages are installed
    success, output = run_command(".venv/bin/python -c 'import fastapi, sqlalchemy'")
    if not success:
        return (False, "Dependencies not installed")

    return (True, "✓ Virtual environment ready")


async def main():
    """Run all verification checks."""
    print("=" * 50)
    print("Codespaces Setup Verification")
    print("=" * 50)
    print()

    checks = {
        "Virtual Environment": check_virtual_env(),
        "Environment Variables": check_environment(),
        "Database Migrations": check_migrations(),
        "Database Connectivity": check_database(),
        "Knowledge Base": check_knowledge_base(),
    }

    results = {}
    for name, check_coro in checks.items():
        success, message = await check_coro
        results[name] = (success, message)
        status = "✓" if success else "✗"
        print(f"{status} {name}: {message}")

    print()
    print("=" * 50)

    all_passed = all(success for success, _ in results.values())

    if all_passed:
        print("✓ All checks passed!")
        print()
        print("Platform is ready. Start server with:")
        print("  python apps/operator-runtime/main.py")
        print()
        print("Run tests with:")
        print("  pytest tests/integration/ -v")
        return 0
    else:
        print("✗ Some checks failed")
        print()
        print("To fix:")
        print("  1. Check .env.local configuration")
        print("  2. Run setup: bash .devcontainer/setup.sh")
        print("  3. See CODESPACES_QUICKSTART.md for help")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
