import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "skillcere.py"
SPEC = importlib.util.spec_from_file_location("skillcere", MODULE_PATH)
skillcere = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(skillcere)


class SkillCereTests(unittest.TestCase):
    def test_plugin_state_parser(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / "config.toml"
            config.write_text(
                '[plugins."one@market"]\nenabled = true\n\n'
                '[plugins."two@market"]\nenabled = false\n',
                encoding="utf-8",
            )
            self.assertEqual(
                skillcere.read_plugin_states(config),
                {"one@market": True, "two@market": False},
            )

    def test_disabled_plugin_overrides_remote_install_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / "config.toml"
            cache = root / "cache"
            marker_dir = cache / "market" / "two"
            marker_dir.mkdir(parents=True)
            (marker_dir / skillcere.REMOTE_PLUGIN_MARKER).write_text("{}", encoding="utf-8")
            config.write_text('[plugins."two@market"]\nenabled = false\n', encoding="utf-8")
            enabled, disabled = skillcere.configured_codex_plugins(config, cache)
            self.assertEqual(enabled, set())
            self.assertEqual(disabled, {"two@market"})

    def test_discovers_highest_plugin_version_with_namespaced_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = root / "config.toml"
            cache = root / "cache"
            config.write_text('[plugins."demo@market"]\nenabled = true\n', encoding="utf-8")
            for version in ("1.2.0", "1.10.0"):
                plugin_root = cache / "market" / "demo" / version
                manifest_dir = plugin_root / ".codex-plugin"
                skill_dir = plugin_root / "skills" / "helper"
                manifest_dir.mkdir(parents=True)
                skill_dir.mkdir(parents=True)
                (manifest_dir / "plugin.json").write_text(
                    json.dumps(
                        {
                            "name": "demo",
                            "version": version,
                            "repository": "https://example.com/demo",
                            "skills": "./skills/",
                        }
                    ),
                    encoding="utf-8",
                )
                (skill_dir / "SKILL.md").write_text(
                    "---\nname: helper\ndescription: Browser testing helper.\n---\n# Helper\n",
                    encoding="utf-8",
                )
            skills, warnings = skillcere.discover_codex_plugin_skills(config, cache)
            self.assertEqual(warnings, [])
            self.assertEqual(len(skills), 1)
            self.assertEqual(skills[0]["id"], "demo:helper")
            self.assertEqual(skills[0]["latest_version"], "1.10.0")
            self.assertEqual(skills[0]["install_metadata"]["distribution"], "plugin")
            self.assertEqual(skills[0]["categories"], ["browser", "plugin"])


if __name__ == "__main__":
    unittest.main()
