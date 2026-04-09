"""DEAL.md reader/writer.

Uses python-frontmatter for YAML frontmatter + body separation.
Thesis is stored in the markdown body (not in frontmatter) because
multiline YAML strings are fragile.
"""

from pathlib import Path

import frontmatter

from diligent.helpers.io import atomic_write
from diligent.state.models import DealFile


def read_deal(path: Path) -> DealFile:
    """Read DEAL.md into a DealFile dataclass.

    Extracts structured fields from YAML frontmatter and thesis
    from the markdown body.
    """
    post = frontmatter.load(str(path))
    meta = post.metadata

    return DealFile(
        deal_code=str(meta.get("deal_code", "")),
        target_legal_name=str(meta.get("target_legal_name", "")),
        target_common_name=str(meta.get("target_common_name", "")),
        deal_stage=str(meta.get("deal_stage", "")),
        loi_date=str(meta.get("loi_date", "")),
        principal=str(meta.get("principal", "")),
        principal_role=str(meta.get("principal_role", "")),
        seller=str(meta.get("seller", "")),
        broker=str(meta.get("broker", "")),
        thesis=post.content.strip(),
        workstreams=meta.get("workstreams", []) or [],
    )


def write_deal(path: Path, deal: DealFile) -> None:
    """Write a DealFile to DEAL.md using atomic_write.

    Frontmatter contains structured fields; body contains thesis prose.
    Validates output by re-parsing.
    """
    post = frontmatter.Post(content=deal.thesis)
    post.metadata["deal_code"] = deal.deal_code
    post.metadata["target_legal_name"] = deal.target_legal_name
    post.metadata["target_common_name"] = deal.target_common_name
    post.metadata["deal_stage"] = deal.deal_stage
    post.metadata["loi_date"] = deal.loi_date
    post.metadata["principal"] = deal.principal
    post.metadata["principal_role"] = deal.principal_role
    post.metadata["seller"] = deal.seller
    post.metadata["broker"] = deal.broker
    post.metadata["workstreams"] = deal.workstreams

    content = frontmatter.dumps(post) + "\n"

    def validate(c: str) -> bool:
        """Re-parse and verify key fields survived."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(c)
            tmp = Path(f.name)
        try:
            reread = read_deal(tmp)
            return (
                reread.deal_code == deal.deal_code
                and reread.thesis == deal.thesis
            )
        finally:
            tmp.unlink(missing_ok=True)

    atomic_write(path, content, validate_fn=validate)
