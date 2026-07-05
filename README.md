# keeper

A terminal tribute to Vozinha -- the 40-year-old Cape Verde goalkeeper who went viral at the 2026 World Cup for denying everyone. Spain, Messi, all of them. Blocked.

`keeper` renders Vozinha (or any image you throw at it) as ASCII art in your terminal, then slams an `ACCESS DENIED` screen. Because that's what keepers do.

It also works as a Claude Code hook that blocks dangerous shell commands before they run. Vozinha doesn't care who you are. He dives full-stretch and denies you.

<!-- screenshots go here -->

## Install

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

## Claude Code hook

This is the real use case. Keeper runs as a PreToolUse hook in Claude Code. Before Claude executes a shell command, Vozinha inspects it. If it matches a dangerous pattern -- `rm -rf`, force-push to main, `chmod 777`, fork bombs, `DROP TABLE` -- the keeper dives in and blocks it. Exit code 2. Command denied. Safe commands pass through untouched.

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

## About

Built as a fun weekend project after watching Vozinha deny everything at the 2026 World Cup. The man is 40 years old and he's out there making saves that have no business being made.

This is a tribute. Nothing official, just a fan who thought it would be funny to have a goalkeeper blocking your terminal commands.

## License

MIT
