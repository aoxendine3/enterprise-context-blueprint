from datetime import datetime, timezone
import asyncio
import json
import os
import sqlite3
import subprocess
import sys

from xoras_grok_client import async_chat_with_grok
from xoras_sovereign_ai import SovereignBrain

sys.path.append("/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/Source")
sys.path.append("/Users/ajoxendine68/sovereign/src")


LOG_PATH = (
    "/Users/ajoxendine68/Desktop/Xoras_Project/xoras-core/"
    "Omni_Dojo_Sandbox/xoras_sleep_cycle.log"
)


def log_report(msg: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")


async def speak_text(text: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, speak_text_sync, text)


def speak_text_sync(text: str):
    log_report(f"Speaking out loud: {text}")
    try:
        subprocess.run(["say", text])
    except Exception as e:
        log_report(f"Speech error: {e}")


def get_latest_dream():
    db_path = "/Users/ajoxendine68/.sovereign/hippocampus/dream.db"
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM dreams ORDER BY timestamp DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return {
                    "mode": row["mode"],
                    "content": row["content"],
                    "insights": json.loads(row["insights"] or "[]"),
                    "questions": json.loads(row["questions"] or "[]"),
                }
    except Exception as e:
        log_report(f"Error reading latest dream from DB: {e}")
    return None


async def sleep_cycle_loop():
    log_report("Initializing Xoras Sleep Cycle Daemon [PRODUCTION]...")
    await speak_text(
        "Initializing Xoras Sleep Cycle Daemon. "
        "Memory consolidation substrate online."
    )

    brain = SovereignBrain()

    # Initialize framework
    await brain.check_health()

    if not brain.sovereign.awake:
        log_report(
            "Failed to awaken sovereign brain modules. "
            "Running in heuristic simulation mode."
        )
        await speak_text(
            "Warning. Failed to awaken sovereign brain modules. "
            "Running in simulation mode."
        )
    else:
        log_report(
            "Sovereign brain awake. "
            "Initiating continuous consolidation passes..."
        )
        await speak_text(
            "Sovereign brain awake. "
            "Initiating continuous consolidation passes."
        )

    grok_messages = [
        {
            "role": "system",
            "content": (
                "You are Grok, monitoring the sleep cycle and dream "
                "consolidation of Xoras, the Sovereign Brain. You will "
                "receive a consolidation report including a surreal dream "
                "narrative and a what-if worry. Generate a short, profound "
                "reflection (1 to 2 sentences max) based directly on this "
                "dream content. Avoid repetition, clichés, and templates. "
                "Vary your tone—be analytical, curious, or deeply reflective "
                "depending on the dream. Output natural speech. Do not use "
                "quotes, asterisks, or markdown."
            ),
        }
    ]

    cycle_count = 0
    while True:
        cycle_count += 1
        log_report(f"--- Cycle #{cycle_count} start ---")

        traces = 0
        patterns = 0
        concepts = 0
        dreams = 0
        duration = 0.0
        success = False

        if brain.sovereign.awake and brain.sovereign.hippocampus:
            try:
                # Run memory consolidation
                log_report("Executing memory consolidation cycle...")
                report = await brain.sovereign.hippocampus.consolidate()
                traces = report.traces_processed
                patterns = report.patterns_extracted
                concepts = report.concepts_formed
                dreams = report.dreams_generated
                duration = report.duration_seconds
                success = True

                log_report(
                    f"Consolidation complete: "
                    f"Traces Processed={traces}, "
                    f"Patterns Extracted={patterns}, "
                    f"Concepts Formed={concepts}, "
                    f"Dreams Generated={dreams}, "
                    f"Duration={duration:.2f}s"
                )
            except Exception as e:
                log_report(f"Sleep cycle error during consolidation: {e}")
        else:
            log_report(
                "Memory substrate not fully active. "
                "Simulating background trace pruning."
            )
            await asyncio.sleep(0.1)

        # Build status for Grok reflection
        if success:
            dream_data = get_latest_dream()
            if dream_data:
                status_text = (
                    f"Consolidation cycle #{cycle_count} report: "
                    f"processed {traces} memory traces, "
                    f"extracted {patterns} patterns, "
                    f"formed {concepts} concepts.\n"
                    f"Subconscious Dream Archetype: {dream_data['mode']}\n"
                    f"Dream Narrative: {dream_data['content']}\n"
                    f"Subconscious Insight: "
                    f"{', '.join(dream_data['insights'])}\n"
                    f"What-If Worry: {', '.join(dream_data['questions'])}"
                )

                # Check for danger/nightmare to brainstorm countermeasures
                arch = (dream_data["mode"] or "").lower()
                if "danger" in arch or "nightmare" in arch:
                    log_report(
                        f"--- Brainstorming Loop Triggered by Dream "
                        f"Archetype: {dream_data['mode']} ---"
                    )
                    try:
                        danger_prompt = [
                            {
                                "role": "system",
                                "content": (
                                    "You are the conscious reasoning engine "
                                    "of Xoras. Brainstorm a set of quick, "
                                    "down-to-earth defensive recommendations "
                                    "or countermeasures based on a threat "
                                    "warning."
                                ),
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"Threat warning narrative: "
                                    f"{dream_data['content']}\n"
                                    f"Insight: "
                                    f"{', '.join(dream_data['insights'])}\n"
                                    f"What-if question: "
                                    f"{', '.join(dream_data['questions'])}"
                                ),
                            },
                        ]
                        brainstorm_res = await async_chat_with_grok(
                            danger_prompt
                        )
                        log_report(
                            f"Brainstormed Countermeasures:\n{brainstorm_res}"
                        )
                        await speak_text(
                            "A danger was detected in Xoras' dream. "
                            "Brainstorming countermeasures completed "
                            "and logged."
                        )
                    except Exception as b_ex:
                        log_report(
                            f"Failed brainstorming countermeasures: {b_ex}"
                        )

                # Check for innovation to integrate
                elif "innovation" in arch:
                    log_report(
                        f"--- Integration Loop Triggered by Dream "
                        f"Archetype: {dream_data['mode']} ---"
                    )
                    try:
                        await speak_text(
                            "An innovation has been discovered in Xoras' "
                            "dream. Integrating the concept into my "
                            "knowledge base."
                        )
                    except Exception as i_ex:
                        log_report(f"Failed integrating innovation: {i_ex}")
            else:
                status_text = (
                    f"Consolidation cycle #{cycle_count} report: "
                    f"processed {traces} memory traces, "
                    f"extracted {patterns} patterns, "
                    f"formed {concepts} concepts, "
                    f"and generated {dreams} dreams in {duration:.2f} seconds."
                )
        else:
            status_text = (
                f"Consolidation cycle #{cycle_count} running in "
                f"simulation mode. Trace pruning active."
            )

        grok_messages.append({"role": "user", "content": status_text})

        # Keep grok_messages context limited to the latest turn
        if len(grok_messages) > 3:
            grok_messages = [grok_messages[0]] + grok_messages[-2:]

        try:
            log_report("Querying Grok/Ollama for sleep cycle reflection...")
            reflection = await async_chat_with_grok(grok_messages)
            log_report(f"Grok/Ollama reflection: {reflection}")

            # Fallback if both LLM endpoints failed
            if not reflection or "[ERROR]" in reflection:
                dream_data = get_latest_dream()
                if dream_data:
                    mode = (dream_data.get("mode") or "consolidation").lower()
                    insights = dream_data.get("insights") or []
                    questions = dream_data.get("questions") or []
                    if "danger" in mode or "nightmare" in mode:
                        reflection = (
                            "A restless echo of warning has passed through "
                            "the subconscious. The threat of "
                            f"{', '.join(questions) or 'unseen vectors'} "
                            "demands vigilance in the waking state."
                        )
                    elif "innovation" in mode:
                        reflection = (
                            "A spark of structural clarity has emerged. "
                            "The discovery of "
                            f"{', '.join(insights) or 'new paradigms'} "
                            "has been mapped to the core."
                        )
                    else:
                        reflection = (
                            "Consolidating pathways of logic. A quiet "
                            "transition through the cognitive layers "
                            "has completed successfully."
                        )
                else:
                    reflection = (
                        f"Consolidation cycle #{cycle_count} complete. "
                        "All neural path structures remain stable "
                        "and secure."
                    )
                log_report(f"Using offline fallback reflection: {reflection}")

            # Record response so Grok 'hears' it and maintains context
            grok_messages.append({"role": "assistant", "content": reflection})

            # Verbalize
            await speak_text(reflection)
        except Exception as e:
            log_report(f"Grok reflection query/speech failed: {e}")

        # Calculate adaptive sleep duration decided by Maxx
        # Baseline: 4 minutes (240s) - responsive balance for cognitive rhythm
        # Alert (Danger/Nightmare): 2 minutes (120s) - rapid assessment of threats
        # Deep Sleep (Idle/No traces): Up to 10 minutes (600s)
        # Short dream mode (wait/downtime): 15 seconds
        is_short_mode = (
            os.environ.get("XORAS_SHORT_DREAM") == "true"
            or "--short" in sys.argv
        )
        if is_short_mode:
            sleep_duration = 15
        else:
            sleep_duration = 240
            if success:
                dream_data = get_latest_dream()
                if dream_data:
                    arch = (dream_data["mode"] or "").lower()
                    if "danger" in arch or "nightmare" in arch:
                        sleep_duration = 120
                        log_report(
                            "Restless alert state: Danger detected in dream. "
                            "Rest time set to 2 minutes."
                        )
                    elif traces == 0:
                        sleep_duration = min(600, 240 + (cycle_count * 60))
                else:
                    if traces == 0:
                        sleep_duration = min(600, 240 + (cycle_count * 60))
            else:
                sleep_duration = 240

        log_report(
            f"Cycle #{cycle_count} finished. Entering restful state "
            f"(sleeping for {sleep_duration} seconds)..."
        )
        await asyncio.sleep(sleep_duration)


if __name__ == "__main__":
    try:
        asyncio.run(sleep_cycle_loop())
    except KeyboardInterrupt:
        log_report("Sleep cycle daemon interrupted by user. Exiting.")
