# GitHub Codespaces Secrets Configuration

This guide explains how to configure secrets for the RemoteMotel platform in GitHub Codespaces.

## Required Secrets

### OPENAI_API_KEY (Required)

- **Purpose**: Powers knowledge base embeddings and voice AI
- **Get Key**: https://platform.openai.com/api-keys
- **Set Secret**:
  1. Go to Repository Settings → Secrets → Codespaces
  2. Click "New repository secret"
  3. Name: `OPENAI_API_KEY`
  4. Value: `sk-...` (your OpenAI API key)

## Optional Secrets (For Full Feature Testing)

### TWILIO_ACCOUNT_SID

- **Purpose**: Voice call testing
- **Get Key**: https://console.twilio.com/
- **Format**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### TWILIO_AUTH_TOKEN

- **Purpose**: Voice call authentication
- **Format**: 32-character alphanumeric string

### TWILIO_PHONE_NUMBER

- **Purpose**: Twilio phone number for testing
- **Format**: `+1XXXXXXXXXX`

### STRIPE_API_KEY

- **Purpose**: Payment link generation testing
- **Get Key**: https://dashboard.stripe.com/test/apikeys
- **Format**: `sk_test_...`

### STRIPE_WEBHOOK_SECRET

- **Purpose**: Stripe webhook verification
- **Format**: `whsec_...`

## Setting Secrets

### Repository-wide (Recommended)

1. Navigate to: `https://github.com/YOUR_ORG/front-desk/settings/secrets/codespaces`
2. Click "New repository secret"
3. Add each secret name and value
4. Secrets will be available in all Codespaces for this repo

### User-level (For Personal Use)

1. Navigate to: `https://github.com/settings/codespaces`
2. Click "New secret"
3. Add secrets that will be available across all your Codespaces
4. Select which repositories can access these secrets

### Per-Codespace (Advanced)

1. Open your Codespace
2. Click on your profile in the bottom-left
3. Select "Codespace Settings"
4. Add secrets specific to this Codespace instance

## Verification

After setting secrets, verify in Codespace terminal:

```bash
echo $OPENAI_API_KEY  # Should show sk-...
echo $TWILIO_ACCOUNT_SID  # Should show AC... or empty if not set
echo $STRIPE_API_KEY  # Should show sk_test_... or empty if not set
```

Or use the validation script:

```bash
python scripts/validate_secrets.py
```

## Troubleshooting

### Secret not available in Codespace?

- Ensure secret is set at repository level, not user level (if you want team access)
- Rebuild Codespace: Cmd/Ctrl+Shift+P → "Codespaces: Rebuild Container"
- Check secret name matches exactly (case-sensitive)
- Restart Codespace: Stop and start the Codespace

### OpenAI API errors?

- Verify key is valid:
  ```bash
  curl https://api.openai.com/v1/models \
    -H "Authorization: Bearer $OPENAI_API_KEY" | jq '.data[0].id'
  ```
- Check billing: https://platform.openai.com/account/billing
- Ensure you have credits available
- Check rate limits: https://platform.openai.com/account/limits

### Twilio errors?

- Verify credentials:
  ```bash
  curl -X GET "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID.json" \
    -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" | jq '.friendly_name'
  ```
- Check that your Twilio account is active
- Verify phone number is verified in Twilio console

### Stripe errors?

- Verify API key:
  ```bash
  curl https://api.stripe.com/v1/balance \
    -u "$STRIPE_API_KEY:" | jq '.available'
  ```
- Ensure you're using test mode keys (start with `sk_test_`)
- Check API version compatibility

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Use test credentials** for Codespaces (not production)
3. **Rotate secrets** regularly
4. **Limit secret scope** to only necessary repositories
5. **Review access** periodically in GitHub settings

## Default Behavior (No Secrets)

If you don't set optional secrets, the platform will:

- **OpenAI**: Fail to start knowledge base features (required)
- **Twilio**: Use MOCK mode for voice features (limited functionality)
- **Stripe**: Use MOCK mode for payment features (limited functionality)

## Next Steps

After configuring secrets:

1. Create a new Codespace or rebuild existing one
2. Run validation: `python scripts/validate_secrets.py`
3. Start the platform: `python apps/operator-runtime/main.py`
4. Run tests: `pytest tests/integration/ -v`

For more help, see [CODESPACES_QUICKSTART.md](CODESPACES_QUICKSTART.md).
