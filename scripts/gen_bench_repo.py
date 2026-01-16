from __future__ import annotations

import argparse
from pathlib import Path


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")


def gen_repo(out_dir: Path, *, n_concepts: int) -> Path:
    repo = out_dir.resolve()
    _write(
        repo / "ontology" / "manifest.yaml",
        "\n".join(
            [
                "rocs:",
                "  layer: core",
                '  id: "bench.core"',
                '  version: "0.0.0"',
                '  created: "2026-01-01"',
                "",
            ]
        ),
    )
    _write(repo / "ontology" / "src" / "system4d.yaml", "system4d: {}\n")

    _write(
        repo / "ontology" / "src" / "reference" / "relations" / "is_a.md",
        "\n".join(
            [
                "---",
                "ont:",
                '  id: "core.rel.is_a"',
                "  type: relation",
                '  labels: ["is_a"]',
                '  description: "taxonomy"',
                "  group: taxonomy",
                "  characteristics:",
                "    transitive: true",
                "    symmetric: false",
                "---",
                "",
                "# is_a",
                "",
                "## Definition",
                "taxonomy",
                "",
                "## Domain / Range",
                "- Domain: subtype concept",
                "- Range: supertype concept",
                "",
            ]
        ),
    )

    for i in range(1, n_concepts + 1):
        cid = f"core.Bench{i:04d}"
        rels = []
        if i > 1:
            rels = ["  relations:", "    - type: is_a", f'      target: "core.Bench{i-1:04d}"']
        else:
            rels = ["  relations: []"]
        _write(
            repo / "ontology" / "src" / "reference" / "concepts" / f"{cid}.md",
            "\n".join(
                [
                    "---",
                    "ont:",
                    f'  id: "{cid}"',
                    "  type: concept",
                    f'  labels: ["Bench{i:04d}"]',
                    f'  description: "bench concept {i}"',
                    *rels,
                    "  examples:",
                    '    - "example"',
                    "  anti_examples:",
                    '    - "anti-example"',
                    "---",
                    "",
                    f"# {cid}",
                    "",
                    "## Definition",
                    f"bench concept {i}",
                    "",
                ]
            ),
        )

    return repo


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, help="output directory for the synthetic repo")
    p.add_argument("--n-concepts", type=int, default=200, help="number of concept docs to generate")
    args = p.parse_args(argv)

    out_dir = Path(args.out)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"--out must be empty or non-existent: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    gen_repo(out_dir, n_concepts=int(args.n_concepts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

