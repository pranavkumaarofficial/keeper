"""Find the pool of images and pick one at random.

Resolution order (first non-empty wins):
  1. an explicit --dir passed on the command line
  2. the $KEEPER_IMAGES environment variable
  3. ~/.keeper/images   (your personal drop folder)
  4. the sample images bundled with the package

So the usual flow is: point $KEEPER_IMAGES at a folder once (or drop files in
~/.keeper/images), then just run `keeper` with no arguments.
"""
import os
import random
from pathlib import Path

try:
    from importlib.resources import files as _res_files  # py3.9+
except ImportError:  # pragma: no cover
    _res_files = None

EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
USER_DIR = Path.home() / ".keeper" / "images"


def _images_in(path):
    p = Path(path).expanduser()
    if not p.is_dir():
        return []
    return sorted(f for f in p.iterdir()
                  if f.is_file() and f.suffix.lower() in EXTS)


def _bundled_images():
    if _res_files is None:
        return []
    try:
        root = _res_files("keeper") / "images"
        return sorted(f for f in root.iterdir()
                      if f.suffix.lower() in EXTS)
    except Exception:
        return []


def resolve_pool(explicit_dir=None):
    """Return (list_of_images, source_label)."""
    if explicit_dir:
        return _images_in(explicit_dir), f"--dir {explicit_dir}"
    env = os.environ.get("KEEPER_IMAGES")
    if env:
        imgs = _images_in(env)
        if imgs:
            return imgs, f"$KEEPER_IMAGES ({env})"
    imgs = _images_in(USER_DIR)
    if imgs:
        return imgs, str(USER_DIR)
    return _bundled_images(), "bundled samples"


def pick(explicit_dir=None):
    """Return (path_or_None, source_label)."""
    pool, label = resolve_pool(explicit_dir)
    if not pool:
        return None, label
    return str(random.choice(pool)), label


def add_to_user_pool(src):
    """Copy an image into ~/.keeper/images so it joins the random rotation."""
    import shutil
    src = Path(src).expanduser()
    if not src.is_file():
        raise FileNotFoundError(src)
    USER_DIR.mkdir(parents=True, exist_ok=True)
    dest = USER_DIR / src.name
    shutil.copy2(src, dest)
    return dest
