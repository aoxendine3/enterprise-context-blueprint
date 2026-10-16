/**
 * Windows Node Inference & Cluster Offload Server Singleton
 * ==========================================================
 * Connects Sovereign Agentic App to the high-performance Windows Ollama node
 * at http://192.168.1.211:11434 to offload heavy inference, embeddings, and
 * deep reasoning, preventing local Apple Silicon M4 resource exhaustion.
 */

export interface WindowsNodeStatus {
  online: boolean;
  host: string;
  port: number;
  url: string;
  latencyMs: number;
  availableModels: {
    name: string;
    parameterSize: string;
    quantization: string;
    family: string;
  }[];
  activeOffloadModel: string;
  error?: string;
}

export class WindowsClusterNode {
  private host: string;
  private port: number;
  private url: string;

  constructor() {
    this.host = process.env.WINDOWS_NODE_HOST || "192.168.1.211";
    this.port = Number(process.env.WINDOWS_NODE_PORT || 11434);
    this.url = `http://${this.host}:${this.port}`;
  }

  public async getStatus(): Promise<WindowsNodeStatus> {
    const start = performance.now();
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);

      const resp = await fetch(`${this.url}/api/tags`, {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      const latencyMs = Number((performance.now() - start).toFixed(2));

      if (!resp.ok) {
        return {
          online: false,
          host: this.host,
          port: this.port,
          url: this.url,
          latencyMs,
          availableModels: [],
          activeOffloadModel: "none",
          error: `HTTP ${resp.status}`,
        };
      }

      const data = (await resp.json()) as any;
      const models = (data.models || []).map((m: any) => ({
        name: m.name,
        parameterSize: m.details?.parameter_size || "unknown",
        quantization: m.details?.quantization_level || "unknown",
        family: m.details?.family || "unknown",
      }));

      return {
        online: true,
        host: this.host,
        port: this.port,
        url: this.url,
        latencyMs,
        availableModels: models,
        activeOffloadModel: "sovereign-r1:latest",
      };
    } catch (err: any) {
      const latencyMs = Number((performance.now() - start).toFixed(2));
      return {
        online: false,
        host: this.host,
        port: this.port,
        url: this.url,
        latencyMs,
        availableModels: [],
        activeOffloadModel: "fallback-local",
        error: err.name === "AbortError" ? "Timeout (>2.5s)" : String(err.message || err),
      };
    }
  }

  public async generateOffloadedInference(
    prompt: string,
    model = "sovereign-r1:latest",
    options: Record<string, unknown> = {},
  ): Promise<{ response: string; latencyMs: number; node: string }> {
    const start = performance.now();
    try {
      const resp = await fetch(`${this.url}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model,
          prompt,
          stream: false,
          options,
        }),
      });

      const data = (await resp.json()) as any;
      const latencyMs = Number((performance.now() - start).toFixed(2));

      return {
        response: data.response || "",
        latencyMs,
        node: `Windows Cluster (${this.host})`,
      };
    } catch (err: any) {
      const latencyMs = Number((performance.now() - start).toFixed(2));
      return {
        response: `[WINDOWS CLUSTER OFFLINE FALLBACK] Reason: ${err.message}`,
        latencyMs,
        node: "Local Fallback",
      };
    }
  }

  public async generateEmbedding(
    prompt: string,
    model = "nomic-embed-text:latest",
  ): Promise<{ embedding: number[]; latencyMs: number }> {
    const start = performance.now();
    const resp = await fetch(`${this.url}/api/embeddings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model, prompt }),
    });

    const data = (await resp.json()) as any;
    const latencyMs = Number((performance.now() - start).toFixed(2));
    return {
      embedding: data.embedding || [],
      latencyMs,
    };
  }
}

export const windowsNode = new WindowsClusterNode();
