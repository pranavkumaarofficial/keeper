# keeper

[![PyPI](https://img.shields.io/pypi/v/vozinha-keeper?color=brightgreen&label=PyPI&v=1)](https://pypi.org/project/vozinha-keeper/)
[![Python](https://img.shields.io/pypi/pyversions/vozinha-keeper?v=1)](https://pypi.org/project/vozinha-keeper/)
[![Downloads](https://img.shields.io/pypi/dm/vozinha-keeper?color=blue&v=1)](https://pypi.org/project/vozinha-keeper/)
[![Publish](https://github.com/pranavkumaarofficial/keeper/actions/workflows/publish.yml/badge.svg)](https://github.com/pranavkumaarofficial/keeper/actions/workflows/publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<img width="389" height="397" alt="image" src="https://github.com/user-attachments/assets/aa60a4f7-8267-41db-a530-c539d7e5dba2" />

A terminal tribute to Vozinha -- the 40-year-old Cape Verde goalkeeper who went viral at the 2026 World Cup for denying everyone (Spain, Messi, all of them)
Turned away at the line. Now he does the same thing to Claude Code.

`keeper` renders Vozinha (or any image you throw at it) as ASCII art in your terminal, then slams up an `ACCESS DENIED` screen. That's the joke. Literally he "blocks" the command like how he blocked the goals.

But the real reason it exists: it plugs into **Claude Code** as a hook. Before Claude runs a shell command, Vozinha inspects it. `rm -rf`, force-push to main, `chmod 777`, a fork bomb -- he dives full-stretch and blocks it. Exit code 2, command denied. Your safe commands stroll right through. Nobody gets past him lol!

### The story in numbers

At 40 years old, Vozinha saved all **7** of Spain's shots on target in a 0-0
draw (Cape Verde ranked 67th, Spain 2nd), kept another clean sheet against
Saudi Arabia, then made **8** saves against Messi's Argentina in the Round of
32. He finished the tournament with an **.782** save rate (18 saves from 23
shots on target), and Cape Verde never lost a match inside 90 minutes. He
became the oldest player ever to appear in a nation's World Cup debut, and the
third-oldest goalkeeper to keep a World Cup clean sheet, after Peter Shilton
and Dino Zoff.

<img width="960" height="1200" alt="image" src="https://github.com/user-attachments/assets/8a7ad291-6d2d-4476-9f78-d53da17823bc" />

## The data behind it

I got curious about *why* 2026 has been such a goalkeeper's World Cup, so I
built a small Monte Carlo model I call the **Siege Curve**. Short version: the
48-team format produces roughly **3x** the goalkeeper "siege games" (8+ saves)
of a 32-team one, even though the field only grew by 50%. Half of that is more
matches; the other half is that each game is now more lopsided.

- Model + figures: [`analysis/siege_curve.py`](analysis/siege_curve.py)
- The human story: [Medium — the Vozinha article](ADD_MEDIUM_LINK_1)
- The data-science write-up: [Medium — the Siege Curve](ADD_MEDIUM_LINK_2)

Run it yourself:

    python analysis/siege_curve.py

<img width="1659" height="1019" alt="image" src="https://github.com/user-attachments/assets/d7921ff1-c2c5-47f4-a913-6ba9713ca7ff" />

<img width="1659" height="1019" alt="image" src="https://github.com/user-attachments/assets/99d2680b-1b04-4325-a915-19db0bd4717f" />

## CLI Install

```
pip install vozinha-keeper
```

## Usage

```bash
keeper                        # ASCII art, center-cropped at width 90, + ACCESS DENIED
keeper --style color          # truecolor half-block, looks like a photo
keeper --style mono           # green phosphor retro terminal
keeper --no-crop              # render the full frame instead of cropping
keeper -w 120                 # wider render
keeper --demo                 # compare all 3 styles side by side
```

Works out of the box. Ships with bundled sample images so there's something to render on a fresh install.

## Add your own images

```bash
keeper --add some_photo.jpg          # copies into ~/.keeper/images
export KEEPER_IMAGES=~/Pictures/vozinha   # or point at a whole folder
keeper --dir ~/Pictures/keepers      # one-off folder
```

It picks a random image from the pool each run. The pool checks (in order): `--dir` flag, `$KEEPER_IMAGES` env var, `~/.keeper/images`, bundled samples.

## Blocking Claude Code (the whole point)

This is what keeper is actually for. It runs as a PreToolUse hook in Claude Code, so it stands between Claude and your shell. Every time Claude wants to run a command, Vozinha reads it first. Match a dangerous pattern -- `rm -rf`, force-push to main, `chmod 777`, a fork bomb, `DROP TABLE` -- and the keeper dives in. Exit code 2. Command denied, and the AI gets the ACCESS DENIED screen instead of your filesystem. Safe commands pass through untouched, no ceremony.

Think of it as a last line of defence for the 2am moment when you've told Claude to "just clean up the repo" and you're not watching closely.

### One-command setup

```bash
keeper --install-hook          # writes to ~/.claude/settings.json
keeper --install-hook --project   # or ./.claude/settings.json for this repo only
```

Remove it:

```bash
keeper --uninstall-hook
```

### Try it locally without Claude Code

```bash
keeper --simulate                      # demo reel: safe + dangerous commands
keeper --simulate "rm -rf ./build"     # blocked
keeper --simulate "npm test"           # allowed
```

### Manual hook setup

If you prefer to set it up yourself, add this to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"/path/to/python\" -m keeper --hook"
          }
        ]
      }
    ]
  }
}
```

Find your python path with `python -c "import sys; print(sys.executable)"`.

## What gets blocked

The danger patterns live in `keeper/cli.py`. Current list:

- `rm -rf` (recursive force delete)
- `sudo rm`
- `git push --force` to main/master
- `chmod 777`
- `mkfs` (format disk)
- `dd if=` (raw disk write)
- Redirects to `/dev/sd*`
- Fork bombs
- `DROP TABLE`

Edit the `DANGER` list to add your own.

## Render styles

- **ascii** (default) -- brightness-ramp characters tinted with pixel color. Clean subjects look great. This is what the hook uses.
- **color** -- truecolor half-block. Two pixels per character cell. Busy photos with lots of detail work best here.
- **mono** -- green phosphor brightness ramp. Retro CRT look. Works on any terminal.

Center-crop at width 90 is the default -- the sweet spot for most images. Pass `--no-crop` to render the full frame, or `-w` to change the width.

## Known issues

**Rendering quality depends on your terminal, and that needs work.** The output is tuned for a truecolor terminal (Windows Terminal, iTerm2, most modern Linux terminals) at a decent width. On terminals without 24-bit color, narrower than 90 columns, or with unusual font aspect ratios, the render can wrap, wash out, or look squashed. Right now there's no auto-detection -- keeper just assumes you've got the good setup.

This is the main thing I'd like fixed. If you want to make the render adapt to different terminals -- detecting truecolor vs. 256-color vs. mono, capping width to the actual terminal size, handling font aspect ratio -- **please open a PR.** That's exactly the kind of contribution this project needs. Bug reports about how it looks on your specific terminal (with a screenshot) are welcome too.

## About

A weekend project made after watching Vozinha deny the entire World Cup. The man is 40 years old and he was out there pulling off saves that had no business being made, against players half his age. Least I could do was put him in front of my terminal too.

Nothing official. Just a fan who thought it'd be funny -- and then kind of useful -- to have a Cape Verdean goalkeeper standing between an AI and my filesystem. Obrigado, Vozinha.

## License

MIT
