import { useState } from "react";
import type { ActionFunctionArgs, LoaderFunctionArgs } from "@remix-run/node";
import { json } from "@remix-run/node";
import { useLoaderData, useFetcher } from "@remix-run/react";
import {
  Page,
  Layout,
  Text,
  Card,
  Button,
  BlockStack,
  Box,
  Badge,
  Banner,
  InlineStack,
  Divider,
  Tag,
  Grid,
} from "@shopify/polaris";
import { TitleBar, useAppBridge } from "@shopify/app-bridge-react";
import { authenticate } from "../shopify.server";
import { getAllSkills, type SovereignSkill } from "../skills.server";
import { windowsNode, type WindowsNodeStatus } from "../windows_node.server";

export const loader = async ({ request }: LoaderFunctionArgs) => {
  await authenticate.admin(request);

  const skills: SovereignSkill[] = getAllSkills();
  const windowsStatus: WindowsNodeStatus = await windowsNode.getStatus();

  return json({
    skills,
    windowsStatus,
    timestamp: new Date().toISOString(),
  });
};

export const action = async ({ request }: ActionFunctionArgs) => {
  await authenticate.admin(request);
  const formData = await request.formData();
  const actionType = formData.get("actionType");

  if (actionType === "TEST_WINDOWS_OFFLOAD") {
    const prompt = "Briefly state your role and verification status as the offloaded Sovereign reasoning model.";
    const result = await windowsNode.generateOffloadedInference(prompt, "sovereign-r1:latest");
    return json({
      success: true,
      actionType,
      result,
      timestamp: new Date().toISOString(),
    });
  }

  return json({ success: false, error: "Unknown action" });
};

export default function SkillsPage() {
  const data = useLoaderData<typeof loader>();
  const fetcher = useFetcher<typeof action>();
  const shopify = useAppBridge();
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  const categories = ["ALL", "Security", "Affiliate & Growth", "Governance", "Infrastructure", "AI & Memory"];

  const filteredSkills = selectedCategory === "ALL"
    ? data.skills
    : data.skills.filter((s) => s.category === selectedCategory);

  const handleTestWindowsOffload = () => {
    fetcher.submit({ actionType: "TEST_WINDOWS_OFFLOAD" }, { method: "POST" });
    shopify.toast.show("Dispatching inference test to Windows Cluster (192.168.1.211)...");
  };

  const offloadTestResult = fetcher.data?.result;

  return (
    <Page fullWidth>
      <TitleBar title="Sovereign Skills & Cluster Offload Manager">
        <button variant="primary" onClick={handleTestWindowsOffload}>
          Test Windows GPU Offload
        </button>
      </TitleBar>

      <BlockStack gap="500">
        {/* Banner: Dual-Node Hardware Allocation */}
        <Banner
          title="Hardware Workload Balance — Local Mac M4 + Windows Host (192.168.1.211)"
          tone="info"
        >
          <Text as="p" variant="bodyMd">
            To prevent local resource exhaustion on the Mac M4, compute-heavy tasks (deep reasoning, AST synthesis,
            affiliate creative distillation, high-dimensional vector embeddings) are dynamically offloaded to the
            remote Windows cluster host over LAN.
          </Text>
        </Banner>

        {/* Windows Cluster Telemetry Card */}
        <Card>
          <BlockStack gap="400">
            <InlineStack align="space-between" blockAlign="center">
              <InlineStack gap="300" blockAlign="center">
                <Text as="h2" variant="headingMd">
                  Windows Compute Cluster (Remote Worker)
                </Text>
                <Badge tone={data.windowsStatus.online ? "success" : "critical"}>
                  {data.windowsStatus.online ? "Online & Connected" : "Offline"}
                </Badge>
              </InlineStack>
              <Text as="p" variant="bodySm" tone="subdued">
                Endpoint: <code>{data.windowsStatus.url}</code> ({data.windowsStatus.latencyMs}ms ping)
              </Text>
            </InlineStack>
            <Divider />

            <InlineStack gap="600" wrap>
              <Box>
                <Text as="p" variant="bodySm" tone="subdued">
                  Active Offload Model
                </Text>
                <Text as="p" variant="headingSm">
                  <code>{data.windowsStatus.activeOffloadModel}</code>
                </Text>
              </Box>
              <Box>
                <Text as="p" variant="bodySm" tone="subdued">
                  Available Models on Node
                </Text>
                <Text as="p" variant="headingSm">
                  {data.windowsStatus.availableModels.length} Models Loaded
                </Text>
              </Box>
              <Box>
                <Text as="p" variant="bodySm" tone="subdued">
                  Network Latency
                </Text>
                <Text as="p" variant="headingSm">
                  {data.windowsStatus.latencyMs} ms (Local LAN)
                </Text>
              </Box>
            </InlineStack>

            <Box paddingBlockStart="200">
              <Text as="p" variant="bodySm">
                <strong>Hosted Models on Windows Node:</strong>
              </Text>
              <Box paddingBlockStart="100">
                <InlineStack gap="200" wrap>
                  {data.windowsStatus.availableModels.map((m) => (
                    <Badge key={m.name} tone="info">
                      {`${m.name} (${m.parameterSize})`}
                    </Badge>
                  ))}
                </InlineStack>
              </Box>
            </Box>

            {offloadTestResult && (
              <Box
                padding="300"
                background="bg-surface-secondary"
                borderRadius="200"
              >
                <BlockStack gap="100">
                  <Text as="p" variant="bodySm">
                    <strong>Offload Response from {offloadTestResult.node}:</strong>
                  </Text>
                  <Text as="p" variant="bodyXs">
                    {offloadTestResult.response}
                  </Text>
                  <Text as="p" variant="bodyXs" tone="subdued">
                    Round-trip latency: {offloadTestResult.latencyMs} ms
                  </Text>
                </BlockStack>
              </Box>
            )}
          </BlockStack>
        </Card>

        {/* Skills Filter & Inventory Card */}
        <Card>
          <BlockStack gap="400">
            <InlineStack align="space-between" blockAlign="center">
              <BlockStack gap="100">
                <Text as="h2" variant="headingMd">
                  Active Sovereign Swarm Skills ({data.skills.length} Capabilities)
                </Text>
                <Text as="p" variant="bodySm" tone="subdued">
                  All production skills synchronized into <code>.agents/skills/</code> and ready for autonomous dispatch.
                </Text>
              </BlockStack>
              <InlineStack gap="200">
                {categories.map((cat) => (
                  <Tag
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                  >
                    {cat}
                  </Tag>
                ))}
              </InlineStack>
            </InlineStack>
            <Divider />

            <Grid>
              {filteredSkills.map((skill) => {
                const isOffloaded = skill.targetHost.includes("Windows");

                return (
                  <Grid.Cell key={skill.id} columnSpan={{ xs: 6, sm: 6, md: 6, lg: 6, xl: 6 }}>
                    <Box
                      padding="400"
                      background="bg-surface-secondary"
                      borderRadius="200"
                      borderWidth="025"
                      borderColor={isOffloaded ? "border-brand" : "border"}
                    >
                      <BlockStack gap="200">
                        <InlineStack align="space-between" blockAlign="center">
                          <Text as="h3" variant="headingSm">
                            {skill.name}
                          </Text>
                          <Badge tone={isOffloaded ? "attention" : "success"}>
                            {skill.targetHost}
                          </Badge>
                        </InlineStack>

                        <Text as="p" variant="bodySm" tone="subdued">
                          {skill.description}
                        </Text>

                        <Divider />

                        <InlineStack align="space-between" blockAlign="center">
                          <Text as="p" variant="bodyXs" tone="subdued">
                            Category: <strong>{skill.category}</strong>
                          </Text>
                          <Text as="p" variant="bodyXs">
                            <code>{skill.path}</code>
                          </Text>
                        </InlineStack>
                      </BlockStack>
                    </Box>
                  </Grid.Cell>
                );
              })}
            </Grid>
          </BlockStack>
        </Card>
      </BlockStack>
    </Page>
  );
}
