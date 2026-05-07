from __future__ import annotations

from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest import mock

import yaml

from scripts import build_shadow_dashboard
from scripts import shadow_commit


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_yaml(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


class ShadowCommitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "shadow_assets").mkdir()
        (self.root / "shadow_reviews").mkdir()
        (self.root / "shadow_sessions").mkdir()
        (self.root / "raw-transcripts").mkdir()
        write_text(
            self.root / "raw-transcripts" / "260421.md",
            "Lufttaxis kommen in der breiten Masse an.\nNeue Systeme werten den ländlichen Raum auf.\n---\n- in der breiten Masse\n- aufwerten\n",
        )
        write_text(
            self.root / "shadow_sessions" / "2026-04-21-0934.md",
            textwrap.dedent(
                """
                # Shadow Session

                - source: `{source}`
                - captured_at: `2026-04-21 09:34`
                - status: staged

                ## Raw Transcript
                See source file: `{source}`

                ---

                ## Must Keep Candidates

                - raw: `in der breiten Masse`
                  target: `in der breiten Masse`
                  type: `phrase`
                  english: `among the broad public`
                  transcript_sentence: `Lufttaxis kommen in der breiten Masse an.`
                  collocation: `in der breiten Masse ankommen`

                ## Recommendations

                - raw: `aufwerten`
                  target: `aufwerten`
                  type: `word`
                  english: `upgrade`
                  transcript_sentence: `Neue Systeme werten den ländlichen Raum auf.`
                """
            ).strip().format(source=self.root / "raw-transcripts" / "260421.md"),
        )
        write_yaml(
            self.root / "shadow_assets" / "assets.yaml",
            [
                {
                    "id": "a-2026-04-13-026",
                    "type": "phrase",
                    "title": "in der breiten Masse",
                    "content": "in der breiten Masse",
                    "english": "among the broad public",
                    "collocation": "in der breiten Masse ankommen",
                    "transcript_sentence": "Frueher kam das kaum in der breiten Masse an.",
                    "source_session": "shadow_sessions/2026-04-13-1215.md",
                    "created_at": "2026-04-13",
                    "status": "solid",
                    "priority": "high",
                    "review_count": 4,
                    "reset_count": 1,
                    "last_reviewed_at": "2026-04-20",
                    "mistake_note": None,
                }
            ],
        )
        write_yaml(
            self.root / "shadow_reviews" / "review_state.yaml",
            [
                {
                    "id": "a-2026-04-13-026",
                    "status": "solid",
                    "priority": "high",
                    "review_count": 4,
                    "reset_count": 1,
                    "last_reviewed_at": "2026-04-20",
                    "mistake_note": None,
                }
            ],
        )
        write_text(self.root / "shadow_reviews" / "review_log.md", "# Shadow Review Log\n")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_commit_resets_existing_asset_and_adds_new_one(self) -> None:
        result = shadow_commit.commit_session(
            root=self.root,
            session_path=self.root / "shadow_sessions" / "2026-04-21-0934.md",
            committed_at="2026-04-21 10:00",
        )

        self.assertEqual(result["added_count"], 1)
        self.assertEqual(result["reset_count"], 1)

        assets = yaml.safe_load((self.root / "shadow_assets" / "assets.yaml").read_text(encoding="utf-8"))
        state = yaml.safe_load((self.root / "shadow_reviews" / "review_state.yaml").read_text(encoding="utf-8"))

        self.assertEqual(len(assets), 2)
        self.assertEqual(len(state), 2)

        existing_asset = next(item for item in assets if item["content"] == "in der breiten Masse")
        self.assertEqual(existing_asset["id"], "a-2026-04-13-026")
        self.assertEqual(existing_asset["status"], "new")
        self.assertEqual(existing_asset["priority"], "high")
        self.assertEqual(existing_asset["review_count"], 4)
        self.assertEqual(existing_asset["reset_count"], 2)
        self.assertEqual(existing_asset["transcript_sentence"], "Lufttaxis kommen in der breiten Masse an.")
        self.assertEqual(existing_asset["collocation"], "in der breiten Masse ankommen")

        new_asset = next(item for item in assets if item["content"] == "aufwerten")
        self.assertEqual(new_asset["id"], "a-2026-04-21-027")
        self.assertEqual(new_asset["status"], "new")
        self.assertEqual(new_asset["review_count"], 0)
        self.assertEqual(new_asset["reset_count"], 0)
        self.assertEqual(new_asset["source_session"], "shadow_sessions/2026-04-21-0934.md")

        log_text = (self.root / "shadow_reviews" / "review_log.md").read_text(encoding="utf-8")
        self.assertIn("Added 1 new assets", log_text)
        self.assertIn("Reset 1 existing assets to `new`", log_text)

    def test_commit_refreshes_asset_index(self) -> None:
        shadow_commit.commit_session(
            root=self.root,
            session_path=self.root / "shadow_sessions" / "2026-04-21-0934.md",
            committed_at="2026-04-21 10:00",
        )

        index = yaml.safe_load((self.root / "shadow_assets" / "asset_index.json").read_text(encoding="utf-8"))

        self.assertEqual(index["source"], "shadow_assets/assets.yaml")
        self.assertEqual(index["exact"]["in der breiten masse"], ["a-2026-04-13-026"])
        self.assertEqual(index["exact"]["aufwerten"], ["a-2026-04-21-027"])
        self.assertEqual(index["items"]["a-2026-04-13-026"]["reset_count"], 2)

    def test_commit_resets_existing_asset_when_target_matches_title_or_collocation(self) -> None:
        write_text(
            self.root / "shadow_sessions" / "2026-04-22-0900.md",
            textwrap.dedent(
                """
                # Shadow Session

                - source: `raw-transcripts\\260421.md`
                - captured_at: `2026-04-22 09:00`
                - status: staged

                ## Must Keep Candidates

                - raw: `in der breiten Masse ankommen`
                  target: `in der breiten Masse ankommen`
                  type: `phrase`
                  english: `reach the broad public`
                  transcript_sentence: `Lufttaxis kommen in der breiten Masse an.`
                """
            ).strip(),
        )

        result = shadow_commit.commit_session(
            root=self.root,
            session_path=self.root / "shadow_sessions" / "2026-04-22-0900.md",
            committed_at="2026-04-22 09:30",
        )

        assets = yaml.safe_load((self.root / "shadow_assets" / "assets.yaml").read_text(encoding="utf-8"))

        self.assertEqual(result["added_count"], 0)
        self.assertEqual(result["reset_count"], 1)
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]["id"], "a-2026-04-13-026")
        self.assertEqual(assets[0]["content"], "in der breiten Masse ankommen")
        self.assertEqual(assets[0]["reset_count"], 2)

    def test_commit_chooses_first_asset_when_exact_index_has_multiple_ids(self) -> None:
        assets = yaml.safe_load((self.root / "shadow_assets" / "assets.yaml").read_text(encoding="utf-8"))
        duplicate = dict(assets[0])
        duplicate["id"] = "a-2026-04-14-999"
        duplicate["reset_count"] = 0
        assets.append(duplicate)
        write_yaml(self.root / "shadow_assets" / "assets.yaml", assets)
        state = yaml.safe_load((self.root / "shadow_reviews" / "review_state.yaml").read_text(encoding="utf-8"))
        state.append(
            {
                "id": "a-2026-04-14-999",
                "status": "solid",
                "priority": "normal",
                "review_count": 0,
                "reset_count": 0,
                "last_reviewed_at": None,
                "mistake_note": None,
            }
        )
        write_yaml(self.root / "shadow_reviews" / "review_state.yaml", state)

        result = shadow_commit.commit_session(
            root=self.root,
            session_path=self.root / "shadow_sessions" / "2026-04-21-0934.md",
            committed_at="2026-04-21 10:00",
        )

        assets = yaml.safe_load((self.root / "shadow_assets" / "assets.yaml").read_text(encoding="utf-8"))
        first = next(item for item in assets if item["id"] == "a-2026-04-13-026")
        second = next(item for item in assets if item["id"] == "a-2026-04-14-999")

        self.assertEqual(result["reset_count"], 1)
        self.assertEqual(first["reset_count"], 2)
        self.assertEqual(second["reset_count"], 0)

    def test_dashboard_data_includes_reset_count(self) -> None:
        shadow_commit.commit_session(
            root=self.root,
            session_path=self.root / "shadow_sessions" / "2026-04-21-0934.md",
            committed_at="2026-04-21 10:00",
        )

        payload = build_shadow_dashboard.build_dashboard_data(root=self.root)
        item = next(entry for entry in payload["all_items"] if entry["content"] == "in der breiten Masse")

        self.assertEqual(item["reset_count"], 2)
        self.assertEqual(item["status"], "new")
        self.assertEqual(item["collocation"], "in der breiten Masse ankommen")
        self.assertEqual(payload["summary"]["total_items"], 2)

    def test_dashboard_recent_summary_counts_latest_commit_batch_only(self) -> None:
        shadow_commit.commit_session(
            root=self.root,
            session_path=self.root / "shadow_sessions" / "2026-04-21-0934.md",
            committed_at="2026-04-21 10:00",
        )
        assets = yaml.safe_load((self.root / "shadow_assets" / "assets.yaml").read_text(encoding="utf-8"))
        assets.append(
            {
                "id": "a-2026-04-13-099",
                "type": "pattern",
                "title": "older pattern",
                "content": "older pattern",
                "english": "older pattern",
                "transcript_sentence": "Older sentence.",
                "source_session": "shadow_sessions/2026-04-13-1215.md",
                "created_at": "2026-04-13",
                "status": "solid",
                "priority": "normal",
                "review_count": 2,
                "reset_count": 0,
                "last_reviewed_at": "2026-04-20",
                "mistake_note": None,
            }
        )
        write_yaml(self.root / "shadow_assets" / "assets.yaml", assets)

        payload = build_shadow_dashboard.build_dashboard_data(root=self.root)

        self.assertEqual(payload["summary"]["type_counts"], {"phrase": 1, "word": 1, "pattern": 1})
        self.assertEqual(payload["recent_summary"]["type_counts"], {"phrase": 1, "word": 1})
        self.assertEqual(payload["recent_summary"]["status_counts"], {"new": 2})
        self.assertEqual(payload["recent_summary"]["total_items"], 2)

    def test_commit_accepts_relative_session_path_against_root(self) -> None:
        result = shadow_commit.commit_session(
            root=self.root,
            session_path=Path("shadow_sessions") / "2026-04-21-0934.md",
            committed_at="2026-04-21 10:00",
        )

        self.assertEqual(result["session"], "shadow_sessions/2026-04-21-0934.md")
        self.assertEqual(result["added_count"], 1)
        self.assertEqual(result["reset_count"], 1)

    def test_recent_items_include_reset_hits_from_latest_commit_batch(self) -> None:
        shadow_commit.commit_session(
            root=self.root,
            session_path=self.root / "shadow_sessions" / "2026-04-21-0934.md",
            committed_at="2026-04-21 10:00",
        )

        assets = yaml.safe_load((self.root / "shadow_assets" / "assets.yaml").read_text(encoding="utf-8"))
        for serial in range(28, 40):
            assets.append(
                {
                    "id": f"a-2026-04-21-{serial:03d}",
                    "type": "word",
                    "title": f"extra {serial}",
                    "content": f"extra {serial}",
                    "english": f"extra english {serial}",
                    "transcript_sentence": f"Extra sentence {serial}.",
                    "source_session": "shadow_sessions/2026-04-21-0934.md",
                    "created_at": "2026-04-21",
                    "status": "new",
                    "priority": "normal",
                    "review_count": 0,
                    "reset_count": 0,
                    "last_reviewed_at": None,
                    "mistake_note": None,
                }
            )
        write_yaml(self.root / "shadow_assets" / "assets.yaml", assets)

        payload = build_shadow_dashboard.build_dashboard_data(root=self.root)
        recent_titles = {entry["content"] for entry in payload["recent_items"]}

        self.assertIn("in der breiten Masse", recent_titles)
        self.assertIn("aufwerten", recent_titles)

    def test_dashboard_followup_starts_launcher_when_port_is_free(self) -> None:
        with mock.patch("scripts.shadow_commit.is_dashboard_port_in_use", return_value=False), mock.patch(
            "scripts.shadow_commit.run_dashboard_launcher"
        ) as run_launcher, mock.patch("scripts.shadow_commit.open_dashboard_url") as open_url:
            shadow_commit.post_commit_dashboard_followup(self.root)

        run_launcher.assert_called_once_with(self.root, no_open=False)
        open_url.assert_not_called()

    def test_dashboard_followup_opens_existing_dashboard_when_port_is_busy(self) -> None:
        data_path = self.root / "dashboard" / "data" / "dashboard-data.json"
        write_text(
            data_path,
            '{"generated_at":"2026-04-21T10:15:00","summary":{"total_items":2},"all_items":[],"recent_items":[],"weekly_groups":[]}',
        )

        with mock.patch("scripts.shadow_commit.is_dashboard_port_in_use", return_value=True), mock.patch(
            "scripts.shadow_commit.run_dashboard_launcher"
        ) as run_launcher, mock.patch("scripts.shadow_commit.open_dashboard_url") as open_url:
            shadow_commit.post_commit_dashboard_followup(self.root)

        run_launcher.assert_not_called()
        open_url.assert_called_once()
        self.assertIn("http://localhost:4173/?v=2026-04-21T10%3A15%3A00", open_url.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
