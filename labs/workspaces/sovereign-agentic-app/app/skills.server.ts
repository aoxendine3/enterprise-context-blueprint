/**
 * Skills Registry Server Singleton
 * =================================
 * Discovers, parses, and provides all sovereign skills located in
 * labs/workspaces/sovereign-agentic-app/.agents/skills/
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const APP_ROOT = path.resolve(__dirname, "..");
const SKILLS_DIR = path.join(APP_ROOT, ".agents", "skills");

export interface SovereignSkill {
  id: string;
  name: string;
  description: string;
  category: "Security" | "Affiliate & Growth" | "Governance" | "Infrastructure" | "AI & Memory";
  targetHost: "Mac M4 (Bare-Metal)" | "Windows 192.168.1.211 (GPU Offload)" | "Hybrid Swarm";
  path: string;
  files: string[];
  hasScripts: boolean;
}

export function getAllSkills(): SovereignSkill[] {
  if (!fs.existsSync(SKILLS_DIR)) {
    return [];
  }

  const entries = fs.readdirSync(SKILLS_DIR, { withFileTypes: true });
  const skills: SovereignSkill[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;

    const skillPath = path.join(SKILLS_DIR, entry.name);
    const skillMdPath = path.join(skillPath, "SKILL.md");

    let name = entry.name;
    let description = "Autonomous Swarm Capability";

    if (fs.existsSync(skillMdPath)) {
      try {
        const content = fs.readFileSync(skillMdPath, "utf-8");
        const matchName = content.match(/^name:\s*(.+)$/m);
        const matchDesc = content.match(/^description:\s*(.+)$/m);
        if (matchName && matchName[1]) name = matchName[1].trim();
        if (matchDesc && matchDesc[1]) description = matchDesc[1].trim();
      } catch {
        // Fallback to folder name
      }
    }

    const subfiles = fs.readdirSync(skillPath);

    let category: SovereignSkill["category"] = "Governance";
    let targetHost: SovereignSkill["targetHost"] = "Mac M4 (Bare-Metal)";

    if (entry.name.includes("affiliate") || entry.name.includes("creative") || entry.name.includes("landing")) {
      category = "Affiliate & Growth";
      targetHost = "Windows 192.168.1.211 (GPU Offload)";
    } else if (entry.name.includes("upgp") || entry.name.includes("locking") || entry.name.includes("shield")) {
      category = "Security";
      targetHost = "Mac M4 (Bare-Metal)";
    } else if (entry.name.includes("xmars") || entry.name.includes("provenance")) {
      category = "AI & Memory";
      targetHost = "Hybrid Swarm";
    } else if (entry.name.includes("deployment") || entry.name.includes("github")) {
      category = "Infrastructure";
      targetHost = "Mac M4 (Bare-Metal)";
    }

    skills.push({
      id: entry.name,
      name,
      description,
      category,
      targetHost,
      path: `.agents/skills/${entry.name}/SKILL.md`,
      files: subfiles,
      hasScripts: subfiles.includes("scripts"),
    });
  }

  return skills.sort((a, b) => a.name.localeCompare(b.name));
}
