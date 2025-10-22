# Stripe Payment Integration for BizHive Agent Platform

## Overview

BizHive Agent uses **Stripe's official MCP server** for payment processing. This provides secure, maintained payment functionality without requiring us to build and maintain Stripe integration code.

## Architecture

### Multi-Server MCP Architecture

```
Claude Desktop / AI Client
    │
    ├── StayHive MCP Server (Business Logic)
    │   ├── check_availability
    │   ├── create_reservation
    │   ├── create_lead
    │   └── [other hospitality tools]
    │
    └── Stripe MCP Server (Payment Processing)
        ├── create_payment_link
        ├── create_checkout_session
        ├── retrieve_payment_status
        ├── list_customers
        └── [other Stripe tools]
```

**How it works:**
1. Guest inquires about booking → StayHive handles it
2. Reservation created → StayHive generates reservation ID and pricing
3. Payment needed → AI automatically calls Stripe MCP server
4. Payment link generated → Stripe returns secure payment URL
5. Optional: StayHive stores payment link ID with reservation

## Setup Instructions

### Option 1: Stripe's Hosted MCP Server (Recommended)

Stripe provides a hosted MCP server at `https://mcp.stripe.com`.

**Claude Desktop Configuration** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "stayhive": {
      "command": "python",
      "args": ["-m", "mcp_servers.stayhive.server"],
      "cwd": "/path/to/bizhive-agent"
    },
    "stripe": {
      "url": "https://mcp.stripe.com"
    }
  }
}
```

**Authentication:**
- Stripe MCP uses OAuth Dynamic Client Registration
- When you add Stripe MCP, it opens an OAuth consent form
- Authorize the client to access your Stripe account
- Only Stripe admins can install the MCP

### Option 2: Local Stripe MCP Server

For development or air-gapped environments, run Stripe MCP locally.

**Installation:**
```bash
# Clone Stripe agent toolkit
git clone https://github.com/stripe/agent-toolkit.git
cd agent-toolkit/modelcontextprotocol

# Follow Stripe's setup instructions
npm install
npm run build
```

**Configuration:**
```json
{
  "mcpServers": {
    "stayhive": {
      "command": "python",
      "args": ["-m", "mcp_servers.stayhive.server"],
      "cwd": "/path/to/bizhive-agent"
    },
    "stripe": {
      "command": "node",
      "args": ["/path/to/stripe-mcp/dist/index.js"],
      "env": {
        "STRIPE_API_KEY": "sk_test_..."
      }
    }
  }
}
```

### Option 3: Cursor IDE Configuration

Similar configuration in Cursor's MCP settings:

```json
{
  "mcpServers": {
    "stayhive": {...},
    "stripe": {
      "url": "https://mcp.stripe.com"
    }
  }
}
```

## Usage Patterns

### Pattern 1: Reservation with Payment

**Guest Workflow:**
```
Guest: "I'd like to book a room for June 1-3"
AI → StayHive: check_availability(...)
AI: "We have rooms available. I'll need your details..."
Guest: "I'm John Doe, john@example.com, 555-1234"
AI → StayHive: create_reservation(...)
AI: "Reservation RSV-20250601-ABC123 created. Total: $360"
AI: "Would you like to pay now?"
Guest: "Yes, I'll pay a deposit"
AI → Stripe: create_payment_link(amount=20000, description="Deposit for RSV-20250601-ABC123")
AI: "Here's your secure payment link: https://checkout.stripe.com/..."
```

### Pattern 2: Inquiry with Payment Intent

**Guest Workflow:**
```
Guest: "Do you have pet-friendly rooms? I'd like to reserve one."
AI → StayHive: check_availability(pets=true)
AI: "Yes! Pet-Friendly Room available for $160/night (includes $20 pet fee)"
Guest: "Perfect, book it for me"
AI → StayHive: create_reservation(...)
AI → Stripe: create_checkout_session(...)
AI: "Reservation confirmed! Complete payment here: [link]"
```

## Stripe MCP Tools Available

Based on Stripe's official MCP server, these tools are available:

### Payment Links
- `create_payment_link` - Generate payment URL for specific amount
- `retrieve_payment_link` - Get payment link details
- `list_payment_links` - List all payment links

### Checkout Sessions
- `create_checkout_session` - Full checkout page with customization
- `retrieve_checkout_session` - Get session details
- `expire_checkout_session` - Cancel a checkout session

### Customers
- `create_customer` - Create Stripe customer record
- `retrieve_customer` - Get customer details
- `update_customer` - Update customer information
- `list_customers` - List customers

### Payment Intents
- `create_payment_intent` - Create payment intent
- `retrieve_payment_intent` - Get payment status
- `confirm_payment_intent` - Confirm payment

### Refunds
- `create_refund` - Issue refund
- `retrieve_refund` - Get refund details

## Integration with StayHive Reservations

### Storing Payment Information

When Stripe creates a payment, optionally store the reference:

```python
# In StayHive create_reservation response
{
    "reservation_id": "RSV-20250601-ABC123",
    "total_price": 360,
    "payment_link_id": "plink_1234567890",  # From Stripe
    "payment_status": "pending"
}
```

### Payment Status Tracking

The AI can check payment status:

```
AI → Stripe: retrieve_payment_intent(payment_intent_id="pi_...")
Stripe: {"status": "succeeded", "amount": 36000}
AI → StayHive: update_reservation_status(reservation_id="RSV-...", status="confirmed")
```

## Fallback: Mock Payment (Development/Testing)

StayHive includes a mock `generate_payment_link` tool for development when Stripe MCP isn't available:

**When to use:**
- ✅ Local development without Stripe account
- ✅ Automated testing
- ✅ Demonstration mode
- ✅ Offline operation

**Limitations:**
- ❌ No actual payment processing
- ❌ No payment validation
- ❌ Returns mock URLs only

**Configuration:**
```yaml
# config.yaml
mcp:
  fallback_payment: true  # Use mock if Stripe MCP unavailable
```

## Security Considerations

### OAuth Authentication (Stripe MCP)
- Stripe MCP uses OAuth for secure authorization
- Tokens are managed by MCP client (Claude Desktop, Cursor)
- No API keys stored in configuration files

### API Keys (Local Stripe MCP)
- Store in environment variables, never in code
- Use Stripe test keys for development
- Rotate keys regularly
- Restrict key permissions to minimum needed

### Payment Data
- **Never store** credit card numbers or CVVs
- Store only Stripe IDs (payment_intent_id, checkout_session_id)
- Use Stripe's PCI-compliant infrastructure
- Log payment events, not payment details

## Best Practices

### 1. Amount Validation
Always validate payment amounts match reservation pricing:

```python
# In AI prompt/logic
expected_amount = reservation_total_price * 100  # Convert to cents
if payment_amount != expected_amount:
    raise ValueError("Payment amount mismatch")
```

### 2. Idempotency
Use reservation ID as idempotency key:

```python
# Stripe MCP handles this
create_payment_link(
    amount=36000,
    description="RSV-20250601-ABC123",
    metadata={"reservation_id": "RSV-20250601-ABC123"}
)
```

### 3. Error Handling
Handle Stripe errors gracefully:

```
AI → Stripe: create_payment_link(...)
Stripe: Error - "Invalid amount"
AI: "I'm sorry, there was an issue creating the payment link. Let me try again..."
```

### 4. Currency Configuration
Configure default currency in StayHive config:

```yaml
# config.yaml
payment:
  currency: "usd"
  test_mode: true  # Use Stripe test mode
```

## Monitoring & Logging

### Events to Log
- Payment link created
- Payment succeeded/failed
- Refund issued
- Payment status checked

### Example Log Entry
```json
{
  "timestamp": "2025-10-17T16:30:00Z",
  "event": "payment_link_created",
  "reservation_id": "RSV-20250601-ABC123",
  "amount_cents": 36000,
  "stripe_payment_link_id": "plink_1234567890",
  "status": "pending"
}
```

## Future: BizHive MCP Gateway

When BizHive scales to multiple business modules, we'll build an **MCP Gateway**:

```
Claude Desktop
    └── BizHive MCP Gateway (Port 8080)
        ├── Routes /stayhive/* → StayHive Server
        ├── Routes /techhive/* → TechHive Server
        ├── Routes /stripe/* → Stripe MCP
        └── Routes /twilio/* → Twilio MCP (SMS/Voice)
```

**Gateway Benefits:**
- Single endpoint configuration
- Centralized authentication
- Unified logging and monitoring
- Load balancing
- Rate limiting across all services

**Timeline:**
- Phase 1 (Current): Multi-server configuration (StayHive + Stripe)
- Phase 2 (Q1 2026): Basic gateway for 3+ business modules
- Phase 3 (Q2 2026): Production gateway with full observability

## Troubleshooting

### Stripe MCP Not Showing Tools

**Problem:** AI doesn't see Stripe payment tools

**Solutions:**
1. Verify Stripe MCP is in `claude_desktop_config.json`
2. Restart Claude Desktop completely
3. Check Claude Desktop logs for connection errors
4. Verify OAuth authorization completed

### Payment Link Creation Fails

**Problem:** Stripe returns error when creating payment link

**Solutions:**
1. Check Stripe API key is valid (if using local MCP)
2. Verify amount is positive integer (cents)
3. Ensure description is not empty
4. Check Stripe account is active

### Mock Payment Instead of Real

**Problem:** Getting mock payment URLs instead of Stripe

**Solutions:**
1. Verify Stripe MCP is configured and connected
2. Check AI is calling Stripe MCP, not StayHive's generate_payment_link
3. Review MCP server logs

## Resources

- **Stripe MCP Documentation**: https://docs.stripe.com/mcp
- **Stripe Agent Toolkit**: https://github.com/stripe/agent-toolkit
- **MCP Specification**: https://modelcontextprotocol.io
- **BizHive Support**: support@bizhive.cloud

## Support

For Stripe payment integration issues:
1. Check Stripe Dashboard for payment events
2. Review Claude Desktop logs
3. Test with Stripe CLI: `stripe listen --forward-to localhost:8000/webhooks`
4. Contact BizHive support with reservation ID and error logs

---

**Summary:** BizHive uses Stripe's official MCP server for secure, maintained payment processing. This provides better security, less code to maintain, and automatic updates as Stripe adds features.
