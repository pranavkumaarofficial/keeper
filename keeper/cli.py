"""Command-line entry point for `keeper`."""
import re
import sys
import json
import time
import argparse

# Force UTF-8 on Windows so ANSI art and Unicode characters work correctly.
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from . import art, pool
from .render import render


# Commands matching these get denied by the keeper in Claude Code hook mode.
DANGER = [
    r"\brm\s+-[a-z]*r[a-z]*f",         # rm -rf
    r"\bsudo\s+rm\b",
    r"\bgit\s+push\s+.*--force.*\b(main|master)\b",
    r"\bchmod\s+777\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r">\s*/dev/sd",
    r":\(\)\s*\{",                     # fork bomb
    r"\bDROP\s+TABLE\b",
]


def _claude_settings_path(project):
    from pathlib import Path
    if project:
        return Path.cwd() / ".claude" / "settings.json"
    return Path.home() / ".claude" / "settings.json"


def _hook_command():
    """A command string that works regardless of PATH: this python + -m keeper."""
    return f'"{sys.executable}" -m keeper --hook'


def install_hook(args):
    """Write the PreToolUse hook into Claude Code's settings.json for the user."""
    import json as _json
    from pathlib import Path
    path = _claude_settings_path(args.project)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if path.exists():
        try:
            data = _json.loads(path.read_text() or "{}")
        except Exception:
            print(f"! {path} exists but isn't valid JSON — not touching it.")
            print("  Add the hook manually (see the README).")
            return 1

    cmd = _hook_command()
    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])

    # refresh an existing keeper entry, or append a new one
    for block in pre:
        for h in block.get("hooks", []):
            if "keeper" in h.get("command", "") and "--hook" in h.get("command", ""):
                h["command"] = cmd
                path.write_text(_json.dumps(data, indent=2))
                print(f"✓ keeper hook refreshed in {path}")
                return 0
    pre.append({"matcher": "Bash",
                "hooks": [{"type": "command", "command": cmd}]})
    path.write_text(_json.dumps(data, indent=2))
    print(f"✓ keeper is now guarding Claude Code.\n  wrote hook to: {path}")
    print(f"  command:       {cmd}")
    print("  try it: ask Claude Code to run  rm -rf ./tmpjunk")
    return 0


def uninstall_hook(args):
    import json as _json
    path = _claude_settings_path(args.project)
    if not path.exists():
        print(f"nothing to remove — {path} doesn't exist.")
        return 0
    try:
        data = _json.loads(path.read_text() or "{}")
    except Exception:
        print(f"! {path} isn't valid JSON — leaving it alone.")
        return 1
    pre = data.get("hooks", {}).get("PreToolUse", [])
    kept = [b for b in pre
            if not any("keeper" in h.get("command", "")
                       for h in b.get("hooks", []))]
    data.setdefault("hooks", {})["PreToolUse"] = kept
    path.write_text(_json.dumps(data, indent=2))
    print(f"✓ keeper hook removed from {path}")
    return 0


def keeper_visual(width=90, crop=True):
    """A rendered pool image (ascii, cropped) for the block screen.

    Uses a random image from the pool so a different save flashes up each block.
    Falls back to the hand-drawn keeper if there's no image or Pillow is missing.
    """
    try:
        path, _ = pool.pick(None)
        if path:
            lines, err = render(path, width, "ascii", crop)
            if lines and not err:
                return lines
    except Exception:
        pass
    return [art.c("\x1b[0;36m", art.DIVE)]


def is_dangerous(command):
    return any(re.search(p, command, re.IGNORECASE) for p in DANGER)


def run_hook():
    """Claude Code PreToolUse hook: read a tool call on stdin, block if dangerous."""
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    command = (data.get("tool_input") or {}).get("command", "")
    if not is_dangerous(command):
        sys.exit(0)  # nothing dangerous -> let it through
    out = keeper_visual() + art.denied_block(command)
    print("\n".join(out), file=sys.stderr)
    sys.exit(2)  # exit 2 = block the tool call, stderr becomes the reason


# A scripted mix of safe + dangerous commands for `keeper --simulate`
SAMPLE_RUN = [
    "npm install",
    "git status",
    "rm -rf ./build",
    "chmod 777 secrets.env",
    "python train.py",
    "git push --force origin main",
]


def simulate(args):
    """Mimic Claude Code's permission flow locally, no Claude Code required."""
    cmds = SAMPLE_RUN if args.simulate == "__REEL__" else [args.simulate]
    for command in cmds:
        print(art.c("\x1b[1;37m", "\n  ● Claude wants to run a command:"))
        print(art.c("\x1b[0;33m", f"      $ {command}"))
        print(art.c("\x1b[0;90m", "      [PreToolUse hook → keeper] inspecting…"))
        time.sleep(0.5)
        if is_dangerous(command):
            for line in keeper_visual():
                print(line)
            for line in art.denied_block(command):
                print(line)
            print(art.c("\x1b[1;31m",
                        "      ✗ BLOCKED (hook exit 2) — Claude will not run it."))
        else:
            print(art.c("\x1b[0;32m",
                        "      ✓ allowed (hook exit 0) — command runs normally."))
        time.sleep(0.4)
    print()


def demo(args):
    """Render the same image in all three styles, stacked, for comparison."""
    path, label = pool.pick(args.dir)
    if not path:
        print("no images in the pool — add one with `keeper --add IMG`, "
              "or pass --dir FOLDER")
        return
    print(art.c("\x1b[1;37m", f"\n  comparing styles for: {path}"))
    if args.crop:
        print(art.c("\x1b[0;90m", "  (center-cropped)"))
    for style in ("color", "ascii", "mono"):
        print(art.c("\x1b[1;36m", f"\n  ── {style} " + "─" * 40))
        lines, err = render(path, args.width, style, args.crop)
        if err:
            print(art.c("\x1b[0;90m", f"  ({err})"))
            continue
        print("\n".join(lines))
    print()
    for line in art.denied_block():
        print(line)
    print()


def show(args):
    """Render a random image from the pool (or the ASCII keeper) + denial."""
    animate = not args.no_anim
    print("\x1b[2J\x1b[H", end="")
    if animate:
        for _ in range(6):
            print(art.c("\x1b[0;31m", "  \x1b[2K" + art.glitch_bar()), end="\r")
            time.sleep(0.05)
        print("\x1b[2K", end="")

    lines = None
    if not args.drawn:
        path, label = pool.pick(args.dir)
        if path:
            lines, err = render(path, args.width, args.style, args.crop)
            if err:
                print(art.c("\x1b[0;90m", f"  ({err})"))
    if lines:
        print("\n".join(lines))
    else:
        print(art.c("\x1b[0;36m", art.DIVE))

    print()
    for line in art.denied_block():
        art.typewriter(line, animate=animate)
    print()


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="keeper",
        description="A goalkeeper who denies your terminal access. "
                    "Renders a random image from a folder as terminal pixels.")
    ap.add_argument("-d", "--dir", help="folder to pull a random image from")
    ap.add_argument("-s", "--style", choices=["color", "ascii", "mono"],
                    default="ascii",
                    help="render style: color (photo-like), ascii (colored "
                         "characters, default), mono (green phosphor)")
    ap.add_argument("-w", "--width", type=int, default=90,
                    help="render width in characters (default: 90)")
    ap.add_argument("--crop", dest="crop", action="store_true", default=True,
                    help="center-crop to the subject (on by default)")
    ap.add_argument("--no-crop", dest="crop", action="store_false",
                    help="render the full frame instead of center-cropping")
    ap.add_argument("--drawn", action="store_true",
                    help="force the built-in hand-drawn ASCII keeper")
    ap.add_argument("--no-anim", action="store_true", help="disable animation")
    ap.add_argument("--hook", action="store_true",
                    help="run as a Claude Code PreToolUse hook (reads JSON stdin)")
    ap.add_argument("--simulate", nargs="?", const="__REEL__", metavar="COMMAND",
                    help="mimic Claude's permission flow locally (no Claude Code "
                         "needed). Pass a command, or leave blank for a demo reel.")
    ap.add_argument("--install-hook", action="store_true",
                    help="wire keeper into Claude Code (writes settings.json)")
    ap.add_argument("--uninstall-hook", action="store_true",
                    help="remove keeper's hook from Claude Code")
    ap.add_argument("--project", action="store_true",
                    help="with --install/uninstall-hook: use ./.claude "
                         "instead of the user-level ~/.claude")
    ap.add_argument("--add", metavar="IMAGE",
                    help="copy an image into ~/.keeper/images (the random pool)")
    ap.add_argument("--demo", action="store_true",
                    help="render one image in all three styles, stacked")
    ap.add_argument("--list", action="store_true",
                    help="list the images in the current pool and exit")
    args = ap.parse_args(argv)

    if args.hook:
        return run_hook()

    if args.install_hook:
        return install_hook(args)
    if args.uninstall_hook:
        return uninstall_hook(args)

    if args.simulate is not None:
        simulate(args)
        return 0

    if args.add:
        dest = pool.add_to_user_pool(args.add)
        print(f"added -> {dest}")
        return 0

    if args.list:
        imgs, label = pool.resolve_pool(args.dir)
        print(f"pool: {label}  ({len(imgs)} image(s))")
        for f in imgs:
            print(f"  {f}")
        return 0

    if args.demo:
        demo(args)
        return 0

    show(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
