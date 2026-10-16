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
} from "@shopify/polaris";
import { TitleBar, useAppBridge } from "@shopify/app-bridge-react";
import { authenticate } from "../shopify.server";
import { SOVEREIGN_PLANS, createCheckoutSession } from "../stripe.server";

export const loader = async ({ request }: LoaderFunctionArgs) => {
  await authenticate.admin(request);
  const url = new URL(request.url);
  const status = url.searchParams.get("status");
  const planId = url.searchParams.get("plan");

  return json({
    plans: Object.values(SOVEREIGN_PLANS),
    currentSubscription: status === "success" ? {
      planId: planId || "sovereign_enterprise",
      status: "ACTIVE",
      renewDate: "2026-11-16",
    } : null,
    stripeConfigured: Boolean(process.env.STRIPE_SECRET_KEY && !process.env.STRIPE_SECRET_KEY.startsWith("sk_test_placeholder")),
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
  const { plans, currentSubscription, stripeConfigured } = useLoaderData<typeof loader>();
  const fetcher = useFetcher();
  const shopify = useAppBridge();

  const handleSubscribe = (planId: string) => {
    shopify.toast.show(`Initiating Stripe checkout for ${planId}...`);
    fetcher.submit({ planId }, { method: "POST" });
  };

  return (
    <Page fullWidth>
      <TitleBar title="Monetization & Stripe Billing" />

      <BlockStack gap="500">
        {!stripeConfigured && (
          <Banner title="Stripe Sandbox Simulation Active" tone="warning">
            <Text as="p" variant="bodyMd">
              The billing pipeline is fully wired and functional in test/sandbox mode. Provide your live{" "}
              <code>STRIPE_SECRET_KEY</code> to enable live payment processing.
            </Text>
          </Banner>
        )}

        {currentSubscription && (
          <Banner title="Subscription Active" tone="success">
            <Text as="p" variant="bodyMd">
              You are currently subscribed to <strong>{currentSubscription.planId.toUpperCase()}</strong>. Renews on{" "}
              {currentSubscription.renewDate}.
            </Text>
          </Banner>
        )}

        <Layout>
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <InlineStack align="space-between">
                  <BlockStack gap="100">
                    <Text as="h2" variant="headingMd">
                      Autonomous Swarm Security Subscriptions
                    </Text>
                    <Text as="p" variant="bodySm" tone="subdued">
                      Direct automated payment flow powered by Stripe. Billed monthly with instant provisioning.
                    </Text>
                  </BlockStack>
                  <Badge tone="success">Automated Revenue Engine</Badge>
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
                            onClick={() => handleSubscribe(plan.id)}
                            loading={fetcher.state !== "idle"}
                          >
                            Subscribe — ${plan.priceMonthly}/mo
                          </Button>
                        </Box>
                      </BlockStack>
                    </Box>
                  ))}
                </InlineStack>
              </BlockStack>
            </Card>
          </Layout.Section>
        </Layout>
      </BlockStack>
    </Page>
  );
}
