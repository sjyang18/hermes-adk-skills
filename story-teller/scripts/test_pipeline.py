#!/usr/bin/env python3
"""Test suite for the story teller pipeline.

Tests:
1. validate_inputs.py — prompt/chapters/max_words validation
2. assemble_story.py — story assembly with frontmatter
3. save_to_vault.py — vault file creation
4. Integration — full pipeline with mock sub-agent outputs

Run:
    python test_pipeline.py
    python test_pipeline.py -v
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
VALIDATE_SCRIPT = SCRIPTS_DIR / "validate_inputs.py"
ASSEMBLE_SCRIPT = SCRIPTS_DIR / "assemble_story.py"
SAVE_SCRIPT = SCRIPTS_DIR / "save_to_vault.py"

# --- Mock outputs ---

MOCK_ENHANCED_PROMPT = """Setting: The year is 2247. The Helix Station orbits Neptune, a massive research facility studying the planet's storms. The station is home to 200 scientists and crew.

Characters:
- Detective Kira Voss: A hardened investigator from Earth, sent to Helix after a high-profile case went wrong. Sharp, methodical, haunted by past failures.
- Dr. Amir Patel: The victim — lead atmospheric physicist, brilliant but secretive. Found dead in the sealed observation dome.
- Commander Li Wei: Station commander, ex-military, values order above all. Wants the case resolved quickly and quietly.
- Dr. Sasha Okafor: Patel's research partner, nervous and evasive. Clearly hiding something about their joint project.

Inciting Incident: Dr. Patel is found dead in the observation dome — a room with no external access points and a surveillance system that shows no one entering or leaving for 6 hours. The door was magnetically sealed from the inside.

Central Conflict: Kira must solve an impossible murder while the station's political factions try to cover up a dangerous experiment that may have caused Patel's death.

Tone: Noir-tinged sci-fi. Atmospheric dread. The isolation of deep space amplifies paranoia."""

MOCK_CREATIVE_CHAPTER = """## Chapter 1

The body floated three inches above the floor.

Kira Voss pressed her face against the observation dome's porthole, watching Dr. Amir Patel's corpse drift in the low gravity like a marionette with cut strings. His eyes were open. His mouth was frozen mid-scream.

"That's not possible," she whispered.

Behind her, Commander Li Wei cleared his throat. "Detective, the magnetic seals—"

"Were locked from inside. I read the report." Kira pulled up the surveillance feed on her wrist display. Six hours of nothing. An empty room. Then — without any transition — a dead man floating.

She'd seen impossible things before. On Earth, they usually had boring explanations. Money, jealousy, opportunity.

But this was Neptune. And nothing out here was boring.

"I want full access to Patel's research files," she said, not turning around.

"That's... classified."

Kira finally looked at the Commander. "Someone just committed murder in a sealed room orbiting a gas giant. Either you give me access, or I start asking questions you won't like in front of your crew."

Li Wei's jaw tightened. "You have twenty-four hours."

It wouldn't be enough. Kira already knew that. The real question wasn't who killed Amir Patel. It was what he'd found in Neptune's storms that was worth killing for."""

MOCK_FOCUSED_CHAPTER = """## Chapter 1

Detective Kira Voss arrived at Helix Station on the 0600 shuttle from Triton Base. The docking bay was cold — they always were on the outer stations — and only Commander Li Wei waited to greet her.

"I expected more of a welcome committee," Kira said, shouldering her bag.

"I've kept this quiet," Li Wei replied, his face unreadable. "Follow me."

They walked through the station's corridors in silence. Kira noted the cameras at every junction, the badge readers on every door. Security was tight here. Which made the crime scene all the more puzzling.

The observation dome was on Level 7. Li Wei pressed his palm to the scanner and the heavy door slid open. Inside, the room was exactly as the initial report described: Dr. Amir Patel lay on the floor beneath the curved glass ceiling, Neptune's blue storms swirling silently above him.

"Cause of death?" Kira asked, crouching beside the body.

"Cardiac arrest. But the station physician noted unusual cellular damage — consistent with extreme radiation exposure. Except there's no radiation source in this room."

Kira studied the sealed door, the unbroken glass, the clean surveillance logs. A locked room with no entry, no weapon, and a death that shouldn't be possible.

"Tell me about his research," she said.

Li Wei hesitated. That hesitation told Kira everything she needed to know about where this case was really going."""

MOCK_FINAL_STORY = """## Chapter 1

The body floated three inches above the floor.

Kira Voss pressed her face against the observation dome's porthole, watching Dr. Amir Patel's corpse drift in the low gravity like a marionette with cut strings. His eyes were open. His mouth was frozen mid-scream.

"That's not possible," she whispered.

Behind her, Commander Li Wei cleared his throat. "Detective, the magnetic seals—"

"Were locked from inside. I read the report." Kira pulled up the surveillance feed on her wrist display. Six hours of nothing. An empty room. Then — without any transition — a dead man floating.

"I want full access to Patel's research files," she said.

"That's... classified."

"Someone just committed murder in a sealed room orbiting a gas giant. Either you give me access, or I start asking questions you won't like."

Li Wei's jaw tightened. "You have twenty-four hours."

## Chapter 2

The research files were a maze of equations and atmospheric data. Kira wasn't a physicist, but she recognized obsession when she saw it. Patel had been tracking something in Neptune's Great Dark Spot — a signal pattern that repeated every 73 hours.

Dr. Sasha Okafor sat across from Kira in the mess hall, hands wrapped around a coffee cup that had gone cold an hour ago.

"What was Project Resonance?" Kira asked directly.

Okafor's eyes darted to the security camera above them. "I can't—"

"Patel is dead. Whatever you're protecting isn't worth protecting anymore."

A long pause. Then, barely above a whisper: "We weren't just studying the storms. We were communicating with them. Or rather... something inside them was communicating with us."

## Chapter 3

The station's power flickered at 0347. Kira was already awake, studying the signal patterns Okafor had finally shared. The 73-hour cycle was due to repeat in six minutes.

She ran to the observation dome — now unsealed as a crime scene — and watched Neptune's swirling surface. The Great Dark Spot rotated into view.

Her wrist display crackled with static. Then, clear as a bell, a voice that wasn't a voice: *We did not mean to harm. He opened the door. We answered.*

The pieces fell together. Patel hadn't been murdered by anyone on the station. He'd made contact with something in the atmosphere — something that existed as pure energy, something that could reach through the station's hull when the signal aligned. His death wasn't murder. It was a handshake that went wrong.

Kira looked up at Neptune's storms and felt very, very small.

She filed her report the next morning: "Death by misadventure. Recommend Project Resonance be continued — with better safety protocols."

Commander Li Wei read it twice. "And the classified material?"

"Stays classified," Kira said. "But next time something reaches out from a gas giant, maybe answer with a robot first."

*The End*"""


class TestValidation(unittest.TestCase):
    """Test validate_inputs.py"""

    def run_validate(self, prompt, chapters=3, max_words=500):
        cmd = [sys.executable, str(VALIDATE_SCRIPT),
               "--prompt", prompt, "--chapters", str(chapters), "--max-words", str(max_words)]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_valid_inputs(self):
        r = self.run_validate("A sci-fi mystery about a detective on a space station")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertTrue(data["valid"])
        self.assertEqual(data["inputs"]["n_chapters"], 3)
        self.assertEqual(data["inputs"]["max_words"], 500)

    def test_empty_prompt_fails(self):
        r = self.run_validate("")
        self.assertNotEqual(r.returncode, 0)

    def test_short_prompt_warns(self):
        r = self.run_validate("Cat tale")  # 8 chars, below 10-char threshold
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertTrue(data["valid"])
        self.assertTrue(any("short" in w for w in data["warnings"]))

    def test_zero_chapters_fails(self):
        r = self.run_validate("A good story", chapters=0)
        self.assertNotEqual(r.returncode, 0)

    def test_high_chapters_warns(self):
        r = self.run_validate("A good story about adventure", chapters=15)
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertTrue(any("slow" in w.lower() for w in data["warnings"]))

    def test_low_max_words_fails(self):
        r = self.run_validate("A good story about adventure", max_words=10)
        self.assertNotEqual(r.returncode, 0)

    def test_custom_params(self):
        r = self.run_validate("Epic fantasy saga", chapters=5, max_words=1000)
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["inputs"]["n_chapters"], 5)
        self.assertEqual(data["inputs"]["max_words"], 1000)


class TestAssembleStory(unittest.TestCase):
    """Test assemble_story.py"""

    def test_assemble_from_stdin(self):
        input_data = json.dumps({
            "prompt": "A sci-fi mystery about a detective on a space station",
            "story": MOCK_FINAL_STORY,
            "n_chapters": 3,
            "max_words": 500,
        })

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            output_path = f.name

        try:
            r = subprocess.run(
                [sys.executable, str(ASSEMBLE_SCRIPT), "--stdin", "--output", output_path],
                input=input_data, capture_output=True, text=True
            )
            self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")

            with open(output_path) as f:
                content = f.read()

            self.assertIn("---\ntype: story", content)
            self.assertIn("chapters: 3", content)
            self.assertIn("Chapter 1", content)
            self.assertIn("Chapter 2", content)
            self.assertIn("Chapter 3", content)
            self.assertIn("The End", content)
            self.assertIn("story-teller v1.0.0", content)
        finally:
            os.unlink(output_path)

    def test_frontmatter_structure(self):
        input_data = json.dumps({
            "prompt": "A fantasy about dragons",
            "story": "Once upon a time...",
            "n_chapters": 2,
            "max_words": 300,
        })

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            output_path = f.name

        try:
            subprocess.run(
                [sys.executable, str(ASSEMBLE_SCRIPT), "--stdin", "--output", output_path],
                input=input_data, capture_output=True, text=True
            )
            with open(output_path) as f:
                content = f.read()

            parts = content.split("---")
            self.assertGreaterEqual(len(parts), 3)
            frontmatter = parts[1]
            self.assertIn("type: story", frontmatter)
            self.assertIn("chapters: 2", frontmatter)
            self.assertIn("tag", frontmatter)
        finally:
            os.unlink(output_path)


class TestSaveToVault(unittest.TestCase):
    """Test save_to_vault.py"""

    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            story_path = os.path.join(tmp_dir, "story.md")
            with open(story_path, "w") as f:
                f.write("# Test Story\nOnce upon a time...")

            vault_dir = os.path.join(tmp_dir, "vault", "stories")

            r = subprocess.run([
                sys.executable, str(SAVE_SCRIPT),
                "--story", story_path,
                "--title", "sci-fi mystery on space station",
                "--vault-dir", vault_dir,
            ], capture_output=True, text=True)

            self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
            saved_files = list(Path(vault_dir).glob("*.md"))
            self.assertEqual(len(saved_files), 1)
            self.assertIn("sci-fi-mystery", saved_files[0].name)

    def test_save_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            story_path = os.path.join(tmp_dir, "story.md")
            with open(story_path, "w") as f:
                f.write("# Test")

            vault_dir = os.path.join(tmp_dir, "deep", "nested", "stories")
            r = subprocess.run([
                sys.executable, str(SAVE_SCRIPT),
                "--story", story_path,
                "--title", "test story",
                "--vault-dir", vault_dir,
            ], capture_output=True, text=True)

            self.assertEqual(r.returncode, 0)
            self.assertTrue(os.path.isdir(vault_dir))

    def test_save_duplicate_sequencing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            story_path = os.path.join(tmp_dir, "story.md")
            with open(story_path, "w") as f:
                f.write("# Test")

            vault_dir = os.path.join(tmp_dir, "vault")
            for _ in range(3):
                r = subprocess.run([
                    sys.executable, str(SAVE_SCRIPT),
                    "--story", story_path,
                    "--title", "same title",
                    "--vault-dir", vault_dir,
                ], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0)

            saved_files = sorted(Path(vault_dir).glob("*.md"))
            self.assertEqual(len(saved_files), 3)

    def test_slugification(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            story_path = os.path.join(tmp_dir, "story.md")
            with open(story_path, "w") as f:
                f.write("# Test")

            vault_dir = os.path.join(tmp_dir, "vault")
            r = subprocess.run([
                sys.executable, str(SAVE_SCRIPT),
                "--story", story_path,
                "--title", "A Sci-Fi Mystery!!! About @Space",
                "--vault-dir", vault_dir,
            ], capture_output=True, text=True)

            self.assertEqual(r.returncode, 0)
            saved_files = list(Path(vault_dir).glob("*.md"))
            # Should be lowercase, no special chars
            self.assertNotIn("!", saved_files[0].name)
            self.assertNotIn("@", saved_files[0].name)
            self.assertIn("sci-fi", saved_files[0].name)


class TestIntegration(unittest.TestCase):
    """End-to-end integration with mock outputs."""

    def test_full_pipeline_mock(self):
        """Full pipeline: validate → assemble → save."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Step 0: Validate
            r = subprocess.run([
                sys.executable, str(VALIDATE_SCRIPT),
                "--prompt", "A sci-fi mystery about a detective on a space station",
                "--chapters", "3", "--max-words", "500"
            ], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            inputs = json.loads(r.stdout)["inputs"]

            # Step 4: Assemble (using mock story from steps 1-3)
            story_path = os.path.join(tmp_dir, "story.md")
            assemble_input = json.dumps({
                "prompt": inputs["prompt"],
                "story": MOCK_FINAL_STORY,
                "n_chapters": inputs["n_chapters"],
                "max_words": inputs["max_words"],
            })

            r = subprocess.run([
                sys.executable, str(ASSEMBLE_SCRIPT), "--stdin", "--output", story_path
            ], input=assemble_input, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)

            # Step 5: Save to vault
            vault_dir = os.path.join(tmp_dir, "vault")
            r = subprocess.run([
                sys.executable, str(SAVE_SCRIPT),
                "--story", story_path,
                "--title", "sci-fi mystery space station",
                "--vault-dir", vault_dir,
            ], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)

            # Verify
            saved_files = list(Path(vault_dir).glob("*.md"))
            self.assertEqual(len(saved_files), 1)

            with open(saved_files[0]) as f:
                final = f.read()

            self.assertIn("type: story", final)
            self.assertIn("Chapter 1", final)
            self.assertIn("Chapter 3", final)
            self.assertIn("Kira Voss", final)
            self.assertIn("Neptune", final)
            self.assertGreater(len(final), 3000)


if __name__ == "__main__":
    unittest.main()
