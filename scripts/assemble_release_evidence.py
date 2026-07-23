from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from model_modding.builds import canonical_json_bytes
from model_modding.evidence_comparison import build_compatibility_matrix, matrix_markdown
from model_modding.release_pipeline import (
    build_pr_summary,
    check_release_readiness,
    readiness_markdown,
    write_aggregate,
)


def read_manifest(directory: Path) -> dict:
    return json.loads((directory / "manifest.json").read_text(encoding="utf-8"))


def target_key(manifest: dict) -> str:
    provider = str(manifest["runtime"]["provider"]).casefold()
    models = list(manifest["runtime"].get("requested_models", []))
    if len(models) != 1:
        raise ValueError(f"Release evidence bundle must identify exactly one requested model: {manifest['evidence_digest']}")
    return f"{provider}/{models[0]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--evidence-root", type=Path, default=Path("evidence/release-candidate"))
    parser.add_argument("--output", type=Path, default=Path("build/release-candidate"))
    parser.add_argument("--minimum-repetitions", type=int, default=3)
    parser.add_argument("--minimum-cases", type=int, default=40)
    args = parser.parse_args()

    root = args.root.resolve()
    evidence_root = args.evidence_root if args.evidence_root.is_absolute() else root / args.evidence_root
    output = args.output if args.output.is_absolute() else root / args.output
    bundles = sorted({path.parent for path in evidence_root.rglob("manifest.json")})
    if not bundles:
        raise SystemExit(f"No release-candidate evidence bundles found under {evidence_root}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    aggregate_directory, aggregate = write_aggregate(
        root,
        bundles,
        output / "aggregate",
        minimum_repetitions=args.minimum_repetitions,
        require_zero_critical=True,
    )

    representatives = {}
    for bundle in bundles:
        manifest = read_manifest(bundle)
        key = target_key(manifest)
        current = representatives.get(key)
        if current is None or manifest["created_at"] < current[0]["created_at"]:
            representatives[key] = (manifest, bundle)
    representative_paths = [representatives[key][1] for key in sorted(representatives)]
    matrix = build_compatibility_matrix(root, representative_paths)
    matrix_directory = output / "matrix"
    matrix_directory.mkdir()
    (matrix_directory / "matrix.json").write_bytes(canonical_json_bytes(matrix))
    (matrix_directory / "matrix.md").write_text(matrix_markdown(matrix), encoding="utf-8", newline="\n")

    readiness = check_release_readiness(
        root,
        aggregate_directory / "aggregate.json",
        matrix_directory / "matrix.json",
        minimum_repetitions=args.minimum_repetitions,
        minimum_cases=args.minimum_cases,
    )
    readiness_directory = output / "readiness"
    readiness_directory.mkdir()
    (readiness_directory / "readiness.json").write_bytes(canonical_json_bytes(readiness))
    (readiness_directory / "readiness.md").write_text(readiness_markdown(readiness), encoding="utf-8", newline="\n")

    summary = build_pr_summary(matrix=matrix, aggregate=aggregate, readiness=readiness)
    (output / "release-summary.md").write_text(summary, encoding="utf-8", newline="\n")
    print(output / "release-summary.md")
    return 0 if readiness["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
