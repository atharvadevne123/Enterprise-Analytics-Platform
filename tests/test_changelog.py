"""Tests for CHANGELOG.md structure and required sections."""

from __future__ import annotations

import pytest


class TestChangelogStructure:
    """Verify CHANGELOG.md follows Keep-a-Changelog conventions."""

    @pytest.fixture(autouse=True)
    def _read(self):
        with open("CHANGELOG.md") as f:
            self._content = f.read()

    def test_file_exists_and_readable(self):
        assert len(self._content) > 0

    def test_has_title(self):
        assert "# Changelog" in self._content

    def test_references_keep_a_changelog(self):
        assert "keepachangelog.com" in self._content

    def test_references_semantic_versioning(self):
        assert "semver.org" in self._content

    def test_has_unreleased_section(self):
        assert "[Unreleased]" in self._content

    def test_has_versioned_release(self):
        assert "[1.0.0]" in self._content

    @pytest.mark.parametrize("subsection", ["### Added", "### Changed"])
    def test_has_standard_subsections(self, subsection):
        assert subsection in self._content


class TestChangelogContent:
    """Verify CHANGELOG.md documents key platform features."""

    @pytest.fixture(autouse=True)
    def _read(self):
        with open("CHANGELOG.md") as f:
            self._content = f.read()

    @pytest.mark.parametrize("keyword", [
        "Kafka",
        "Spark",
        "Airflow",
        "anomaly",
        "forecasting",
    ])
    def test_key_technology_mentioned(self, keyword):
        assert keyword.lower() in self._content.lower()

    def test_unreleased_section_has_added_items(self):
        lines = self._content.splitlines()
        in_unreleased = False
        added_items = 0
        for line in lines:
            if "[Unreleased]" in line:
                in_unreleased = True
            elif in_unreleased and line.startswith("## [") and "[Unreleased]" not in line:
                break
            elif in_unreleased and line.startswith("- "):
                added_items += 1
        assert added_items > 0, "Unreleased section should have at least one changelog entry"

    def test_validate_mentioned_in_unreleased(self):
        lines = self._content.splitlines()
        in_unreleased = False
        found = False
        for line in lines:
            if "[Unreleased]" in line:
                in_unreleased = True
            elif in_unreleased and line.startswith("## [") and "[Unreleased]" not in line:
                break
            elif in_unreleased and "validate" in line.lower():
                found = True
        assert found, "Settings.validate() should be documented in [Unreleased]"
