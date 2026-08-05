"""
Central voice service for Xoras Systems / ELITE_BOW.

All agents route TTS here — xAI (cloned voices), ElevenLabs, then Mac say.
Handles: API keys, voice resolution, rate limits, disk cache, local fallback.

Prosody (highs/lows): agents may mark beats with [soft], [warm], [lift], [firm],
[excited], [whisper], [sigh], [pause], [steady], [proud], [sharp], [low].
- ElevenLabs (esp. v3): tags kept / normalized as Audio Tags + stability/style nudge.
- Local Mac say: tags stripped; punctuation + optional [[slnc]] / mild rate bias.
  Do NOT multi-call rate-chop — neural Enhanced voices need writing, not WPM jumps.
- xAI: tags stripped to natural punctuation (no guaranteed tag support).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Tuple

# ── Prosody beat tags (highs / lows) ───────────────────────────────────────
# Square-bracket cues agents embed in speak text. See ops/reports/triad/tonal_tts_research.md
PROSODY_TAG_RE = re.compile(r"\[([A-Za-z][A-Za-z0-9_\s]{0,32})\]")

# Canonical beat → ElevenLabs-style audio tag word(s)
ELEVEN_AUDIO_TAGS: dict[str, str] = {
    "soft": "softly",
    "softly": "softly",
    "warm": "warmly",
    "warmly": "warmly",
    "lift": "warmly",
    "proud": "proudly",
    "excited": "excited",
    "firm": "seriously",
    "sharp": "firmly",
    "low": "quietly",
    "quiet": "quietly",
    "whisper": "whispering",
    "whispering": "whispering",
    "sigh": "sighs",
    "sighs": "sighs",
    "pause": "pauses",
    "pauses": "pauses",
    "steady": "calmly",
    "calm": "calmly",
    "rush": "rushed",
    "rushed": "rushed",
    "sad": "sadly",
    "happy": "happily",
    "angry": "frustrated",
}

# Local: how a beat shapes writing (not cartoon rate chops)
LOCAL_BEAT_PREFIX: dict[str, str] = {
    "soft": "… ",
    "softly": "… ",
    "low": "… ",
    "quiet": "… ",
    "whisper": "… ",
    "whispering": "… ",
    "sigh": "*sigh* ",
    "sighs": "*sigh* ",
    "pause": "",
    "pauses": "",
    "warm": "",
    "warmly": "",
    "lift": "",
    "proud": "",
    "excited": "",
    "firm": "",
    "sharp": "",
    "steady": "",
    "calm": "",
}

# Mild single-utterance rate bias vs profile.local_rate (clamped later)
LOCAL_RATE_BIAS: dict[str, int] = {
    "soft": -6,
    "softly": -6,
    "low": -8,
    "quiet": -8,
    "whisper": -10,
    "whispering": -10,
    "sigh": -4,
    "pause": 0,
    "warm": 0,
    "lift": 2,
    "proud": 3,
    "excited": 5,
    "firm": 1,
    "sharp": 2,
    "steady": 0,
    "rush": 6,
    "rushed": 6,
}


@dataclass
class ProsodyPlan:
    """Prepared text + delivery knobs for one backend."""

    text: str
    tags: list[str] = field(default_factory=list)
    local_rate: Optional[int] = None
    eleven_stability: Optional[float] = None
    eleven_style: Optional[float] = None
    use_expressive_model: bool = False


def _norm_tag(raw: str) -> str:
    return re.sub(r"\s+", " ", raw.strip().lower())


def extract_prosody_tags(text: str) -> list[str]:
    return [_norm_tag(m.group(1)) for m in PROSODY_TAG_RE.finditer(text or "")]


def prepare_prosody(text: str, backend: str, base_rate: int = 118) -> ProsodyPlan:
    """Map [beat] markers into backend-specific delivery. One utterance — no rate-chop loops."""
    raw = (text or "").strip()
    tags = extract_prosody_tags(raw)
    if not tags and "[" not in raw:
        return ProsodyPlan(text=raw)

    backend = (backend or "local").lower()
    if backend == "elevenlabs":
        def repl(m: re.Match[str]) -> str:
            key = _norm_tag(m.group(1))
            word = ELEVEN_AUDIO_TAGS.get(key, key.replace(" ", " "))
            return f"[{word}]"

        out = PROSODY_TAG_RE.sub(repl, raw)
        # More room for highs/lows when beats present
        return ProsodyPlan(
            text=out,
            tags=tags,
            eleven_stability=0.35,
            eleven_style=0.45,
            use_expressive_model=True,
        )

    # local + xai: strip tags, enrich punctuation, optional silence embeds for local only
    parts: list[str] = []
    last = 0
    rate_bias = 0
    for m in PROSODY_TAG_RE.finditer(raw):
        parts.append(raw[last : m.start()])
        key = _norm_tag(m.group(1))
        rate_bias += LOCAL_RATE_BIAS.get(key, 0)
        if backend == "local":
            if key in ("pause", "pauses", "sigh"):
                parts.append(" [[slnc 400]] ")
            elif key in ("soft", "low"):
                parts.append(" [[slnc 250]] ")
            else:
                parts.append(LOCAL_BEAT_PREFIX.get(key, ""))
        else:
            parts.append(LOCAL_BEAT_PREFIX.get(key, ""))
        last = m.end()
    parts.append(raw[last:])
    plain = re.sub(r"[ \t]{2,}", " ", "".join(parts))
    plain = re.sub(r"\n{3,}", "\n\n", plain).strip()
    
    if backend == "local":
        # Smooth tone transitions by preventing duplicate silence embeds
        plain = re.sub(r"\[\[slnc \d+\]\]\s*\[\[slnc \d+\]\]", "[[slnc 350]]", plain)
        # Clean sub-clause punctuation flow
        plain = re.sub(r",(?!\s*\[\[slnc)", ", [[slnc 180]]", plain)
        plain = re.sub(r"\.(?!\s*\[\[slnc)", ". [[slnc 350]]", plain)
        plain = re.sub(r"[ \t]{2,}", " ", plain)

    # Light writing cues neural Mac voices actually follow
    if any(t in tags for t in ("excited", "proud", "lift", "sharp")):
        if not plain.endswith(("!", "?", ".")):
            plain = plain.rstrip(",;:") + "."
    local_rate = max(90, min(160, base_rate + max(-12, min(12, rate_bias))))
    return ProsodyPlan(text=plain, tags=tags, local_rate=local_rate if tags else None)

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

DEFAULT_ELITE_BOW = Path.home() / "Desktop" / "Xoras_Workspace" / "ELITE_BOW"
DEFAULT_VOICE_REG = DEFAULT_ELITE_BOW / "core" / "agent_voice_registry.yaml"
DEFAULT_AGENT_REG = DEFAULT_ELITE_BOW / "core" / "agent_registry.yaml"
DEFAULT_CACHE = Path.home() / ".sovereign" / "voice_cache"
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
XAI_TTS_URL = "https://api.x.ai/v1/tts"

MAX_CACHE_FILES = 64
MIN_API_INTERVAL_SEC = 0.35


def _load_dotenv() -> None:
    for path in (
        Path(__file__).resolve().parent.parent / ".env",
        Path.home() / ".env",
    ):
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip('\'\"')
                if k and k not in os.environ:
                    os.environ[k] = v
        except PermissionError:
            # Unable to read .env due to permission restrictions; skip it.
            continue


@dataclass
class VoiceProfile:
    agent_id: str
    elevenlabs_voice_id: Optional[str]
    xai_voice_id: Optional[str]
    local_voice: str
    local_rate: int
    model_id: str
    elevenlabs_settings: dict[str, Any]
    preferred_backend: str  # auto | xai | elevenlabs | local


@dataclass
class SpeakResult:
    agent_id: str
    backend: str  # xai | elevenlabs | cache | local_say
    audio_path: Optional[str]
    played: bool
    error: Optional[str] = None


class VoiceService:
    def __init__(
        self,
        voice_registry_path: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
    ):
        _load_dotenv()
        self.voice_registry_path = voice_registry_path or Path(
            os.getenv("XORAS_VOICE_REGISTRY", str(DEFAULT_VOICE_REG))
        )
        self.cache_dir = cache_dir or Path(os.getenv("XORAS_VOICE_CACHE", str(DEFAULT_CACHE)))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._api_lock = threading.Lock()
        self._last_api_at = 0.0
        self._reg: dict[str, Any] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        if yaml is None or not self.voice_registry_path.is_file():
            self._reg = {}
            return
        self._reg = yaml.safe_load(self.voice_registry_path.read_text(encoding="utf-8")) or {}

    def _agent_json_voice_id(self, agent_id: str) -> Optional[str]:
        if yaml is None or not DEFAULT_AGENT_REG.is_file():
            return None
        data = yaml.safe_load(DEFAULT_AGENT_REG.read_text(encoding="utf-8")) or {}
        meta = data.get("agents", {}).get(agent_id)
        if not meta:
            return None
        card = DEFAULT_ELITE_BOW / meta.get("path", "") / "agent.json"
        if not card.is_file():
            return None
        try:
            payload = json.loads(card.read_text(encoding="utf-8"))
            return payload.get("voice_id")
        except (json.JSONDecodeError, OSError):
            return None

    def resolve_profile(self, agent_id: str) -> VoiceProfile:
        aid = agent_id.lower().strip().replace("-", "_")
        defaults = self._reg.get("defaults", {})
        agents = self._reg.get("agents", {})
        cfg = agents.get(aid, {})
        if not cfg and aid == "joelle":
            cfg = agents.get("narrator", {})
        if not cfg and aid in ("daxx_ai", "daxx.ai"):
            cfg = agents.get("daxx", {})
            aid = "daxx"
        # Honor aliases: list on any agent entry
        if not cfg:
            for canon, entry in agents.items():
                aliases = entry.get("aliases") or []
                if aid in {str(a).lower().replace("-", "_") for a in aliases}:
                    cfg = entry
                    aid = str(canon).lower().replace("-", "_")
                    break

        banned = set(defaults.get("ban_voices", []))
        local_voice = cfg.get("local_voice") or defaults.get("clear_female_default", "Joelle (Enhanced)")
        if local_voice in banned:
            local_voice = "Joelle (Enhanced)"

        el_id = cfg.get("elevenlabs_voice_id") or self._agent_json_voice_id(aid)
        xai_id = cfg.get("xai_voice_id") or cfg.get("xai_voice")
        preferred = str(
            cfg.get("preferred_backend") or defaults.get("preferred_backend") or "auto"
        ).lower()
        el_settings = dict(defaults.get("elevenlabs_settings") or {})
        el_settings.update(dict(cfg.get("elevenlabs_settings") or {}))
        # Prosody defaults from registry
        prosody = dict(defaults.get("prosody") or {})
        prosody.update(dict(cfg.get("prosody") or {}))
        model_id = str(
            cfg.get("elevenlabs_model")
            or prosody.get("elevenlabs_expressive_model")
            or defaults.get("elevenlabs_model", "eleven_multilingual_v2")
        )
        return VoiceProfile(
            agent_id=aid,
            elevenlabs_voice_id=el_id,
            xai_voice_id=xai_id,
            local_voice=local_voice,
            local_rate=int(cfg.get("local_rate") or defaults.get("local_rate", 118)),
            model_id=model_id,
            elevenlabs_settings=el_settings,
            preferred_backend=preferred,
        )

    def _cache_key(self, profile: VoiceProfile, text: str) -> str:
        raw = (
            f"{profile.agent_id}|{profile.xai_voice_id}|{profile.elevenlabs_voice_id}|"
            f"{profile.model_id}|{profile.preferred_backend}|{text}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.mp3"

    def _trim_cache(self) -> None:
        files = sorted(self.cache_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
        while len(files) > MAX_CACHE_FILES:
            files.pop(0).unlink(missing_ok=True)

    def _rate_limit_wait(self) -> None:
        with self._api_lock:
            now = time.monotonic()
            wait = MIN_API_INTERVAL_SEC - (now - self._last_api_at)
            if wait > 0:
                time.sleep(wait)
            self._last_api_at = time.monotonic()

    def _xai_api_key(self) -> str:
        return os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY") or ""

    def _xai_fetch(self, profile: VoiceProfile, text: str) -> bytes:
        key = self._xai_api_key()
        if not key:
            raise RuntimeError("XAI_API_KEY not set")
        if not profile.xai_voice_id:
            raise RuntimeError(f"No xai_voice_id for agent {profile.agent_id}")

        self._rate_limit_wait()
        body = {
            "text": text[:8000],
            "voice_id": profile.xai_voice_id,
            "language": "en",
            "output_format": {
                "codec": "mp3",
                "sample_rate": 44100,
                "bit_rate": 128000,
            },
        }
        req = urllib.request.Request(
            XAI_TTS_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"xAI TTS HTTP {e.code}: {detail}") from e

    def _elevenlabs_fetch(
        self, profile: VoiceProfile, text: str, plan: Optional[ProsodyPlan] = None
    ) -> bytes:
        key = os.environ.get("ELEVENLABS_API_KEY", "")
        if not key:
            raise RuntimeError("ELEVENLABS_API_KEY not set")
        if not profile.elevenlabs_voice_id:
            raise RuntimeError(f"No ElevenLabs voice_id for agent {profile.agent_id}")

        self._rate_limit_wait()
        settings = dict(profile.elevenlabs_settings)
        model_id = profile.model_id
        if plan:
            if plan.eleven_stability is not None:
                settings["stability"] = plan.eleven_stability
            if plan.eleven_style is not None:
                settings["style"] = plan.eleven_style
            if plan.use_expressive_model:
                # Prefer v3 when beats present (Audio Tags); fall back stays multilingual
                expressive = (
                    (self._reg.get("defaults") or {}).get("prosody") or {}
                ).get("elevenlabs_expressive_model") or "eleven_v3"
                model_id = str(expressive)
        body = {
            "text": text[:8000],
            "model_id": model_id,
            "voice_settings": {
                "stability": settings.get("stability", 0.55),
                "similarity_boost": settings.get("similarity_boost", 0.78),
                "style": settings.get("style", 0.15),
                "use_speaker_boost": settings.get("use_speaker_boost", True),
            },
        }
        url = ELEVENLABS_URL.format(voice_id=profile.elevenlabs_voice_id)
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:500]
            # If v3 unavailable, retry once on multilingual without failing the speak
            if plan and plan.use_expressive_model and "eleven_v3" in model_id:
                sys.stderr.write(
                    f"[voice_service] eleven_v3 failed ({e.code}); retry multilingual_v2\n"
                )
                profile_fallback = profile
                # mutate copy via temporary model
                old = profile.model_id
                profile.model_id = "eleven_multilingual_v2"
                try:
                    return self._elevenlabs_fetch(profile, text, plan=None)
                finally:
                    profile.model_id = old
            raise RuntimeError(f"ElevenLabs HTTP {e.code}: {detail}") from e

    @staticmethod
    def _play(path: Path) -> None:
        subprocess.run(["afplay", str(path)], check=False)

    @staticmethod
    def _say_local(
        profile: VoiceProfile,
        text: str,
        out_aiff: Optional[Path] = None,
        rate: Optional[int] = None,
    ) -> Path:
        import tempfile

        use_rate = int(rate if rate is not None else profile.local_rate)
        cmd = ["say", "-v", profile.local_voice, "-r", str(use_rate)]
        tmp: Optional[Path] = None
        if len(text) > 400 or "\n" in text or "[[" in text:
            tmp = Path(tempfile.mkstemp(suffix=".txt", prefix="xoras_speak_")[1])
            tmp.write_text(text, encoding="utf-8")
            if out_aiff:
                cmd.extend(["-o", str(out_aiff), "-f", str(tmp)])
            else:
                cmd.extend(["-f", str(tmp)])
        elif out_aiff:
            cmd.extend(["-o", str(out_aiff), text])
        else:
            cmd.append(text)
        try:
            subprocess.run(cmd, check=True)
        finally:
            if tmp and tmp.is_file():
                tmp.unlink(missing_ok=True)
        return out_aiff if out_aiff is not None else Path("speakers")

    def speak(
        self,
        agent_id: str,
        text: str,
        *,
        play: bool = True,
        out_path: Optional[Path] = None,
        use_cache: bool = True,
        backend: Optional[str] = None,
    ) -> SpeakResult:
        text = text.strip()
        if not text:
            return SpeakResult(agent_id, "none", None, False, "empty text")

        profile = self.resolve_profile(agent_id)
        pref = (backend or os.environ.get("XORAS_SPEAK_BACKEND") or profile.preferred_backend or "auto").lower()

        # Resolve which path we'll try first so prosody prep matches the ear
        if pref == "local":
            plan_backend = "local"
        elif pref == "elevenlabs":
            plan_backend = "elevenlabs"
        elif pref == "xai":
            plan_backend = "xai"
        else:
            # auto: cloud if keys, else local — prosody for first cloud candidate
            if self._xai_api_key() and profile.xai_voice_id:
                plan_backend = "xai"
            elif os.environ.get("ELEVENLABS_API_KEY") and profile.elevenlabs_voice_id:
                plan_backend = "elevenlabs"
            else:
                plan_backend = "local"

        plan = prepare_prosody(text, plan_backend, base_rate=profile.local_rate)
        speak_text = plan.text

        cache_key = self._cache_key(profile, f"{plan_backend}|{speak_text}")
        cached = self._cache_path(cache_key)

        if use_cache and cached.is_file() and cached.stat().st_size > 0:
            dest = out_path or cached
            if out_path and out_path != cached:
                dest.write_bytes(cached.read_bytes())
            if play:
                self._play(dest)
            return SpeakResult(agent_id, "cache", str(dest), play)

        backends: list[str] = []
        if pref == "xai":
            backends = ["xai", "elevenlabs"]
        elif pref == "elevenlabs":
            backends = ["elevenlabs", "xai"]
        elif pref == "local":
            backends = []
        else:
            backends = ["xai", "elevenlabs"] if profile.xai_voice_id else ["elevenlabs", "xai"]

        for be in backends:
            try:
                if be == "xai":
                    if not (self._xai_api_key() and profile.xai_voice_id):
                        continue
                    xplan = prepare_prosody(text, "xai", base_rate=profile.local_rate)
                    audio = self._xai_fetch(profile, xplan.text)
                else:
                    if not (os.environ.get("ELEVENLABS_API_KEY") and profile.elevenlabs_voice_id):
                        continue
                    eplan = prepare_prosody(text, "elevenlabs", base_rate=profile.local_rate)
                    audio = self._elevenlabs_fetch(profile, eplan.text, plan=eplan)
                cached.write_bytes(audio)
                self._trim_cache()
                dest = out_path or cached
                if out_path and out_path != cached:
                    dest.write_bytes(audio)
                if play:
                    self._play(dest)
                return SpeakResult(agent_id, be, str(dest), play)
            except Exception as exc:
                sys.stderr.write(f"[voice_service] {be} failed: {exc}\n")

        try:
            lplan = prepare_prosody(text, "local", base_rate=profile.local_rate)
            aiff = out_path if out_path and str(out_path).endswith(".aiff") else None
            if aiff is None and out_path:
                aiff = out_path.with_suffix(".aiff")
            path = self._say_local(profile, lplan.text, aiff, rate=lplan.local_rate)
            if play and aiff is not None and aiff.is_file():
                self._play(aiff)
                played = True
            elif play and aiff is None:
                played = True
            else:
                played = False
            return SpeakResult(
                agent_id,
                "local_say",
                str(path) if path else "speakers",
                played,
            )
        except Exception as exc:
            return SpeakResult(agent_id, "local_say", None, False, str(exc))

    def speak_file(self, agent_id: str, text_file: Path, **kwargs: Any) -> SpeakResult:
        return self.speak(agent_id, text_file.read_text(encoding="utf-8"), **kwargs)


_service: Optional[VoiceService] = None


def get_voice_service() -> VoiceService:
    global _service
    if _service is None:
        _service = VoiceService()
    return _service


def main() -> None:
    parser = argparse.ArgumentParser(description="Xoras central voice service")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("speak", help="Synthesize and optionally play")
    sp.add_argument("--agent", "-a", required=True, help="Agent id (maxx, xoras, jarvis, narrator, …)")
    sp.add_argument("--text", "-t", default="", help="Text to speak")
    sp.add_argument("--file", "-f", type=Path, help="Read text from file")
    sp.add_argument("--no-play", action="store_true")
    sp.add_argument("--out", type=Path, help="Write audio to path")
    sp.add_argument("--no-cache", action="store_true")

    sub.add_parser("resolve", help="Print resolved voice profile")
    sp_res = sub.choices["resolve"]
    sp_res.add_argument("--agent", "-a", required=True)

    args = parser.parse_args()
    svc = get_voice_service()

    if args.cmd == "resolve":
        p = svc.resolve_profile(args.agent)
        print(json.dumps(p.__dict__, indent=2))
        return

    text = args.text
    if args.file:
        text = args.file.read_text(encoding="utf-8")
    if not text.strip():
        print("No text provided", file=sys.stderr)
        sys.exit(1)

    result = svc.speak(
        args.agent,
        text,
        play=not args.no_play,
        out_path=args.out,
        use_cache=not args.no_cache,
    )
    print(json.dumps(result.__dict__, indent=2))
    if result.error:
        sys.exit(1)


if __name__ == "__main__":
    main()
