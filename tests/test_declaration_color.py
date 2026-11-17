"""Blefes de ação e cor, no multiplayer e nas pilhas de compra."""
import unittest
from pathlib import Path

import server as game


class DeclareActionColorTests(unittest.TestCase):
    def setUp(self):
        game.ROOMS.clear()
        game.USERS.clear()
        self.actor=game.create_player("Quem joga",None)
        self.challenger=game.create_player("Quem duvida",None)
        self.room=game.make_room(self.actor,"online",0)
        self.room["players"]=[self.actor,self.challenger]
        self.room["turn"]=self.actor["id"]
        self.room["started"]=True
        self.room["color"]="green"
        self.room["top"]={"id":"top","rank":"2","color":"green"}
        self.room["discard"]=[self.room["top"]]
        self.room["deck"]=[{"id":str(i),"rank":"4","color":"yellow"} for i in range(20)]
        self.actor["hand"]=[{"id":"play","rank":"draw2","color":"red"},
                            {"id":"keep","rank":"1","color":"blue"}]
        self.challenger["hand"]=[{"id":"other","rank":"8","color":"yellow"}]
        self.challenger["room"]=self.room["code"]

    def tearDown(self):
        game.ROOMS.clear()
        game.USERS.clear()

    def play(self,claim="draw2",color="green"):
        return game.play(self.room,self.actor,["play"],claim,color)

    def test_missing_or_invalid_declared_color_is_rejected(self):
        for color in (None,"wild","",[],{},123):
            with self.subTest(color=color):
                self.assertIsNotNone(self.play(color=color))
                self.assertEqual(len(self.actor["hand"]),2)
                self.assertIsNone(self.room["pending"])

    def test_red_draw2_claimed_green_is_color_bluff_even_with_real_action(self):
        self.assertIsNone(self.play("draw2","green"))
        pending=self.room["pending"]
        self.assertEqual(pending["claim"],"draw2")
        self.assertEqual(pending["color"],"green")
        self.assertFalse(game.pending_truth(self.room,pending))
        self.assertEqual(game.info(self.room)["pending"]["color"],"green")
        self.assertIsNone(game.resolve(self.room,self.challenger,True))
        self.assertEqual(len(self.actor["hand"]),2)  # one played, one penalty
        self.assertEqual(self.room["last"]["penalty"],1)
        self.assertTrue(self.room["last"]["lie"])
        self.assertEqual(self.room["last"]["claim_color"],"green")
        self.assertEqual(self.room["draw_stack"],0)
        self.assertEqual(self.room["turn"],self.challenger["id"])

    def test_true_rank_and_true_color_are_still_bluff_when_illegal_for_table(self):
        # Red +2 over green 2: cannot claim 'red +2' as a legal move.
        self.assertIsNone(self.play("draw2","red"))
        self.assertFalse(game.pending_truth(self.room,self.room["pending"]))
        self.assertIsNone(game.resolve(self.room,self.challenger,True))
        self.assertEqual(self.room["last"]["penalty"],1)

    def test_truthful_green_draw2_makes_wrong_challenger_buy_three(self):
        self.actor["hand"][0]["color"]="green"
        self.assertIsNone(self.play("draw2","green"))
        self.assertTrue(game.pending_truth(self.room,self.room["pending"]))
        self.assertIsNone(game.resolve(self.room,self.challenger,True))
        self.assertFalse(self.room["last"]["lie"])
        self.assertEqual(self.room["last"]["penalty"],3)
        self.assertEqual(len(self.challenger["hand"]),4)

    def test_wrong_action_is_lie_even_if_color_matches(self):
        self.actor["hand"][0]["rank"]="skip"
        self.actor["hand"][0]["color"]="green"
        self.assertIsNone(self.play("draw2","green"))
        self.assertFalse(game.pending_truth(self.room,self.room["pending"]))
        self.assertIsNone(game.resolve(self.room,self.challenger,True))
        self.assertEqual(self.room["last"]["penalty"],1)

    def test_skip_wrong_color_is_lie(self):
        self.actor["hand"][0].update(rank="skip",color="green")
        self.assertIsNone(self.play("skip","red"))
        self.assertFalse(game.pending_truth(self.room,self.room["pending"]))
        self.assertIsNone(game.resolve(self.room,self.challenger,True))
        self.assertEqual(self.room["last"]["penalty"],1)

    def test_true_skip_requires_matching_color_and_can_be_accepted(self):
        self.actor["hand"][0].update(rank="skip",color="green")
        self.assertIsNone(self.play("skip","green"))
        self.assertTrue(game.pending_truth(self.room,self.room["pending"]))
        self.assertIsNone(game.resolve(self.room,self.challenger,False))
        self.assertEqual(self.room["color"],"green")
        self.assertIsNone(self.room["pending"])

    def test_wild_draw4_freely_selects_any_new_color(self):
        self.actor["hand"][0].update(rank="draw4",color="wild")
        self.assertIsNone(self.play("draw4","blue"))
        self.assertTrue(game.pending_truth(self.room,self.room["pending"]))
        self.assertIsNone(game.resolve(self.room,self.challenger,True))
        self.assertEqual(self.room["last"]["penalty"],5)
        self.assertEqual(self.room["color"],"blue")

    def test_cross_color_stack_is_valid_if_actual_color_declared(self):
        self.actor["hand"][0].update(rank="draw2",color="green")
        self.challenger["hand"]=[{"id":"stack","rank":"draw2","color":"blue"}]
        third=game.create_player("Terceiro",None)
        third["hand"]=[{"id":"extra","rank":"1","color":"yellow"}]
        third["room"]=self.room["code"]
        self.room["players"].append(third)
        self.assertIsNone(self.play("draw2","green"))
        self.assertIsNone(game.play(self.room,self.challenger,["stack"],"draw2","blue"))
        self.assertTrue(game.pending_truth(self.room,self.room["pending"]))
        self.assertIsNone(game.resolve(self.room,third,True))
        self.assertEqual(self.room["last"]["penalty"],5)
        self.assertEqual(self.room["color"],"blue")

    def test_stacked_draw2_with_false_color_cancels_stack_and_buys_one(self):
        self.actor["hand"][0].update(rank="draw2",color="green")
        self.challenger["hand"]=[{"id":"stack","rank":"draw2","color":"red"},
                                {"id":"spare","rank":"1","color":"yellow"}]
        third=game.create_player("Terceiro",None)
        third["room"]=self.room["code"]
        self.room["players"].append(third)
        self.assertIsNone(self.play("draw2","green"))
        self.assertIsNone(game.play(self.room,self.challenger,["stack"],"draw2","blue"))
        self.assertFalse(game.pending_truth(self.room,self.room["pending"]))
        self.assertIsNone(game.resolve(self.room,third,True))
        self.assertEqual(self.room["last"]["penalty"],1)
        self.assertEqual(len(self.challenger["hand"]),2)
        self.assertEqual(self.room["draw_stack"],0)
        self.assertEqual(self.room["turn"],third["id"])

    def test_non_action_card_claiming_action_is_lie(self):
        self.actor["hand"][0].update(rank="7",color="green")
        self.assertIsNone(self.play("reverse","green"))
        self.assertFalse(game.pending_truth(self.room,self.room["pending"]))
        self.assertIsNone(game.resolve(self.room,self.challenger,True))
        self.assertEqual(self.room["last"]["penalty"],1)


class DeclarationInterfaceTests(unittest.TestCase):
    def test_gui_requires_both_declaration_steps(self):
        base=Path(__file__).resolve().parent.parent/"public"
        html=(base/"index.html").read_text(encoding="utf-8")
        js=(base/"app.js").read_text(encoding="utf-8")
        modal=html[html.index('id="claimPanel"'):html.index('id="shopModal"')]
        self.assertIn('id="claimActions"',modal)
        self.assertIn('id="claimColorPrompt"',modal)
        self.assertIn('id="colors"',modal)
        self.assertIn("2. Qual cor você declara?",modal)
        self.assertIn("function submitDeclaredColor(color)",js)
        self.assertIn("if(!state.claim)",js)
        self.assertIn("openDeclaration(true,'draw2')",js)
        self.assertIn("openDeclaration(false,c.rank)",js)
        self.assertIn("COR[s.pending.color]",js)
        self.assertIn("r.claim_color",js)


if __name__=="__main__":
    unittest.main()
