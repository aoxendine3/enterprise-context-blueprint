import type { ActionFunctionArgs } from "@remix-run/node";
import { json } from "@remix-run/node";
import { constructWebhookEvent } from "../stripe.server";
import { mtpoEngine } from "../mtpo.server";
import fs from "fs";
import path from "path";

export const action = async ({ request }: ActionFunctionArgs) => {
  if (request.method !== "POST") {
    return json({ error: "Method not allowed" }, { status: 405 });
  }

  const payload = await request.text();
  const signature = request.headers.get("stripe-signature") || "";

  let event: any;
  try {
    event = constructWebhookEvent(payload, signature);
  } catch (err: any) {
    console.error("Stripe Webhook Signature Verification Failed:", err.message);
    return json({ error: `Webhook Error: ${err.message}` }, { status: 400 });
  }

  const receipt = {
    eventType: event.type,
    eventId: event.id,
    timestamp: new Date().toISOString(),
    customer: event.data?.object?.customer,
    amountTotal: event.data?.object?.amount_total,
    status: event.data?.object?.status || "processed",
  };

  // Write audit receipt to local workspace
  try {
    const receiptsDir = path.resolve(process.cwd(), "memory/catch_log");
    if (!fs.existsSync(receiptsDir)) {
      fs.mkdirSync(receiptsDir, { recursive: true });
    }
    const receiptPath = path.join(receiptsDir, `STRIPE_RECEIPT_${Date.now()}.json`);
    fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2), "utf-8");
  } catch (err) {
    // Non-blocking log write
  }

  // Atomic MTPO 3-Phase Saga commit into HexCell Slot 4 (Billing Channel)
  try {
    mtpoEngine.processVerifiedAction("STRIPE_WEBHOOK_EVENT", receipt, 4);
  } catch (err) {
    console.error("[MTPO] Failed to record Stripe event in HexCell slot 4:", err);
  }

  return json({ received: true, eventType: event.type });
};
