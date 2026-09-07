from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


REQUIRED_FIELDS = ("seq", "title", "summary", "tags", "posted_at")


class PostParseError(ValueError):
    """포스트 입력 형식이 올바르지 않을 때 발생한다."""


@dataclass(frozen=True)
class Post:
    seq: int
    title: str
    summary: str
    tags: tuple[str, ...]
    posted_at: str
    filename: str
    body: str

    def to_dict(self) -> dict[str, Any]:
        values = asdict(self)
        values.pop("body")
        values["tags"] = list(self.tags)
        return values


def _read_front_matter(path: Path) -> tuple[dict[str, Any], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise PostParseError(f"{path}: YAML front matter가 없습니다.")

    try:
        end_index = lines.index("---", 1)
    except ValueError as error:
        raise PostParseError(
            f"{path}: YAML front matter가 닫히지 않았습니다."
        ) from error

    front_matter_text = "\n".join(lines[1:end_index])
    try:
        metadata = yaml.safe_load(front_matter_text) or {}
    except yaml.YAMLError as error:
        raise PostParseError(
            f"{path}: YAML front matter를 읽을 수 없습니다."
        ) from error

    if not isinstance(metadata, dict):
        raise PostParseError(
            f"{path}: YAML front matter는 mapping이어야 합니다."
        )

    body = "\n".join(lines[end_index + 1:]).strip()
    return metadata, body


def _require_string(metadata: dict[str, Any], field: str, path: Path) -> str:
    value = metadata.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PostParseError(
            f"{path}: '{field}'는 비어 있지 않은 문자열이어야 합니다."
        )
    return value


def _normalize_posted_at(value: Any, path: Path) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        return value
    raise PostParseError(f"{path}: 'posted_at'은 날짜 문자열이어야 합니다.")


def _build_post(metadata: dict[str, Any], body_path: Path, body: str) -> Post:
    missing = [field for field in REQUIRED_FIELDS if field not in metadata]
    if missing:
        fields = ", ".join(missing)
        raise PostParseError(
            f"{body_path}: 필수 메타데이터가 없습니다: {fields}"
        )

    seq = metadata["seq"]
    if isinstance(seq, bool) or not isinstance(seq, int):
        raise PostParseError(f"{body_path}: 'seq'는 정수여야 합니다.")

    tags = metadata["tags"]
    if not isinstance(tags, list) or not all(
        isinstance(tag, str) and tag for tag in tags
    ):
        raise PostParseError(
            f"{body_path}: 'tags'는 비어 있지 않은 "
            "문자열 목록이어야 합니다."
        )

    return Post(
        seq=seq,
        title=_require_string(metadata, "title", body_path),
        summary=_require_string(metadata, "summary", body_path),
        tags=tuple(tags),
        posted_at=_normalize_posted_at(metadata["posted_at"], body_path),
        filename=body_path.name,
        body=body,
    )


def parse(file_path: str | Path) -> Post:
    """포스트 파일을 읽어 검증된 메타데이터와 본문을 반환한다.
    """
    path = Path(file_path)
    metadata, body = _read_front_matter(path)
    return _build_post(metadata, path, body)


def load_posts(posts_dir: str | Path) -> list[Post]:
    """디렉터리의 Markdown 포스트를 검증하고
    seq 내림차순으로 반환한다.
    """
    paths = sorted(Path(posts_dir).glob("*.md"))
    posts = [parse(path) for path in paths]
    seq_counts: dict[int, int] = {}
    for post in posts:
        seq_counts[post.seq] = seq_counts.get(post.seq, 0) + 1

    duplicates = sorted(seq for seq, count in seq_counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"중복된 포스트 seq가 있습니다: {duplicates}")
    return sorted(posts, key=lambda post: post.seq, reverse=True)
