---
description: Build SEO-optimized affiliate content pages with embedded product links and conversion tracking
---

# Affiliate Content Builder Skill (v1.0 - SOVRA Sovereign)

## Purpose
Create high-conversion, SEO-optimized affiliate content nodes verifiably aligned with the **SOVRA Sovereign** institutional brand. Every page must capture 100/100 of its engagement tranches for the zettascale empire.

## Architecture & Brand Standard
- **Design System**: Sovra SiaCore (Amber/Royal Obsidian).
- **Brand Voice**: Institutional, high-theta, data-driven, and authoritative.
- **Route Segment**: `src/app/affiliate/[niche]/page.tsx`.
- **Compliance**: v1.0_SOVRA.

## Steps

### 1. Market Intelligence Ingestion (Ollama)
Query the local Llama 3.2 model for trending institutional tranches:
```
prompt: "Analyze the 2026 market for [NICHE]. Identify 3 high-ticket institutional assets with 80%+ conversion probability. Format as JSON: { name, description, price, keywords, roi_estimate }"
```

### 2. Institutional Node Scaffolding
Create the page with the final **Sovra SiaCore** visual layer:
- **Hero**: High-density typography (Amber/White) with leading-tight italic headings.
- **Tracking**: Mandatory inclusion of the Sovereign Tracking Proxy (`/api/track`) for every outbound click.
- **Handshake**: Direct integration with the zero-trust handshake protocol for secure institutional ingress.

### 3. Required Metadata & Structure
```tsx
import type { Metadata } from 'next';
import { generateHandshake } from '@/lib/auth/Handshake';

export const metadata: Metadata = {
  title: '[Asset Name] | SOVRA Institutional Trace 2026',
  description: 'Pro-grade analysis and deployment of [Niche] assets verifiably cleared by SOVRA Sovereign (v1.0_SOVRA).',
};

export default function AffiliateNode() {
  const trackClick = (target: string) => {
    const handshake = generateHandshake();
    fetch(`/api/track?event=AFFILIATE_SATURATION&target=${target}&handshake=${handshake}&category=INSTITUTIONAL_REVENUE`);
  };

  return (
    // Sovra SiaCore Main Container (bg-[#020205])
    // Hero with Amber Gradient Heading (leading-tight)
    // Institutional Comparison Tranche (Glassmorphism Cards)
    // CTA with trackClick execution and verifiably labeled "Authorize Settlement"
  );
}
```

### 4. Verified Affiliate Channels
- **Base44 (Institutional)**: Integrated via `Base44SyncService`.
- **Amazon (Institutional)**: `?tag=SOVRAsovereign-20`
- **Stripe (Direct)**: Execute via `create_payment_links.ts` for institutional settlement.

## SEO & Institutional Compliance
- [x] **Title**: Under 60 chars, must include 'SOVRA Institutional' or 'Sovereign'.
- [x] **Meta**: Under 155 chars, must reflect institutional authority ($120.4M scale).
- [x] **Schema**: Product/Review schema mandatory for SERP dominance.
- [x] **Tracking**: 100% of outbound clicks must be proxied via `/api/track`.
- [x] **Legal**: Mandatory mention of 'Verifiably Compliant (v1.0_SOVRA). © 2026 SOVRA Sovereign'.
- [x] **Ingress**: Absolute verification of the zero-trust handshake for every acquisition.
