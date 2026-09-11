#!/usr/bin/env python3
# test_tag_cleanup.py — Tests for the automated tag-cleanup pipeline (F46)
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-09-09
# Updated: 2026-09-09
# Open Source Under MIT license

import json
from unittest.mock import patch

import frontmatter
import pytest

from salasblog2.tag_cleanup import (
    PostSummary,
    TagProposal,
    apply_tag_batch,
    apply_tag_proposal,
    build_proposal,
    has_numeric_tag,
    needs_tag_cleanup,
    promote_recurring_candidates,
    proposals_to_json,
    select_posts_needing_cleanup,
    split_new_tags,
    summaries_to_json,
    summarize_post,
    validate_proposed_tags,
)
from salasblog2.utils import load_curated_tags


def write_post(
    path, tags, title="A Post", body="Some body content here.", tag_review=None
):
    lines = [
        "---",
        f'title: "{title}"',
        f"tags: {json.dumps(tags)}",
        'date: "2020-01-01"',
    ]
    if tag_review is not None:
        lines.append(f'tag_review: "{tag_review}"')
    lines += ["---", body]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class TestHasNumericTag:
    def test_true_when_any_tag_numeric(self):
        assert has_numeric_tag(["ai", "1234"]) is True

    def test_false_when_no_numeric_tags(self):
        assert has_numeric_tag(["ai", "programming"]) is False

    def test_false_for_empty_list(self):
        assert has_numeric_tag([]) is False


class TestNeedsTagCleanup:
    def test_true_for_empty_tags_never_reviewed(self):
        assert needs_tag_cleanup([], reviewed_no_fit=False) is True

    def test_false_for_empty_tags_already_reviewed(self):
        assert needs_tag_cleanup([], reviewed_no_fit=True) is False

    def test_true_for_numeric_tag_even_if_reviewed(self):
        assert needs_tag_cleanup(["1234"], reviewed_no_fit=True) is True

    def test_false_for_clean_tags(self):
        assert needs_tag_cleanup(["ai", "programming"], reviewed_no_fit=False) is False

    def test_true_for_mixed_numeric_and_real(self):
        assert needs_tag_cleanup(["ai", "1234"], reviewed_no_fit=False) is True


class TestSelectPostsNeedingCleanup:
    def test_selects_only_needs_work_posts(self, tmp_path):
        write_post(tmp_path / "a-clean.md", ["ai"])
        write_post(tmp_path / "b-numeric.md", ["1234"])
        write_post(tmp_path / "c-empty.md", [])
        selected = select_posts_needing_cleanup(tmp_path, limit=10)
        names = {p.name for p in selected}
        assert names == {"b-numeric.md", "c-empty.md"}

    def test_skips_empty_tags_already_reviewed_as_no_fit(self, tmp_path):
        write_post(tmp_path / "a-reviewed.md", [], tag_review="no_fit")
        write_post(tmp_path / "b-untouched.md", [])
        selected = select_posts_needing_cleanup(tmp_path, limit=10)
        names = {p.name for p in selected}
        assert names == {"b-untouched.md"}

    def test_still_selects_numeric_tag_even_if_marked_reviewed(self, tmp_path):
        write_post(tmp_path / "a.md", ["1234"], tag_review="no_fit")
        selected = select_posts_needing_cleanup(tmp_path, limit=10)
        assert {p.name for p in selected} == {"a.md"}

    def test_respects_limit(self, tmp_path):
        for i in range(5):
            write_post(tmp_path / f"post-{i}.md", [])
        selected = select_posts_needing_cleanup(tmp_path, limit=2)
        assert len(selected) == 2

    def test_stable_sorted_order(self, tmp_path):
        write_post(tmp_path / "z-post.md", [])
        write_post(tmp_path / "a-post.md", [])
        selected = select_posts_needing_cleanup(tmp_path, limit=10)
        assert [p.name for p in selected] == ["a-post.md", "z-post.md"]


class TestSummarizePost:
    def test_extracts_title_tags_and_excerpt(self, tmp_path):
        path = tmp_path / "post.md"
        write_post(path, ["1234"], title="Robots Are Cool", body="All about robots.")
        summary = summarize_post(path)
        assert summary.filename == "post.md"
        assert summary.title == "Robots Are Cool"
        assert summary.current_tags == ["1234"]
        assert "robots" in summary.excerpt.lower()

    def test_empty_tags_stay_empty(self, tmp_path):
        path = tmp_path / "post.md"
        write_post(path, [])
        summary = summarize_post(path)
        assert summary.current_tags == []


class TestSummariesToJson:
    def test_round_trips_expected_fields(self):
        summaries = [
            PostSummary(
                filename="a.md", title="A", current_tags=["1234"], excerpt="Text."
            )
        ]
        data = json.loads(summaries_to_json(summaries))
        assert data[0]["filename"] == "a.md"
        assert data[0]["current_tags"] == ["1234"]
        assert data[0]["excerpt"] == "Text."


class TestValidateProposedTags:
    def test_passes_through_free_form_tags(self):
        assert validate_proposed_tags(["ai", "blogbridge"]) == ["ai", "blogbridge"]

    def test_drops_numeric_junk(self):
        assert validate_proposed_tags(["ai", "1234"]) == ["ai"]

    def test_drops_empty_strings(self):
        assert validate_proposed_tags(["ai", "", "  "]) == ["ai"]

    def test_dedupes_preserving_order(self):
        assert validate_proposed_tags(["ai", "mars", "ai"]) == ["ai", "mars"]

    def test_empty_list(self):
        assert validate_proposed_tags([]) == []


class TestSplitNewTags:
    def test_curated_new_tags_are_accepted(self):
        accepted, candidates = split_new_tags([], ["robotics"], {"robotics"})
        assert accepted == ["robotics"]
        assert candidates == []

    def test_uncurated_new_tags_become_candidates(self):
        accepted, candidates = split_new_tags([], ["boston-dynamics"], {"robotics"})
        assert accepted == []
        assert candidates == ["boston-dynamics"]

    def test_ignores_tags_already_on_the_post(self):
        accepted, candidates = split_new_tags(["technology"], ["technology"], set())
        assert accepted == []
        assert candidates == []


class TestBuildProposal:
    def test_accepts_curated_new_tag(self):
        summary = PostSummary(
            filename="post.md",
            title="Robots Are Cool",
            current_tags=["1234"],
            excerpt="All about robots.",
        )
        proposal = build_proposal(summary, ["robotics"], {"robotics"})

        assert proposal.filename == "post.md"
        assert proposal.title == "Robots Are Cool"
        assert proposal.current_tags == ["1234"]
        assert proposal.proposed_tags == ["robotics"]
        assert proposal.candidate_tags == []

    def test_holds_back_uncurated_new_tag_as_candidate(self):
        summary = PostSummary(
            filename="post.md",
            title="Robots Are Cool",
            current_tags=[],
            excerpt="All about robots.",
        )
        proposal = build_proposal(summary, ["boston-dynamics"], {"robotics"})

        assert proposal.proposed_tags == []
        assert proposal.candidate_tags == ["boston-dynamics"]

    def test_preserves_existing_real_tags_even_if_not_curated(self):
        summary = PostSummary(
            filename="post.md", title="T", current_tags=["blogbridge"], excerpt="e"
        )
        proposal = build_proposal(summary, ["robotics"], {"robotics"})
        assert proposal.proposed_tags == ["blogbridge", "robotics"]

    def test_does_not_duplicate_a_tag_already_present(self):
        summary = PostSummary(
            filename="post.md", title="T", current_tags=["technology"], excerpt="e"
        )
        proposal = build_proposal(
            summary, ["technology", "robotics"], {"technology", "robotics"}
        )
        assert proposal.proposed_tags == ["technology", "robotics"]

    def test_no_fit_when_nothing_proposed(self):
        summary = PostSummary(
            filename="post.md", title="T", current_tags=[], excerpt="e"
        )
        proposal = build_proposal(summary, [], set())
        assert proposal.no_fit is True


class TestPromoteRecurringCandidates:
    def make_hints(self, tmp_path, extra=""):
        path = tmp_path / "tag-hints.md"
        path.write_text(
            "# Curated Tags\n\nrobotics\n" + extra, encoding="utf-8"
        )
        return path

    def make_proposals(self, filenames, tag="mars"):
        return [
            TagProposal(filename=f, title="T", current_tags=[], candidate_tags=[tag])
            for f in filenames
        ]

    def test_ignores_candidates_below_threshold(self, tmp_path):
        path = self.make_hints(tmp_path)
        proposals = self.make_proposals(
            ["a.md", "b.md"]
        )  # 2 < MIN_RECURRENCE_FOR_PROPOSED_TAG
        assert promote_recurring_candidates(proposals, path) == []
        assert "mars" not in path.read_text(encoding="utf-8")

    def test_appends_candidates_meeting_threshold_to_curated_list(self, tmp_path):
        path = self.make_hints(tmp_path)
        proposals = self.make_proposals(["a.md", "b.md", "c.md"])
        added = promote_recurring_candidates(proposals, path)
        assert added == ["mars"]
        assert load_curated_tags(path) == ["robotics", "mars"]

    def test_does_not_duplicate_already_listed_tag(self, tmp_path):
        path = self.make_hints(tmp_path, extra="mars\n")
        proposals = self.make_proposals(["a.md", "b.md", "c.md"])
        assert promote_recurring_candidates(proposals, path) == []


class TestTagProposal:
    def test_no_fit_true_when_no_proposed_tags(self):
        proposal = TagProposal(filename="f.md", title="T", current_tags=[])
        assert proposal.no_fit is True

    def test_no_fit_false_when_tags_proposed(self):
        proposal = TagProposal(
            filename="f.md", title="T", current_tags=[], proposed_tags=["ai"]
        )
        assert proposal.no_fit is False


class TestProposalsToJson:
    def test_round_trips_expected_fields(self):
        proposals = [
            TagProposal(
                filename="a.md",
                title="A",
                current_tags=["1234"],
                proposed_tags=["ai"],
            )
        ]
        data = json.loads(proposals_to_json(proposals))
        assert data[0]["filename"] == "a.md"
        assert data[0]["proposed_tags"] == ["ai"]
        assert data[0]["no_fit"] is False


class TestApplyTagProposal:
    def test_writes_tags_and_preserves_body(self, tmp_path):
        write_post(tmp_path / "post.md", ["1234"], body="Original body text.")
        apply_tag_proposal(tmp_path, "post.md", ["ai", "programming"])

        post = frontmatter.load(tmp_path / "post.md")
        assert post.metadata["tags"] == ["ai", "programming"]
        assert post.content.strip() == "Original body text."

    def test_marks_no_fit_when_tags_end_up_empty(self, tmp_path):
        write_post(tmp_path / "post.md", ["1234"])
        apply_tag_proposal(tmp_path, "post.md", [])

        post = frontmatter.load(tmp_path / "post.md")
        assert post.metadata["tag_review"] == "no_fit"

    def test_clears_no_fit_marker_once_real_tags_applied(self, tmp_path):
        write_post(tmp_path / "post.md", [], tag_review="no_fit")
        apply_tag_proposal(tmp_path, "post.md", ["ai"])

        post = frontmatter.load(tmp_path / "post.md")
        assert "tag_review" not in post.metadata

    def test_raises_if_body_changes_unexpectedly(self, tmp_path):
        write_post(tmp_path / "post.md", ["1234"], body="Original body text.")

        real_load = frontmatter.load
        call_count = {"n": 0}

        def flaky_load(f):
            call_count["n"] += 1
            post = real_load(f)
            if call_count["n"] == 2:
                post.content = "corrupted body"
            return post

        with (
            patch("salasblog2.tag_cleanup.frontmatter.load", side_effect=flaky_load),
            pytest.raises(ValueError, match="body content changed"),
        ):
            apply_tag_proposal(tmp_path, "post.md", ["ai"])


class TestApplyTagBatch:
    def test_applies_multiple_and_skips_flagged(self, tmp_path):
        write_post(tmp_path / "keep.md", ["1234"])
        write_post(tmp_path / "skip.md", ["5678"])

        written = apply_tag_batch(
            tmp_path,
            [
                {"filename": "keep.md", "tags": ["ai"]},
                {"filename": "skip.md", "tags": ["ai"], "skip": True},
            ],
        )

        assert written == ["keep.md"]
        assert frontmatter.load(tmp_path / "keep.md").metadata["tags"] == ["ai"]
        assert frontmatter.load(tmp_path / "skip.md").metadata["tags"] == ["5678"]
