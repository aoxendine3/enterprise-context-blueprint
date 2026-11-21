import sys
import subprocess


def main():
    """Entry point. All side effects run only when invoked directly."""
    turns = [
        [
            "daxx",
            "Anthony, you were completely right. The root folder looked like a dumping ground with random patch files, receipts, dangling model symlinks, HTML files, and Docker manifests tossed on the floor. I have stepped in and executed a canonical organization pass across the root of the SSOT Agentic Brain."
        ],
        [
            "vance",
            "William Vance here. The Blackbox Sentry enforced our strict folder schema from Section Three of the charter. Twenty-one dumped files and artifacts have been relocated to their canonical destinations: reports to docs and catch log, diffs to scratch, HTML to legacy web, certificates to security certs, and Docker files to ops docker."
        ],
        [
            "daxx",
            "Furthermore, that Wan two point one symlink was an old Text-to-Video diffusion model pointer targeting an unplugged USB drive from October tenth, not your Windows S3 model. I moved it cleanly into the Barn symlinks folder. The root of your brain is now restored to its pristine governance contract: only ROOTS, AGENTS, README, and foundational system manifests remain."
        ]
    ]

    import json
    p = subprocess.Popen(
        ["python3", "ops/scripts/council_audio_dispatch.py", "--json"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = p.communicate(input=json.dumps(turns))
    print(stdout)


if __name__ == "__main__":
    main()
