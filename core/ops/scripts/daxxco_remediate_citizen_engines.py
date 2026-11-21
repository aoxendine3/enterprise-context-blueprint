import os
import sys


def main():
    """Entry point. All side effects run only when invoked directly."""
    files_to_fix = [
        "workspaces/sandboxes/sophia/tools/sophia_engine.py",
        "workspaces/sandboxes/sia_core/tools/sia_core_engine.py",
        "workspaces/sandboxes/axlon/tools/axlon_engine.py",
        "workspaces/sandboxes/lex/tools/lex_engine.py",
        "workspaces/sandboxes/noboo/tools/noboo_engine.py",
        "workspaces/sandboxes/arthur/tools/arthur_engine.py"
    ]

    fixed = 0
    for rel in files_to_fix:
        if os.path.exists(rel):
            with open(rel, "rb") as fp:
                content = fp.read().decode("utf-8", errors="ignore")
            if content.endswith("\\n"):
                content = content[:-2] + "\n"
                with open(rel, "wb") as fp:
                    fp.write(content.encode("utf-8"))
                print(f"Fixed trailing literal \\n in: {rel}")
                fixed += 1

    print(f"Total citizen engines remediated: {fixed}")


if __name__ == "__main__":
    main()
