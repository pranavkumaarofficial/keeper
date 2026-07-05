"""ASCII art, the denied screen, and terminal helpers."""
import os
import sys
import time
import random

RESET = "\x1b[0m"
NO_COLOR = os.environ.get("NO_COLOR")


def c(code, s):
    """Colorize unless NO_COLOR is set."""
    return s if NO_COLOR else f"{code}{s}{RESET}"


# Hand-drawn full-stretch dive, zero dependencies. Used when there is no image
# pool, when --ascii is passed, and inside the Claude Code hook.
DIVE = r"""
                                       .-.
                                      (   )  . o O
                                       '-'  '
                                    .:'
                         _..--''''--:.._
                    _.-''              '#=>
               _.-''    .------.        '
           _.-''       ( >  <  )         '.
       _.-''            '--,,--'   #1      '.
     ((            .:''       ''::._   VOZINHA )
       '=..__   .:'                     ''--'
             ''--::.._______________..--''
                  /   /        \   \
                 /   /          \   \
                '   '            '   '
"""


def denied_block(command=None):
    """The ACCESS DENIED text lines."""
    cmd_line = f"  $ {command}" if command else "  $ sudo ./deploy.sh"
    return [
        c("\x1b[1;31m", "  ┌──────────────────────────────────────────────┐"),
        c("\x1b[1;31m", "  │  ⛔  ACCESS DENIED — PERMISSION REQUIRED       │"),
        c("\x1b[1;31m", "  └──────────────────────────────────────────────┘"),
        "",
        c("\x1b[0;33m", cmd_line),
        c("\x1b[0;31m", "  keeper: SHOT BLOCKED. request denied at the line."),
        c("\x1b[0;90m", "  reason: the goalkeeper dove full-stretch. no way through."),
        "",
        c("\x1b[0;32m", "  saves this session ... 18 / 23   (.782)"),
        c("\x1b[0;37m", "  authorized by ...... nobody. he denies everyone."),
        "",
        c("\x1b[1;37m", "  hint: rephrase the command, or take it to the spot."),
    ]


def typewriter(text, delay=0.012, animate=True):
    if not animate:
        print(text)
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay if ch != "\n" else delay * 4)
    print()


def glitch_bar(width=50):
    return "".join(random.choice("▓▒░█▄▀") for _ in range(width))
