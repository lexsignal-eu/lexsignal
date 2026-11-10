#!/usr/bin/env python3
"""Build and validate the single public LexSignal Pages release artifact.

No network requests, credentials, customer data or production writes. This script
is used identically in pull-request previews and the production Pages pipeline.
A release manifest fingerprints exact generated files; the manifest intentionally
does not reference itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from build_agent_feed import build_documents, openapi_spec, write_json
from knowledge_index import build_index
from research_demo import build_example_research


PAGES = (
    "index.html",
    "landing.html",
    "workspace.html",
    "documents.html",
    "global-signals.html",
    "regulatory-library.html",
    "agent-access.html",
    "llms.txt",
)
DATA_FILES = (
    "data/regulatory_snapshot.json",
    "data/global_signals.json",
    "data/regulatory_library.json",
    "data/example_profile_lenses.json",
)
ASSET_DIRS = ("brand", "geo")
RELEASE_SCHEMA = "lexsignal-static-release-v1"


class SiteBuildError(ValueError):
    """A release artifact fails a quality or safety gate."""


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _hash(data):
    return hashlib.sha256(data).hexdigest()


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        for key in ("href", "src"):
            if key in data and data[key]:
                self.links.append((tag, key, data[key]))


def validate_local_links(site_root):
    """Fail the artifact if an HTML page references a missing local asset.

    External sources are not asserted to be reachable by this offline check.
    JavaScript links and references escaping the site root are disallowed.
    """
    root = Path(site_root).resolve()
    checked = 0
    for page in sorted(root.glob("*.html")):
        parser = _LinkParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for tag, attr, value in parser.links:
            value = value.strip()
            if not value or value.startswith("#"):
                continue
            parsed = urlsplit(value)
            if parsed.scheme in ("http", "https", "mailto", "tel") or parsed.netloc:
                continue
            if parsed.scheme:
                raise SiteBuildError(f"Disallowed link protocol in {page.name}: {value[:100]}")
            pathname = unquote(parsed.path)
            if not pathname:
                continue
            if pathname.startswith("/"):
                # The public Pages project is published under /lexsignal/.
                if pathname.startswith("/lexsignal/"):
                    pathname = pathname[len("/lexsignal/"):]
                    target = root / pathname
                elif pathname == "/lexsignal":
                    target = root / "index.html"
                else:
                    raise SiteBuildError(f"Unexpected root-absolute link in {page.name}: {value[:100]}")
            else:
                target = page.parent / pathname
            resolved = target.resolve()
            if not resolved.is_relative_to(root):
                raise SiteBuildError(f"Link escapes site root in {page.name}: {value[:100]}")
            if resolved.is_dir():
                resolved = resolved / "index.html"
            if not resolved.is_file():
                raise SiteBuildError(f"Missing local target in {page.name}: {value[:100]}")
            checked += 1
    return checked


def build_site(repository, destination, revision="unknown"):
    root = Path(repository).resolve()
    output = Path(destination).resolve()
    if output == root or output.is_relative_to(root) and output == root / "data":
        raise SiteBuildError("Refusing to overwrite repository inputs")
    if output.exists() and any(output.iterdir()):
        raise SiteBuildError("Output directory is not empty; start with a fresh artifact")
    output.mkdir(parents=True, exist_ok=True)

    for relative in PAGES + DATA_FILES:
        src = root / relative
        if not src.is_file():
            raise SiteBuildError(f"Required release input missing: {relative}")
        dst = output / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)

    for folder in ASSET_DIRS:
        source = root / folder
        if not source.is_dir():
            raise SiteBuildError(f"Required assets folder missing: {folder}")
        shutil.copytree(source, output / folder)

    snapshot = _json(root / "data/regulatory_snapshot.json")
    library = _json(root / "data/regulatory_library.json")
    registry = _json(root / "data/source_registry.json")
    lenses = _json(root / "data/example_profile_lenses.json")

    feeds = build_documents(snapshot)
    index = build_index(library, snapshot, registry)
    api = output / "api/v1"
    for name, document in feeds.items():
        write_json(api / name, document)
    write_json(api / "openapi.json", openapi_spec())
    write_json(api / "knowledge.json", index)
    research = build_example_research(library, lenses, index)
    write_json(output / "data/example_research.json", research)

    # Validate relationships across independently generated public exports.
    if feeds["status.json"]["recordCount"] != feeds["updates.json"]["count"]:
        raise SiteBuildError("RSS status record count differs from the published feed")
    if index["counts"]["rssPublications"] != len(snapshot["records"]):
        raise SiteBuildError("Knowledge index must reflect the full committed snapshot")
    if index["counts"]["legalInstruments"] != len(library["acts"]):
        raise SiteBuildError("Knowledge index legal reference count differs from curated library")

    links_checked = validate_local_links(output)
    files = {}
    for path in sorted(output.rglob("*")):
        if path.is_file():
            files[path.relative_to(output).as_posix()] = _hash(path.read_bytes())
    manifest = {
        "schema": RELEASE_SCHEMA,
        "sourceRevision": revision,
        "sourceSnapshotGeneratedAt": snapshot["generatedAt"],
        "sourceSnapshotSHA256": _hash((root / "data/regulatory_snapshot.json").read_bytes()),
        "artifactFileCount": len(files),
        "localLinksValidated": links_checked,
        "dataStatus": "public_research_preview_unreviewed_rss",
        "counts": index["counts"],
        "files": files,
    }
    write_json(api / "build-manifest.json", manifest)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=".")
    parser.add_argument("--out", required=True)
    parser.add_argument("--revision", default="unknown")
    args = parser.parse_args(argv)
    manifest = build_site(args.repository, args.out, args.revision)
    print(
        "LexSignal release artifact:",
        manifest["artifactFileCount"], "files;",
        manifest["localLinksValidated"], "internal links validated;",
        "source:", manifest["sourceSnapshotGeneratedAt"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
