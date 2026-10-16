/**
 * Sovereign Stripe Server Integration
 * Handles subscriptions, checkout sessions, and webhook processing
 * for the 22-Agent Sovereign Swarm monetization pipeline.
 */

import Stripe from "stripe";

const stripeSecretKey = process.env.STRIPE_SECRET_KEY || "sk_test_placeholder_sovereign_key";
const stripeWebhookSecret = process.env.STRIPE_WEBHOOK_SECRET || "whsec_placeholder";

export const stripe = new Stripe(stripeSecretKey, {
  apiVersion: "2025-01-27.acacia" as any,
  typescript: true,
});

export interface SubscriptionPlan {
  id: string;
  name: string;
  priceMonthly: number;
  description: string;
  features: string[];
  stripePriceId?: string;
  badgeTone?: "info" | "success" | "attention";
}

export const SOVEREIGN_PLANS: Record<string, SubscriptionPlan> = {
  sentinel: {
    id: "sentinel",
    name: "Sentinel Tier",
    priceMonthly: 299,
    description: "Automated agentic SAST scanning, AST invariant audits, and weekly security health reports.",
    features: [
      "100 Automated AST Scans / month",
      "Memory Safety & Invariant Falsification",
      "Standard CVSS 3.1 Vulnerability Reports",
      "Email & Webhook Notifications",
    ],
    badgeTone: "info",
  },
  sovereign_enterprise: {
    id: "sovereign_enterprise",
    name: "Sovereign Enterprise Tier",
    priceMonthly: 1499,
    description: "Full Lead 9 Council autonomous audit, Z3 formal SMT proofs, deterministic PoC generation, and zero-gap audio alerts.",
    features: [
      "Unlimited Autonomous Scans",
      "Full Z3 SMT Formal Logic Proofs",
      "Deterministic Playwright PoC Reproduction",
      "Kokoro Zero-Gap Live Audio Council Alerts",
      "Direct API Integration for HackerOne & Bugcrowd",
      "Priority 24/7 Swarm Self-Healing",
    ],
    badgeTone: "success",
  },
  bounty_retainer: {
    id: "bounty_retainer",
    name: "Bounty Hunter Retainer",
    priceMonthly: 4999,
    description: "Dedicated 16,000 MTPO node allocation with direct HackerOne/Bugcrowd bounty hunting and revenue sharing.",
    features: [
      "Dedicated 16,000 MTPO Swarm Node Cluster",
      "Autonomous 24/7 Zero-Day Hunting",
      "Turnkey PoC & Patch Delivery for Triage Fast-Track",
      "White-Glove Direct Council Audio Channel",
      "Custom SMT Solver Rules for Proprietary Smart Contracts",
    ],
    badgeTone: "attention",
  },
};

export async function createCheckoutSession({
  planId,
  customerEmail,
  returnUrl,
}: {
  planId: string;
  customerEmail?: string;
  returnUrl: string;
}) {
  const plan = SOVEREIGN_PLANS[planId];
  if (!plan) {
    throw new Error(`Invalid plan ID: ${planId}`);
  }

  // If using placeholder key in development/testing, return mock session URL
  if (stripeSecretKey.startsWith("sk_test_placeholder")) {
    return {
      id: `cs_mock_${Date.now()}`,
      url: `${returnUrl}?session_id=cs_mock_${Date.now()}&status=success&plan=${planId}`,
      isMock: true,
    };
  }

  const session = await stripe.checkout.sessions.create({
    payment_method_types: ["card"],
    mode: "subscription",
    customer_email: customerEmail,
    line_items: [
      {
        price_data: {
          currency: "usd",
          product_data: {
            name: `Sovereign Security - ${plan.name}`,
            description: plan.description,
          },
          unit_amount: plan.priceMonthly * 100,
          recurring: {
            interval: "month",
          },
        },
        quantity: 1,
      },
    ],
    success_url: `${returnUrl}?session_id={CHECKOUT_SESSION_ID}&status=success&plan=${planId}`,
    cancel_url: `${returnUrl}?status=cancelled`,
    metadata: {
      planId: plan.id,
      director: "Anthony",
      swarm: "22-Agent Collective",
    },
  });

  return {
    id: session.id,
    url: session.url,
    isMock: false,
  };
}

export function constructWebhookEvent(payload: string | Buffer, signature: string) {
  if (stripeWebhookSecret === "whsec_placeholder") {
    return JSON.parse(payload.toString());
  }
  return stripe.webhooks.constructEvent(payload, signature, stripeWebhookSecret);
}
