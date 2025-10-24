#!/usr/bin/env python3
"""Validate that required secrets are configured correctly."""

import os
import sys
from typing import Tuple


def check_secret(name: str, required: bool = False) -> Tuple[bool, str]:
    """Check if a secret is configured."""
    value = os.getenv(name)

    if not value:
        status = "❌ MISSING" if required else "⚠️  NOT SET"
        return (False, status)

    # Check for placeholder values
    placeholders = [
        "your-openai-api-key-here",
        "MOCK",
        "sk-your-openai-api-key-here",
        "${OPENAI_API_KEY}",
        "${TWILIO_ACCOUNT_SID}",
        "${TWILIO_AUTH_TOKEN}",
        "${STRIPE_API_KEY}",
    ]
    if value in placeholders:
        return (False, "⚠️  DEFAULT/PLACEHOLDER VALUE (not configured)")

    # Basic format validation
    if name == "OPENAI_API_KEY":
        if not value.startswith("sk-"):
            return (False, "❌ INVALID FORMAT (should start with 'sk-')")

    if name == "TWILIO_ACCOUNT_SID":
        if not value.startswith("AC"):
            return (False, "⚠️  INVALID FORMAT (should start with 'AC')")

    if name == "STRIPE_API_KEY":
        if not value.startswith("sk_"):
            return (False, "⚠️  INVALID FORMAT (should start with 'sk_')")

    # Mask the value for display
    if len(value) > 8:
        masked = f"{value[:4]}...{value[-4:]}"
    else:
        masked = "***"

    return (True, f"✓ CONFIGURED ({masked})")


def main():
    """Validate all secrets."""
    print("=" * 50)
    print("Secret Configuration Validation")
    print("=" * 50)
    print()

    secrets = {
        "Required Secrets": [
            ("OPENAI_API_KEY", True),
            ("DATABASE_URL", True),
        ],
        "Optional Secrets (Voice Testing)": [
            ("TWILIO_ACCOUNT_SID", False),
            ("TWILIO_AUTH_TOKEN", False),
            ("TWILIO_PHONE_NUMBER", False),
        ],
        "Optional Secrets (Payment Testing)": [
            ("STRIPE_API_KEY", False),
            ("STRIPE_WEBHOOK_SECRET", False),
        ],
    }

    all_valid = True
    optional_configured = []

    for category, secret_list in secrets.items():
        print(f"{category}:")
        for secret_name, required in secret_list:
            valid, status = check_secret(secret_name, required)
            print(f"  {secret_name}: {status}")
            if required and not valid:
                all_valid = False
            if not required and valid:
                optional_configured.append(secret_name)
        print()

    # Summary
    print("=" * 50)
    if all_valid:
        print("✓ All required secrets configured!")
        print()
        print("Platform ready for:")
        print("  ✓ Database operations")
        print("  ✓ Knowledge base (semantic search)")
        if "TWILIO_ACCOUNT_SID" in optional_configured:
            print("  ✓ Voice AI (Twilio configured)")
        else:
            print("  ⚠️  Voice AI (MOCK mode - limited functionality)")
        if "STRIPE_API_KEY" in optional_configured:
            print("  ✓ Payment links (Stripe configured)")
        else:
            print("  ⚠️  Payment links (MOCK mode - limited functionality)")
        print()
        print("Next steps:")
        print("  - Start server: python apps/operator-runtime/main.py")
        print("  - Run tests: pytest tests/integration/ -v")
        print("  - Verify setup: python scripts/verify_codespaces_setup.py")
        sys.exit(0)
    else:
        print("❌ Missing required secrets!")
        print()
        print("To fix:")
        print("  1. Set secrets at: https://github.com/settings/codespaces")
        print("  2. See CODESPACES_SECRETS.md for detailed instructions")
        print("  3. Rebuild container: Cmd/Ctrl+Shift+P → Rebuild Container")
        sys.exit(1)


if __name__ == "__main__":
    main()
