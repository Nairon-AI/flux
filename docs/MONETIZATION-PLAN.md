# Flux Monetization Plan

> Comprehensive, research-backed strategy for making Flux a paid plugin with enforcement through AI agents

## Executive Summary

**Verdict: Yes, it's absolutely possible and enforceable.**

Based on research into Keygen.sh, Stripe Entitlements, Cursor's $1B ARR growth, and industry best practices for developer tool monetization, this plan outlines a foolproof approach.

### Key Principles (From Research)

1. **Gate by value, not arbitrary limits** - Developer tools succeed when free tiers enable viral adoption and premium tiers unlock enterprise features (SSO, compliance, advanced analysis)
2. **Server-side is truth** - Client-side validation is theater; all premium features must require API calls
3. **Convenience beats DRM** - Make paying easier than pirating; don't punish legitimate users
4. **Graceful degradation** - Never break workflows; just limit advanced features

---

## Part 1: Industry Research & Precedents

### Developer Tool Pricing Benchmarks (2025-2026)

| Tool | Free Tier | Pro Tier | Enterprise | Model |
|------|-----------|----------|------------|-------|
| **Cursor** | 2000 completions, 50 slow requests | $20/mo (500 fast requests) | $40/user/mo (SSO, admin) | Usage + features |
| **GitHub Copilot** | None | $10/mo individual | $19/user/mo (business) | Flat subscription |
| **Linear** | 250 issues | $8/user/mo | Custom | Seat-based |
| **Raycast** | Core features | $8/mo (AI, sync) | Teams pricing | Feature-gated |

### Key Insight: Cursor's GTM Strategy

Cursor hit $1B ARR in 24 months with:
- No sales team initially
- Free tier with real value (not crippled)
- Clear upgrade moment (hit request limits)
- Premium = more capacity + enterprise features

**Flux should mirror this**: Free tier handles 100% of task tracking, paid tier unlocks AI recommendations.

### Open Core vs Closed Source

Research recommends **Open Core** for developer tools:
- Core functionality: Open source (builds trust, enables contributions)
- Premium features: Closed/API-gated (generates revenue)

For Flux:
- **Open**: `fluxctl`, skills, hooks, task tracking, `.flux/` management
- **Closed**: Recommendation engine, analytics, cloud sync, team features

---

## Part 2: Architecture (Detailed)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User's Machine                                  │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────────┐ │
│  │   Claude Code   │───▶│                 Flux Plugin                      │ │
│  │  Cursor/Factory │    │  ┌─────────────┐  ┌─────────────┐               │ │
│  └─────────────────┘    │  │ fluxctl CLI │  │ Skills/*.md │               │ │
│                         │  └──────┬──────┘  └──────┬──────┘               │ │
│                         │         │                │                       │ │
│                         │  ┌──────▼────────────────▼──────┐               │ │
│                         │  │      license-check.py         │               │ │
│                         │  │  - Validates cached license   │               │ │
│                         │  │  - Checks entitlements        │               │ │
│                         │  │  - Gates premium features     │               │ │
│                         │  └──────────────┬───────────────┘               │ │
│                         │                 │                                │ │
│                         │  ┌──────────────▼───────────────┐               │ │
│                         │  │   ~/.flux/license.json       │               │ │
│                         │  │   - Encrypted + HMAC signed  │               │ │
│                         │  │   - Machine fingerprint      │               │ │
│                         │  │   - Cached entitlements      │               │ │
│                         │  └──────────────────────────────┘               │ │
│                         └─────────────────────────────────────────────────┘ │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │ HTTPS (TLS 1.3)
                    ┌───────────────────▼───────────────────┐
                    │         Flux License API              │
                    │         license.flux.dev              │
                    │                                       │
                    │  POST /validate     - Key validation  │
                    │  POST /activate     - Machine binding │
                    │  POST /check        - Periodic verify │
                    │  POST /deactivate   - Release machine │
                    │  GET  /entitlements - Feature flags   │
                    └───────────────────┬───────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
┌─────────▼─────────┐    ┌──────────────▼──────────────┐    ┌────────▼────────┐
│   Stripe Billing  │    │   PostgreSQL Database       │    │  Recommendations │
│                   │    │                             │    │  API (gated)     │
│ - Subscriptions   │───▶│  licenses                   │    │                  │
│ - Entitlements    │    │  activations                │    │  /improve        │
│ - Webhooks        │    │  usage_logs                 │    │  /analytics      │
│ - Customer Portal │    │  customers                  │    │  /sync           │
└───────────────────┘    └─────────────────────────────┘    └──────────────────┘
```

---

## Part 3: Tiered Feature Model

### Tier Design Principles

Based on developer tool research:
1. **Free tier must be genuinely useful** (not a demo)
2. **Upgrade moment should be clear** (hit a limit, need a feature)
3. **Enterprise features gate themselves** (SSO, compliance = org decision)

### Feature Matrix

| Feature | Free | Pro ($29/mo) | Team ($99/mo/5 seats) |
|---------|------|--------------|----------------------|
| **Task Tracking** | | | |
| `fluxctl` CLI | Unlimited | Unlimited | Unlimited |
| `/flux:plan` command | Unlimited | Unlimited | Unlimited |
| `/flux:work` command | Unlimited | Unlimited | Unlimited |
| Local `.flux/` state | Unlimited | Unlimited | Unlimited |
| **Skills & Hooks** | | | |
| All skill files | Yes | Yes | Yes |
| Pre-commit hooks | Yes | Yes | Yes |
| Ralph guard | Yes | Yes | Yes |
| **AI Recommendations** | | | |
| `/flux:improve` | 2 previews | Full analysis | Full analysis |
| Friction detection | No | Yes | Yes |
| Knowledge gap analysis | No | Yes | Yes |
| Custom recommendations | No | No | Yes |
| **Analytics** | | | |
| Local session logs | Yes | Yes | Yes |
| Aggregated insights | No | Yes | Team-wide |
| Export to dashboard | No | No | Yes |
| **Support** | | | |
| Community Discord | Yes | Yes | Yes |
| Priority support | No | Yes (48h SLA) | Yes (24h SLA) |
| Onboarding call | No | No | Yes |
| **Infrastructure** | | | |
| Cloud sync | No | No | Yes |
| SSO (SAML/OIDC) | No | No | Yes |
| Audit logs | No | No | Yes |
| Machine limit | 1 | 3 | Per seat |

### Pricing Justification

- **Pro at $29/mo**: Matches Cursor Pro ($20), slightly higher = perceived premium
- **Yearly discount**: $249/yr saves $99 (29% off) - standard SaaS discount
- **Team at $99/5 seats**: ~$20/seat, competitive with Linear ($8) + premium

---

## Part 4: License Key System

### Option A: Build Your Own (Recommended for Control)

#### Key Format
```
FLUX-{TIER}-{RANDOM_12}-{CHECKSUM_4}

Examples:
FLUX-PRO-A7K9X2M48B3C-F1D2
FLUX-TEAM-M2P5Q8R14D7E-A3B4
FLUX-TRIAL-X1Y2Z3A4B5C6-E7F8
```

#### Key Generation (TypeScript)

```typescript
// license-api/src/lib/keys.ts

import { createHmac, randomBytes } from 'crypto';

const HMAC_SECRET = process.env.LICENSE_HMAC_SECRET!;

interface LicenseKeyData {
  tier: 'trial' | 'pro' | 'team';
  email: string;
  seats?: number;
  expiresAt?: Date;
  stripeCustomerId?: string;
  stripeSubscriptionId?: string;
}

export function generateLicenseKey(tier: string): string {
  // Generate 12 random alphanumeric characters
  const random = randomBytes(6)
    .toString('hex')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '');
  
  const payload = `FLUX-${tier.toUpperCase()}-${random}`;
  
  // Generate HMAC checksum
  const checksum = createHmac('sha256', HMAC_SECRET)
    .update(payload)
    .digest('hex')
    .slice(0, 4)
    .toUpperCase();
  
  return `${payload}-${checksum}`;
}

export function verifyKeyFormat(key: string): boolean {
  const regex = /^FLUX-(TRIAL|PRO|TEAM)-[A-Z0-9]{12}-[A-Z0-9]{4}$/;
  return regex.test(key);
}

export function verifyKeyChecksum(key: string): boolean {
  const parts = key.split('-');
  if (parts.length !== 4) return false;
  
  const payload = parts.slice(0, 3).join('-');
  const providedChecksum = parts[3];
  
  const expectedChecksum = createHmac('sha256', HMAC_SECRET)
    .update(payload)
    .digest('hex')
    .slice(0, 4)
    .toUpperCase();
  
  return providedChecksum === expectedChecksum;
}
```

### Option B: Use Keygen.sh (Recommended for Speed)

Keygen.sh is an enterprise-grade licensing API that handles:
- Key generation & validation
- Machine fingerprinting
- Floating licenses
- Offline validation with signed certificates
- Entitlements system

```typescript
// Using Keygen.sh SDK
import { Keygen } from 'keygen-sh';

const keygen = new Keygen({
  account: process.env.KEYGEN_ACCOUNT_ID,
  product: process.env.KEYGEN_PRODUCT_ID,
});

// Validate license
const validation = await keygen.licenses.validate({
  key: licenseKey,
  fingerprint: machineId,
});

if (validation.valid) {
  // License is valid for this machine
  const entitlements = validation.license.entitlements;
  // Check if 'improve' feature is entitled
  if (entitlements.includes('flux-improve')) {
    // Allow full recommendations
  }
}
```

**Keygen.sh Pricing**: Free during development, ~$0.05/validation in production

### Recommendation

Start with **Option A (custom)** for full control and lower ongoing costs. Migrate to Keygen.sh if scaling challenges arise.

---

## Part 5: Machine Fingerprinting

### Why Fingerprint?

Prevents a single license key from being shared across unlimited machines.

### Fingerprint Generation (Python)

```python
# scripts/machine-fingerprint.py

import hashlib
import uuid
import platform
import subprocess
import os

def get_machine_fingerprint() -> str:
    """
    Generate a stable machine fingerprint from hardware identifiers.
    
    Components (in order of stability):
    1. MAC address (stable unless NIC replaced)
    2. CPU info (stable)
    3. Hostname (can change, but included for uniqueness)
    4. OS platform (stable)
    """
    components = []
    
    # MAC address
    mac = ':'.join([
        '{:02x}'.format((uuid.getnode() >> elements) & 0xff)
        for elements in range(0, 2*6, 2)
    ][::-1])
    components.append(f"mac:{mac}")
    
    # Platform
    components.append(f"platform:{platform.system()}")
    components.append(f"machine:{platform.machine()}")
    
    # CPU info (macOS)
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True
            )
            components.append(f"cpu:{result.stdout.strip()}")
        except:
            pass
    
    # Linux: use machine-id if available
    if platform.system() == "Linux":
        machine_id_path = "/etc/machine-id"
        if os.path.exists(machine_id_path):
            with open(machine_id_path) as f:
                components.append(f"machine_id:{f.read().strip()}")
    
    # Combine and hash
    combined = "|".join(sorted(components))
    fingerprint = hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    return fingerprint


def get_fingerprint_cached() -> str:
    """Get or create cached fingerprint."""
    cache_file = os.path.expanduser("~/.flux/.machine_id")
    
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return f.read().strip()
    
    fingerprint = get_machine_fingerprint()
    
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w") as f:
        f.write(fingerprint)
    
    return fingerprint
```

### Machine Activation Flow

```
1. User enters license key
2. Client generates machine fingerprint
3. POST /activate with { key, fingerprint }
4. Server checks:
   - Is key valid?
   - How many machines already activated?
   - Is this fingerprint already registered?
5. If under limit: Store activation, return success
6. If at limit: Return error with deactivation instructions
```

### Handling Hardware Changes

Users legitimately upgrade hardware. Handle with:

1. **Grace activations**: Allow 1 extra activation per year
2. **Self-service deactivation**: `/flux deactivate` releases current machine
3. **Support override**: Manual intervention for edge cases

---

## Part 6: Stripe Integration (Detailed)

### Stripe Resources to Create

```typescript
// stripe-setup.ts - Run once to configure Stripe

import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

async function setupStripeProducts() {
  // Create Flux product
  const product = await stripe.products.create({
    name: 'Flux',
    description: 'AI-native workflow optimization for developer agents',
  });

  // Create prices
  const proMonthly = await stripe.prices.create({
    product: product.id,
    unit_amount: 2900, // $29.00
    currency: 'usd',
    recurring: { interval: 'month' },
    metadata: { tier: 'pro' },
  });

  const proYearly = await stripe.prices.create({
    product: product.id,
    unit_amount: 24900, // $249.00
    currency: 'usd',
    recurring: { interval: 'year' },
    metadata: { tier: 'pro' },
  });

  const teamMonthly = await stripe.prices.create({
    product: product.id,
    unit_amount: 9900, // $99.00
    currency: 'usd',
    recurring: { interval: 'month' },
    metadata: { tier: 'team', seats: '5' },
  });

  // Create entitlements (Stripe Entitlements API)
  const features = [
    { name: 'flux-improve', lookup_key: 'flux-improve' },
    { name: 'flux-analytics', lookup_key: 'flux-analytics' },
    { name: 'flux-sync', lookup_key: 'flux-sync' },
    { name: 'flux-sso', lookup_key: 'flux-sso' },
  ];

  for (const feature of features) {
    await stripe.entitlements.features.create({
      name: feature.name,
      lookup_key: feature.lookup_key,
    });
  }

  console.log('Stripe setup complete');
  console.log({ product, proMonthly, proYearly, teamMonthly });
}
```

### Webhook Handler (Production-Grade)

```typescript
// license-api/src/routes/webhooks/stripe.ts

import Stripe from 'stripe';
import express from 'express';
import { db } from '../db';
import { generateLicenseKey } from '../lib/keys';
import { sendLicenseEmail, sendCancellationEmail } from '../lib/email';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

const router = express.Router();

// CRITICAL: Use raw body for signature verification
router.post(
  '/stripe',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const sig = req.headers['stripe-signature'] as string;

    let event: Stripe.Event;
    try {
      event = stripe.webhooks.constructEvent(req.body, sig, webhookSecret);
    } catch (err: any) {
      console.error('Webhook signature verification failed:', err.message);
      return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    try {
      switch (event.type) {
        // New subscription created
        case 'checkout.session.completed': {
          const session = event.data.object as Stripe.Checkout.Session;
          
          if (session.mode !== 'subscription') break;
          
          const tier = session.metadata?.tier || 'pro';
          const email = session.customer_email!;
          const customerId = session.customer as string;
          const subscriptionId = session.subscription as string;

          // Generate license key
          const key = generateLicenseKey(tier);

          // Store in database
          await db.license.create({
            data: {
              key,
              tier,
              email,
              stripeCustomerId: customerId,
              stripeSubscriptionId: subscriptionId,
              status: 'active',
              maxMachines: tier === 'team' ? 25 : 3,
              createdAt: new Date(),
            },
          });

          // Send welcome email with license key
          await sendLicenseEmail({
            to: email,
            key,
            tier,
            portalUrl: `https://flux.dev/portal?customer=${customerId}`,
          });

          console.log(`License created: ${key} for ${email}`);
          break;
        }

        // Subscription renewed (payment succeeded)
        case 'invoice.payment_succeeded': {
          const invoice = event.data.object as Stripe.Invoice;
          
          if (!invoice.subscription) break;
          
          // Update license expiry
          await db.license.updateMany({
            where: { stripeSubscriptionId: invoice.subscription as string },
            data: {
              status: 'active',
              lastPaymentAt: new Date(),
            },
          });
          break;
        }

        // Payment failed
        case 'invoice.payment_failed': {
          const invoice = event.data.object as Stripe.Invoice;
          
          if (!invoice.subscription) break;
          
          const license = await db.license.findFirst({
            where: { stripeSubscriptionId: invoice.subscription as string },
          });

          if (license) {
            // Mark as past_due but don't revoke immediately
            await db.license.update({
              where: { id: license.id },
              data: { status: 'past_due' },
            });

            // Stripe handles retry logic; we just track status
            console.log(`Payment failed for license: ${license.key}`);
          }
          break;
        }

        // Subscription cancelled
        case 'customer.subscription.deleted': {
          const subscription = event.data.object as Stripe.Subscription;

          const license = await db.license.findFirst({
            where: { stripeSubscriptionId: subscription.id },
          });

          if (license) {
            // Revoke license
            await db.license.update({
              where: { id: license.id },
              data: {
                status: 'cancelled',
                revokedAt: new Date(),
              },
            });

            // Deactivate all machines
            await db.activation.deleteMany({
              where: { licenseId: license.id },
            });

            // Send cancellation email
            await sendCancellationEmail({
              to: license.email,
              reactivateUrl: 'https://flux.dev/pricing',
            });

            console.log(`License revoked: ${license.key}`);
          }
          break;
        }

        // Subscription updated (plan change)
        case 'customer.subscription.updated': {
          const subscription = event.data.object as Stripe.Subscription;
          const previousAttributes = event.data
            .previous_attributes as Partial<Stripe.Subscription>;

          // Check if plan changed
          if (previousAttributes.items) {
            const newPriceId = subscription.items.data[0]?.price.id;
            const price = await stripe.prices.retrieve(newPriceId);
            const newTier = price.metadata?.tier || 'pro';

            await db.license.updateMany({
              where: { stripeSubscriptionId: subscription.id },
              data: {
                tier: newTier,
                maxMachines: newTier === 'team' ? 25 : 3,
              },
            });

            console.log(`License upgraded to: ${newTier}`);
          }
          break;
        }

        default:
          console.log(`Unhandled event type: ${event.type}`);
      }

      res.json({ received: true });
    } catch (err: any) {
      console.error('Webhook processing error:', err);
      // Return 200 anyway to prevent Stripe retries for our bugs
      // Log error for investigation
      res.json({ received: true, error: err.message });
    }
  }
);

export default router;
```

### Using Stripe Entitlements for Feature Flags

Stripe Entitlements automatically sync with subscriptions:

```typescript
// Check entitlements for a customer
async function checkEntitlement(
  customerId: string,
  feature: string
): Promise<boolean> {
  const entitlements = await stripe.entitlements.activeEntitlements.list({
    customer: customerId,
  });

  return entitlements.data.some(
    (e) => e.feature.lookup_key === feature
  );
}

// In your API route
app.get('/api/improve', async (req, res) => {
  const license = await validateLicense(req.headers.authorization);
  
  if (!license) {
    return res.status(401).json({ error: 'Invalid license' });
  }

  // Check if entitled to 'flux-improve' feature
  const canImprove = await checkEntitlement(
    license.stripeCustomerId,
    'flux-improve'
  );

  if (!canImprove) {
    return res.status(403).json({
      error: 'Feature not available on your plan',
      upgrade_url: 'https://flux.dev/upgrade',
    });
  }

  // Process improvement request...
});
```

---

## Part 7: Client-Side License Validation

### License Check Script (Python)

```python
#!/usr/bin/env python3
"""
Flux License Checker

Validates license status and caches entitlements locally.
Called before premium features in skills.
"""

import json
import os
import sys
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

# Configuration
LICENSE_API = os.environ.get("FLUX_LICENSE_API", "https://license.flux.dev")
CACHE_TTL_HOURS = 24
OFFLINE_GRACE_DAYS = 7
HMAC_SECRET = os.environ.get("FLUX_HMAC_SECRET", "")  # Set during install

# Paths
FLUX_DIR = Path.home() / ".flux"
LICENSE_FILE = FLUX_DIR / "license.json"
MACHINE_ID_FILE = FLUX_DIR / ".machine_id"


def get_machine_fingerprint() -> str:
    """Get or create machine fingerprint."""
    if MACHINE_ID_FILE.exists():
        return MACHINE_ID_FILE.read_text().strip()
    
    # Generate fingerprint (simplified for example)
    import uuid
    import platform
    
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> e) & 0xff) 
                    for e in range(0, 12, 2)][::-1])
    raw = f"{mac}|{platform.node()}|{platform.system()}"
    fingerprint = hashlib.sha256(raw.encode()).hexdigest()[:32]
    
    MACHINE_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    MACHINE_ID_FILE.write_text(fingerprint)
    
    return fingerprint


def verify_license_signature(data: dict) -> bool:
    """Verify HMAC signature on cached license."""
    if not HMAC_SECRET:
        return True  # Skip if not configured
    
    signature = data.pop("_signature", None)
    if not signature:
        return False
    
    payload = json.dumps(data, sort_keys=True)
    expected = hmac.new(
        HMAC_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)


def load_cached_license() -> dict | None:
    """Load and verify cached license."""
    if not LICENSE_FILE.exists():
        return None
    
    try:
        data = json.loads(LICENSE_FILE.read_text())
        
        # Verify signature
        if not verify_license_signature(data.copy()):
            print("Warning: License file signature invalid", file=sys.stderr)
            return None
        
        return data
    except Exception as e:
        print(f"Warning: Failed to load license: {e}", file=sys.stderr)
        return None


def save_license(data: dict):
    """Save license with HMAC signature."""
    # Add signature
    if HMAC_SECRET:
        payload = json.dumps(data, sort_keys=True)
        data["_signature"] = hmac.new(
            HMAC_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    LICENSE_FILE.write_text(json.dumps(data, indent=2))


def validate_online(key: str, fingerprint: str) -> dict | None:
    """Validate license against API."""
    try:
        req = Request(
            f"{LICENSE_API}/validate",
            data=json.dumps({
                "key": key,
                "fingerprint": fingerprint,
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except URLError as e:
        print(f"Warning: License API unreachable: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Warning: Validation failed: {e}", file=sys.stderr)
        return None


def needs_revalidation(cached: dict) -> bool:
    """Check if cached license needs revalidation."""
    last_check = cached.get("last_validated")
    if not last_check:
        return True
    
    try:
        last_dt = datetime.fromisoformat(last_check)
        return datetime.now() - last_dt > timedelta(hours=CACHE_TTL_HOURS)
    except:
        return True


def is_within_grace_period(cached: dict) -> bool:
    """Check if within offline grace period."""
    last_check = cached.get("last_validated")
    if not last_check:
        return False
    
    try:
        last_dt = datetime.fromisoformat(last_check)
        return datetime.now() - last_dt < timedelta(days=OFFLINE_GRACE_DAYS)
    except:
        return False


def check_license() -> dict:
    """
    Main license check function.
    
    Returns:
        {
            "valid": bool,
            "tier": "free" | "pro" | "team",
            "features": ["improve", "analytics", ...],
            "message": str | None,
            "upgrade_url": str | None,
        }
    """
    FREE_RESULT = {
        "valid": True,
        "tier": "free",
        "features": [],
        "message": None,
        "upgrade_url": "https://flux.dev/upgrade",
    }
    
    # Load cached license
    cached = load_cached_license()
    
    if not cached or not cached.get("key"):
        return FREE_RESULT
    
    key = cached["key"]
    fingerprint = get_machine_fingerprint()
    
    # Check if revalidation needed
    if needs_revalidation(cached):
        online_result = validate_online(key, fingerprint)
        
        if online_result:
            if online_result.get("valid"):
                # Update cache
                cached.update({
                    "tier": online_result["tier"],
                    "features": online_result.get("features", []),
                    "email": online_result.get("email"),
                    "expires_at": online_result.get("expires_at"),
                    "last_validated": datetime.now().isoformat(),
                })
                save_license(cached)
            else:
                # License invalid (revoked, expired, etc.)
                print(f"License invalid: {online_result.get('error')}", file=sys.stderr)
                LICENSE_FILE.unlink(missing_ok=True)
                return FREE_RESULT
        else:
            # Offline - check grace period
            if not is_within_grace_period(cached):
                print("Offline grace period expired", file=sys.stderr)
                return FREE_RESULT
            # Within grace period - use cached
    
    return {
        "valid": True,
        "tier": cached.get("tier", "free"),
        "features": cached.get("features", []),
        "message": None,
        "upgrade_url": None,
    }


def require_feature(feature: str) -> bool:
    """
    Check if a feature is available.
    
    Usage in skills:
        if not require_feature("improve"):
            print("Upgrade to Pro for AI recommendations")
            sys.exit(1)
    """
    result = check_license()
    return feature in result.get("features", [])


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Flux license")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--require", type=str, help="Require specific feature")
    args = parser.parse_args()
    
    if args.require:
        if require_feature(args.require):
            sys.exit(0)
        else:
            print(f"Feature '{args.require}' requires upgrade", file=sys.stderr)
            print("Upgrade at: https://flux.dev/upgrade", file=sys.stderr)
            sys.exit(1)
    
    result = check_license()
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Tier: {result['tier']}")
        print(f"Features: {', '.join(result['features']) or 'None'}")
        if result.get("upgrade_url"):
            print(f"Upgrade: {result['upgrade_url']}")
```

### Integration with Skills

```markdown
<!-- skills/flux-improve/SKILL.md -->

## Prerequisites

Before running /flux:improve analysis:

1. Check license status:
   ```bash
   python3 ~/.flux/scripts/license-check.py --require improve
   ```

2. If exit code != 0, show:
   ```
   AI-powered recommendations require Flux Pro.
   
   Free users get 2 preview recommendations per analysis.
   Upgrade for full analysis: https://flux.dev/upgrade
   ```

3. If licensed, proceed with full analysis.
```

---

## Part 8: Security Hardening

### Threat Model

| Threat | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Key sharing | High | Medium | Machine fingerprinting, concurrent limits |
| Key guessing | Low | High | Cryptographic checksums, rate limiting |
| Cache tampering | Medium | Medium | HMAC signatures on license.json |
| API replay | Low | Low | Nonce + timestamp in requests |
| MITM attack | Low | High | TLS 1.3, certificate pinning (optional) |
| Code modification | Medium | High | API-gated features (can't fake API response) |
| Offline bypass | Medium | Medium | Grace periods, periodic phone-home |

### Security Implementations

#### 1. Rate Limiting on License API

```typescript
// Using express-rate-limit
import rateLimit from 'express-rate-limit';

const validateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window per IP
  message: { error: 'Too many validation requests' },
  standardHeaders: true,
});

app.post('/validate', validateLimiter, validateHandler);
```

#### 2. Anomaly Detection

```typescript
// Track validation patterns
async function checkForAnomalies(key: string, fingerprint: string, ip: string) {
  const recentActivations = await db.activation.count({
    where: {
      licenseId: (await db.license.findUnique({ where: { key } }))?.id,
      createdAt: { gte: new Date(Date.now() - 24 * 60 * 60 * 1000) },
    },
  });

  // Flag if >10 new machines in 24h
  if (recentActivations > 10) {
    await alertAdmin({
      type: 'anomaly',
      key,
      message: `${recentActivations} activations in 24h`,
    });
  }
}
```

#### 3. Signed License Responses

```typescript
// Server signs license response
import { createSign } from 'crypto';

function signLicenseResponse(data: object): string {
  const sign = createSign('RSA-SHA256');
  sign.update(JSON.stringify(data));
  return sign.sign(PRIVATE_KEY, 'base64');
}

// Client verifies signature
import { createVerify } from 'crypto';

function verifyLicenseResponse(data: object, signature: string): boolean {
  const verify = createVerify('RSA-SHA256');
  verify.update(JSON.stringify(data));
  return verify.verify(PUBLIC_KEY, signature, 'base64');
}
```

### What You CAN'T Prevent (And Why It's OK)

1. **Determined hackers forking and removing checks**: Legal protection (license terms), feature drift (they don't get updates), no support
2. **Offline-only users**: Grace periods handle legitimate cases; long-term offline = edge case not worth engineering for
3. **VM cloning**: Machine fingerprint changes slightly; treat as new machine

**Philosophy**: Make the legitimate path easier than piracy. Support, updates, and convenience are the real moat.

---

## Part 9: Database Schema

```sql
-- PostgreSQL schema for license management

CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  stripe_customer_id VARCHAR(255) UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE licenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key VARCHAR(64) UNIQUE NOT NULL,
  customer_id UUID REFERENCES customers(id),
  tier VARCHAR(20) NOT NULL CHECK (tier IN ('trial', 'pro', 'team')),
  status VARCHAR(20) NOT NULL DEFAULT 'active' 
    CHECK (status IN ('active', 'past_due', 'cancelled', 'expired')),
  max_machines INT NOT NULL DEFAULT 3,
  stripe_subscription_id VARCHAR(255),
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  revoked_at TIMESTAMPTZ,
  
  INDEX idx_licenses_key (key),
  INDEX idx_licenses_stripe_sub (stripe_subscription_id)
);

CREATE TABLE activations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  license_id UUID REFERENCES licenses(id) ON DELETE CASCADE,
  fingerprint VARCHAR(64) NOT NULL,
  hostname VARCHAR(255),
  platform VARCHAR(50),
  activated_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(license_id, fingerprint),
  INDEX idx_activations_fingerprint (fingerprint)
);

CREATE TABLE validation_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  license_id UUID REFERENCES licenses(id),
  fingerprint VARCHAR(64),
  ip_address INET,
  result VARCHAR(20) NOT NULL,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  INDEX idx_validation_logs_license (license_id, created_at)
);

-- Automatic updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER customers_updated_at
  BEFORE UPDATE ON customers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## Part 10: Implementation Phases

### Phase 1: License Infrastructure (Week 1-2)

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Set up license API (Railway/Vercel) | P0 | 4h | Backend |
| Create database schema | P0 | 2h | Backend |
| Implement key generation | P0 | 2h | Backend |
| Implement validation endpoints | P0 | 4h | Backend |
| Add machine fingerprinting | P1 | 3h | Backend |
| Set up Stripe products/prices | P0 | 2h | Backend |
| Implement webhook handler | P0 | 4h | Backend |
| Create email templates | P1 | 2h | Design |

### Phase 2: Client Integration (Week 2-3)

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Create `license-check.py` | P0 | 4h | Backend |
| Modify `install-plugin.sh` | P0 | 2h | Backend |
| Gate `match-recommendations.py` | P0 | 3h | Backend |
| Update skill files with license checks | P1 | 2h | Backend |
| Add `flux license` CLI commands | P1 | 3h | Backend |
| Test offline scenarios | P0 | 2h | QA |

### Phase 3: Pricing & Portal (Week 3)

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Create `/pricing` page | P0 | 4h | Frontend |
| Implement Stripe Checkout flow | P0 | 3h | Frontend |
| Build customer portal (view license, manage machines) | P1 | 6h | Full-stack |
| Add upgrade prompts to CLI output | P1 | 2h | Backend |

### Phase 4: Launch (Week 4)

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Migrate existing users to free tier | P0 | 2h | Backend |
| Send announcement email | P0 | 2h | Marketing |
| Monitor for issues | P0 | Ongoing | All |
| Set up alerting for anomalies | P1 | 2h | Backend |

---

## Part 11: Operational Runbooks

### Runbook: License Key Not Working

```
1. Check key format: FLUX-{TIER}-{12 chars}-{4 chars}
2. Verify in database: SELECT * FROM licenses WHERE key = ?
3. Check status: active, past_due, cancelled, expired
4. Check activations: SELECT COUNT(*) FROM activations WHERE license_id = ?
5. If at machine limit: Guide user to deactivate old machine
6. If subscription issue: Check Stripe dashboard
7. If all else fails: Generate new key, revoke old
```

### Runbook: Suspected Key Sharing

```
1. Query recent activations:
   SELECT fingerprint, activated_at, hostname 
   FROM activations 
   WHERE license_id = ? 
   ORDER BY activated_at DESC;

2. If >3 unique fingerprints in 24h:
   - Email customer about suspicious activity
   - Do NOT auto-revoke (could be legitimate)

3. If >10 unique fingerprints in 7 days:
   - Flag for manual review
   - Consider reaching out

4. Document in validation_logs for patterns
```

### Runbook: Stripe Webhook Failure

```
1. Check Stripe Dashboard > Developers > Webhooks
2. Look for failed deliveries
3. Check server logs for errors
4. Common issues:
   - Raw body parsing (must use express.raw())
   - Signature verification (check webhook secret)
   - Database transaction failures

5. Replay failed events from Stripe dashboard
```

---

## Part 12: Legal & Compliance

### License Agreement (Key Points)

```
FLUX SOFTWARE LICENSE AGREEMENT

1. GRANT OF LICENSE
   - Pro: 1 user, up to 3 machines
   - Team: Up to 5 users, up to 25 machines total

2. RESTRICTIONS
   - No sharing of license keys
   - No circumvention of license checks
   - No reverse engineering of license system

3. TERMINATION
   - Automatic on subscription cancellation
   - Immediate on breach of terms

4. REFUNDS
   - 14-day money-back guarantee
   - Pro-rated refunds for annual plans if cancelled within 30 days
```

### GDPR Compliance

- Store minimal PII (email, license key)
- Provide data export on request
- Delete data within 30 days of request
- Machine fingerprints are hashed (not raw hardware IDs)

---

## Part 13: Open Questions (Decisions Needed)

| Question | Options | Recommendation |
|----------|---------|----------------|
| Keygen.sh vs custom? | Keygen = faster, Custom = cheaper long-term | Start custom, migrate if needed |
| Grace period length? | 3, 7, or 14 days | 7 days (standard) |
| Machine limit for Pro? | 2, 3, or 5 | 3 (Cursor does 1, we're generous) |
| Free tier recommendations? | 0, 2, or 5 previews | 2 previews (teaser) |
| Trial length? | 7, 14, or 30 days | 14 days (standard) |
| Grandfathering? | Discount, free tier, or nothing | 50% discount for 1 year |
| Open source core? | MIT, Apache, or proprietary | Apache 2.0 for CLI, proprietary API |

---

## Part 14: Success Metrics

### Launch Metrics (First 90 Days)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Free → Pro conversion | 5% | Stripe / total installs |
| Churn rate | <5%/month | Cancelled / active |
| License validation success rate | >99.5% | API logs |
| Support tickets about licensing | <5/week | Helpdesk |
| Anomaly alerts | <10/week | Monitoring |

### Revenue Milestones

| Milestone | Timeline | Notes |
|-----------|----------|-------|
| First paying customer | Week 1 | Founder-led sales if needed |
| $1k MRR | Month 2 | ~35 Pro subscribers |
| $5k MRR | Month 4 | ~175 Pro subscribers |
| $10k MRR | Month 6 | Mix of Pro + Team |

---

## Conclusion

This plan is **technically foolproof** because:

1. **Premium features require API calls** - Can't fake recommendations from a server you don't control
2. **Multiple enforcement layers** - Install check, runtime check, feature check
3. **Graceful degradation** - Free tier works fully; only premium gates
4. **Industry-standard stack** - Stripe, PostgreSQL, standard webhooks
5. **Security in depth** - Fingerprinting, signing, rate limiting, anomaly detection

The **business risk** is not technical enforcement; it's:
- Pricing the tiers correctly
- Making the free tier valuable enough for adoption
- Making the paid tier valuable enough for conversion

**Recommended first step**: Implement Phase 1 (license API + Stripe integration) as a proof of concept before building client-side integration. Validate the flow with 5-10 manual testers.
