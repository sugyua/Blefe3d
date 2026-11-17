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
        self.assertIn('id="showGuideFromLobby" type="button">Como jogar?', self.html)
        self.assertIn("()=>show($('guide'))", self.pwa)

    def test_welcome_buttons_keep_their_original_actions(self):
        for button_id in ("welcomeTraining", "welcomePublic", "welcomeClose"):
            self.assertIn("'"+button_id+"'", self.pwa)
        self.assertIn("'publicBrowse'", self.pwa)
        self.assertIn("'trainingFree'", self.pwa)


    def test_mobile_lobby_prioritizes_four_actions_and_hides_extras(self):
        start = self.html.index('<section id="lobby" class="overlay">')
        end = self.html.index(' <section id="game" hidden>', start)
        lobby = self.html[start:end]
        self.assertIn('id="trainingFree"', lobby)
        self.assertIn('id="publicBrowse"', lobby)
        self.assertIn('id="showCreateRoom"', lobby)
        self.assertIn('id="showJoinRoom"', lobby)
        self.assertIn('id="createRoomPanel" class="homeInlinePanel" hidden', lobby)
        self.assertIn('id="joinRoomPanel" class="homeInlinePanel" hidden', lobby)
        self.assertIn('<details id="homeMoreMenu"', lobby)
        for action in ('openShop','openWallet','openDonation',
                       'showGuideFromLobby','installApp','training'):
            self.assertIn('id="'+action+'"', lobby)
        self.assertIn('<option value="0" selected>Grátis', lobby)
        self.assertIn('Privacidade e moderação', lobby)

    def test_invitation_and_lobby_shortcuts_stay_connected(self):
        script = (PUBLIC / "app.js").read_text(encoding="utf-8")
        self.assertIn("showHomeRoomPanel('join',true)", script)
        self.assertIn("showHomeRoomPanel('create')", script)
        self.assertIn("'trainingFree').onclick", script)
        self.assertIn("'trainingStake').value='0'", script)
        self.assertIn("'training').click()", script)



if __name__ == "__main__":
    unittest.main()
