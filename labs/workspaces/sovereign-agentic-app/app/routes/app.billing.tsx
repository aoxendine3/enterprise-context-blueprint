import { useState } from "react";
import type { ActionFunctionArgs, LoaderFunctionArgs } from "@remix-run/node";
import { json, redirect } from "@remix-run/node";
import { useLoaderData, useFetcher } from "@remix-run/react";
import {
  Page,
  Layout,
  Card,
  Text,
  Badge,
  Button,
  BlockStack,
  InlineStack,
  Box,
  Divider,
  List,
  Banner,
  Link,
} from "@shopify/polaris";
import { TitleBar, useAppBridge } from "@shopify/app-bridge-react";
import { authenticate } from "../shopify.server";
import { SOVEREIGN_PLANS, LIVE_STRIPE_CONFIG, createCheckoutSession } from "../stripe.server";

export const loader = async ({ request }: LoaderFunctionArgs) => {
  await authenticate.admin(request);
  const url = new URL(request.url);
  const status = url.searchParams.get("status");
  const planId = url.searchParams.get("plan");
  const invoiceId = url.searchParams.get("invoice_id");
  const amount = url.searchParams.get("amount");

  return json({
    plans: Object.values(SOVEREIGN_PLANS),
    liveConfig: LIVE_STRIPE_CONFIG,
    invoiceNotification: status === "invoice_generated" && invoiceId ? {
      invoiceId,
      planId: planId || "sentinel",
      amount: amount || "299",
      date: new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }),
    } : null,
    currentSubscription: status === "success" ? {
      planId: planId || "sovereign_enterprise",
      status: "ACTIVE",
      renewDate: "2026-11-16",
    } : null,
  });
};

export const action = async ({ request }: ActionFunctionArgs) => {
  await authenticate.admin(request);
  const formData = await request.formData();
  const planId = formData.get("planId") as string;
  const url = new URL(request.url);

  try {
    const session = await createCheckoutSession({
      planId,
      returnUrl: `${url.origin}/app/billing`,
    });

    if (session.url) {
      return redirect(session.url);
    }

    return json({ success: true, session });
  } catch (error: any) {
    return json({ success: false, error: error.message }, { status: 400 });
  }
};

export default function Billing() {
  const { plans, liveConfig, invoiceNotification, currentSubscription } = useLoaderData<typeof loader>();
  const fetcher = useFetcher();
  const shopify = useAppBridge();

  const handleOrderPlan = (planId: string, amount: number) => {
    shopify.toast.show(`Processing order for ${planId} ($${amount}/mo)...`);
    fetcher.submit({ planId }, { method: "POST" });
  };

  return (
    <Page fullWidth>
      <TitleBar title="Code Security Services & Project Sponsorship" />

      <BlockStack gap="500">
        {/* Transparent Overview Header */}
        <Banner
          title="Security Verification & Development Support"
          tone="info"
        >
          <Text as="p" variant="bodyMd">
            Our mission is to help developers and merchants identify logic flaws, prevent race conditions, and build
            secure applications. We offer standard commercial security auditing packages alongside direct community
            sponsorship channels to keep our open-source tools continuously tested and maintained.
          </Text>
        </Banner>

        {/* Invoice Confirmation Banner */}
        {invoiceNotification && (
          <Banner title={`Invoice & Order Confirmation: ${invoiceNotification.invoiceId}`} tone="success">
            <BlockStack gap="200">
              <Text as="p" variant="bodyMd">
                Thank you for selecting the <strong>{invoiceNotification.planId.toUpperCase()}</strong> package ($
                {invoiceNotification.amount}/month). Your formal service order has been generated under reference{" "}
                <code>{invoiceNotification.invoiceId}</code>.
              </Text>
              <Text as="p" variant="bodySm" tone="subdued">
                An onboarding engineer will confirm your repository scope within 1 business day. Payment can be settled
                via direct Stripe invoice, corporate ACH, or corporate card.
              </Text>
            </BlockStack>
          </Banner>
        )}

        {/* Active Subscription Banner */}
        {currentSubscription && (
          <Banner title="Subscription Active" tone="success">
            <Text as="p" variant="bodyMd">
              Your service is active on <strong>{currentSubscription.planId.toUpperCase()}</strong>. Scheduled renewal:{" "}
              {currentSubscription.renewDate}.
            </Text>
          </Banner>
        )}

        <Layout>
          {/* Main Pricing Cards */}
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <InlineStack align="space-between">
                  <BlockStack gap="100">
                    <Text as="h2" variant="headingMd">
                      Commercial Code Security Packages
                    </Text>
                    <Text as="p" variant="bodySm" tone="subdued">
                      Formal verification, automated AST auditing, and human-verified remediation patches.
                    </Text>
                  </BlockStack>
                  <Badge tone="success">Verified Service Tiers</Badge>
                </InlineStack>
                <Divider />

                <InlineStack gap="400" wrap align="space-between">
                  {plans.map((plan) => (
                    <Box
                      key={plan.id}
                      padding="500"
                      background="bg-surface-secondary"
                      borderRadius="300"
                      minWidth="30%"
                    >
                      <BlockStack gap="400">
                        <InlineStack align="space-between" blockAlign="center">
                          <Text as="h3" variant="headingSm">
                            {plan.name}
                          </Text>
                          <Badge tone={plan.badgeTone || "info"}>
                            ${plan.priceMonthly}/mo
                          </Badge>
                        </InlineStack>

                        <Text as="p" variant="bodySm" tone="subdued">
                          {plan.description}
                        </Text>

                        <Divider />

                        <List type="bullet">
                          {plan.features.map((feature, idx) => (
                            <List.Item key={idx}>
                              <Text as="span" variant="bodySm">
                                {feature}
                              </Text>
                            </List.Item>
                          ))}
                        </List>

                        <Box paddingBlockStart="300">
                          <Button
                            variant={plan.id === "sovereign_enterprise" ? "primary" : "secondary"}
                            fullWidth
                            onClick={() => handleOrderPlan(plan.id, plan.priceMonthly)}
                            loading={fetcher.state !== "idle"}
                          >
                            Order Plan — ${plan.priceMonthly}/mo
                          </Button>
                        </Box>
                      </BlockStack>
                    </Box>
                  ))}
                </InlineStack>
              </BlockStack>
            </Card>
          </Layout.Section>

          {/* Right Rail: Open-Source Support & Sponsorship */}
          <Layout.Section variant="oneThird">
            <BlockStack gap="400">
              <Card>
                <BlockStack gap="300">
                  <Text as="h2" variant="headingMd">
                    Direct Project Contribution
                  </Text>
                  <Text as="p" variant="bodySm" tone="subdued">
                    Support continuous integration hardware, daily fuzzing suites, and MIT open-source tooling with a
                    direct contribution ($1+):
                  </Text>
                  <Divider />
                  <Link url={liveConfig.directContributionLink} target="_blank" removeUnderline>
                    <Button variant="primary" fullWidth>
                      Contribute via Stripe ($1+) ↗
                    </Button>
                  </Link>
                </BlockStack>
              </Card>

              <Card>
                <BlockStack gap="300">
                  <Text as="h2" variant="headingMd">
                    GitHub Sponsors
                  </Text>
                  <Text as="p" variant="bodySm" tone="subdued">
                    Recurring developer sponsorship through GitHub to fund public vulnerability research and tooling:
                  </Text>
                  <Divider />
                  <Link url={liveConfig.githubSponsorsUrl} target="_blank" removeUnderline>
                    <Button variant="secondary" fullWidth>
                      Sponsor aoxendine3 on GitHub ↗
                    </Button>
                  </Link>
                </BlockStack>
              </Card>

              <Card>
                <BlockStack gap="200">
                  <Text as="h3" variant="headingSm">
                    Security & Privacy Commitment
                  </Text>
                  <Text as="p" variant="bodySm" tone="subdued">
                    • <strong>Privacy First:</strong> We never touch or store consumer personal data.
                    <br />
                    • <strong>Non-Invasive:</strong> Audits run in isolated sandboxes without disrupting production.
                    <br />
                    • <strong>Open Source Core:</strong> Licensed under the MIT License for community transparency.
                  </Text>
                </BlockStack>
              </Card>
            </BlockStack>
          </Layout.Section>
        </Layout>
      </BlockStack>
    </Page>
  );
}
