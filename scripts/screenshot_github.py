#!/usr/bin/env python3
"""Screenshot the real GitHub language bar of this repository.

    python scripts/screenshot_github.py
    python scripts/screenshot_github.py --repo quxianp/RAiNBOW_Hello-World

Writes ``assets/rainbow-bar-github.png``.

GitHub ships no public API that returns the rendered bar, and the DOM around it
changes without notice, so this tries a list of selectors and finally falls back
to clipping by the "Languages" heading. GitHub also serves a different page to
logged-out clients, so the script waits for the bar and, failing that, keeps a
full-page screenshot instead.

This is deliberately non-fatal: the acceptance criteria treat
``rainbow-bar-local.png`` as an acceptable substitute, so a Playwright failure
must never fail a build. Exits 0 either way and logs what happened.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "assets" / "rainbow-bar-github.png"

# Ordered most-specific first. Each is tried in turn and the result is size
# checked, because a bare `.Progress` also matches small progress indicators
# elsewhere on the page (a 141-byte capture of one of those was the first
# version of this script's output).
BAR_SELECTORS = [
    "#repository-lang-stats .Progress",
    "div.repository-lang-stats-graph",
    "[data-testid='language-bar']",
    "div.Layout-sidebar .Progress",
    ".Progress[role='progressbar']",
    "svg[aria-label='Repository languages bar']",
]

# A real 600-segment bar rasterises to tens of kilobytes. Anything smaller is a
# degenerate element, not the language bar.
MIN_BYTES = 6000

LOG = logging.getLogger("screenshot_github")


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stdout,
    )


def usable(path: Path) -> bool:
    """A capture is only accepted if it looks like a real bar, not a stub."""
    return path.is_file() and path.stat().st_size >= MIN_BYTES


def discard(path: Path) -> None:
    """Never leave a degenerate image behind for the README to link to."""
    try:
        path.unlink()
    except OSError:
        pass


def clip_from_heading(page, out: Path) -> bool:
    """Last-resort crop: find the 'Languages' heading and clip below it."""
    try:
        heading = page.get_by_text("Languages", exact=True).first
        box = heading.bounding_box()
        if not box:
            return False
        clip = {
            "x": max(box["x"] - 8, 0),
            "y": max(box["y"] - 8, 0),
            "width": box["width"] + 16,
            # The bar plus the legend underneath it.
            "height": box["height"] + 120,
        }
        page.screenshot(path=str(out), clip=clip)
        if usable(out):
            return True
        discard(out)
        return False
    except Exception as exc:  # noqa: BLE001 - any failure is a fallback trigger
        LOG.debug("heading clip failed: %s", exc)
        discard(out)
        return False


def capture(repo: str, out: Path, timeout: int, width: int, height: int) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        LOG.warning("playwright is not installed; skipping the GitHub bar capture")
        return False

    # Do NOT cache-bust this request. An earlier revision appended a query
    # parameter and sent Cache-Control: no-cache through a custom context; GitHub
    # then served an unstyled document (raw "Navigation Menu" markup, 303 KB
    # screenshot of a page with no CSS) and every selector missed. The rendered
    # page may lag the newest push by a few minutes because of the edge cache,
    # which is cosmetic and self-heals on the next run; a blank page is not.
    url = f"https://github.com/{repo}"
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--no-sandbox"])
            try:
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    device_scale_factor=2,
                )
                LOG.info("opening %s", url)
                page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)

                # GitHub computes and injects the language breakdown client
                # side, and to a logged-out client it can take several seconds.
                # Wait for the sidebar to actually fill with language entries
                # rather than sleeping a fixed amount.
                try:
                    page.wait_for_function(
                        "() => document.querySelectorAll('.Layout-sidebar a').length > 50",
                        timeout=timeout * 1000,
                    )
                    LOG.info("language sidebar populated")
                except Exception as exc:  # noqa: BLE001
                    LOG.warning("sidebar did not populate in time: %s", exc)
                page.wait_for_timeout(2000)

                for selector in BAR_SELECTORS:
                    try:
                        element = page.query_selector(selector)
                    except Exception:  # noqa: BLE001
                        element = None
                    if element is None:
                        continue
                    try:
                        element.scroll_into_view_if_needed(timeout=5000)
                        page.wait_for_timeout(500)
                        element.screenshot(path=str(out))
                        if usable(out):
                            LOG.info(
                                "captured language bar via %s (%d bytes)",
                                selector, out.stat().st_size,
                            )
                            return True
                        LOG.info(
                            "selector %s produced only %d bytes; rejecting",
                            selector, out.stat().st_size if out.is_file() else 0,
                        )
                        discard(out)
                    except Exception as exc:  # noqa: BLE001
                        LOG.debug("selector %s failed: %s", selector, exc)
                        discard(out)

                LOG.info("no bar selector produced a usable capture; trying heading clip")
                if clip_from_heading(page, out):
                    LOG.info("captured language bar via heading clip")
                    return True

                # Diagnostic only, and deliberately written outside assets/ so a
                # failed capture can never commit a 300 KB screenshot of the
                # wrong thing into the repository.
                diag = ROOT / ".tmp" / "rainbow-bar-github-fullpage.png"
                diag.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(diag), full_page=False)
                LOG.warning("bar not isolated; saved full page to %s", diag)
                return False
            finally:
                browser.close()
    except Exception as exc:  # noqa: BLE001
        LOG.warning("playwright capture failed: %s", exc)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="quxianp/RAiNBOW_Hello-World")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--timeout", type=int, default=60, help="seconds")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)
    out = Path(args.out)

    ok = capture(args.repo, out, args.timeout, args.width, args.height)
    if ok:
        LOG.info("wrote %s (%d bytes)", out, out.stat().st_size)
    else:
        LOG.warning(
            "no GitHub bar capture; the local render "
            "(assets/rainbow-bar-local.png) remains the reference"
        )
    # Always succeed: a missing browser must not fail the build.
    return 0


if __name__ == "__main__":
    sys.exit(main())
