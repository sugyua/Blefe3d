"""Garante que as boas-vindas sejam objetivas e o tutorial continue acessível."""
import re
import unittest
from pathlib import Path


PUBLIC = Path(__file__).resolve().parent.parent / "public"


class WelcomeScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (PUBLIC / "index.html").read_text(encoding="utf-8")
        cls.pwa = (PUBLIC / "pwa.js").read_text(encoding="utf-8")

    def test_short_welcome_has_only_three_actions_and_short_notice(self):
        start = self.html.index('<div id="welcomeGuide" class="modal"')
        end = self.html.index('<div id="installModal" class="modal"', start)
        intro = self.html[start:end]

        self.assertIn("Bem-vindo ao Blefe Color!", intro)
        self.assertIn("Comece com um treino grátis ou encontre uma sala para jogar.", intro)
        self.assertIn("Entradas apenas de teste, sem valor real.", intro)
        self.assertEqual(re.findall(r'<button\b[^>]*id="([^"]+)"', intro),
                         ["welcomeTraining", "welcomePublic", "welcomeClose"])
        self.assertNotIn("Quando alguém declarar", intro)
        self.assertNotIn("Jogue uma carta da mesma cor", intro)
        self.assertNotIn("O jogo precisa de internet", intro)
        self.assertNotIn("introSteps", intro)

    def test_detailed_rules_are_in_the_tutorial_instead(self):
        start = self.html.index('<div id="guide" class="modal"')
        tutorial = self.html[start:]
        self.assertIn("Como jogar", tutorial)
        self.assertIn("BLOQUEIO", tutorial.upper())
        self.assertIn("+2", tutorial)
        self.assertIn("+4", tutorial)
        self.assertIn("id=\"showGuideFromLobby\">Como jogar?", self.html)
        self.assertIn("()=>show($('guide'))", self.pwa)

    def test_welcome_buttons_keep_their_original_actions(self):
        for button_id in ("welcomeTraining", "welcomePublic", "welcomeClose"):
            self.assertIn("'"+button_id+"'", self.pwa)
        self.assertIn("'publicBrowse'", self.pwa)
        self.assertIn("'trainingStake'", self.pwa)


if __name__ == "__main__":
    unittest.main()
