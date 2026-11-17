"""Oito mesas anunciadas com transparência: bots reais e saldo fictício."""
import asyncio
import json
import unittest

from aiohttp.test_utils import make_mocked_request
import server as game


class ShowcaseRoomTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        game.ROOMS.clear()
        game.USERS.clear()

    async def asyncTearDown(self):
        for room in game.ROOMS.values():
            task=room.get("_turn_clock_task")
            if task and not task.done():task.cancel()
        game.ROOMS.clear()
        game.USERS.clear()
        await asyncio.sleep(0)

    async def test_all_eight_rooms_are_real_and_advertised_with_bot_labels(self):
        self.assertEqual(len(game.SHOWCASE_SPECS),8)
        codes=set()
        for args in game.SHOWCASE_SPECS:
            room=game.make_showcase_room(*args)
            codes.add(room["code"])
            self.assertTrue(room["showcase"])
            self.assertTrue(room["started"])
            self.assertEqual(room["mode"],"showcase")
            self.assertIn(len(room["players"]),(2,3))
            self.assertTrue(all(p["bot"] for p in room["players"]))
            self.assertTrue(all(p["hand"] for p in room["players"]))
            self.assertEqual(room["wallet_type"],"test")
            self.assertEqual(room["visibility"],"public")
        self.assertEqual(len(codes),8)
        result=await game.list_public_rooms(make_mocked_request("GET","/api/salas-publicas"))
        published=json.loads(result.body)["rooms"]
        self.assertEqual(len([r for r in published if r["showcase"]]),8)
        self.assertTrue(all(r["bots"] in (2,3) for r in published))
        self.assertTrue(all(r["status"]=="em andamento" for r in published))

    async def test_takeover_transfers_hand_charges_test_wallet_once(self):
        room=game.make_showcase_room("TST001","Bots para teste",500,2)
        player=game.create_player("Humano",None)
        bot=next(p for p in room["players"] if p["bot"] and not p["out"])
        bot_cards=[c["id"] for c in bot["hand"]]
        original_pot=room["pot_cents"]
        room["turn"]=bot["id"]
        game.sync(room)
        self.assertIsNone(game.takeover_showcase_bot(room,player))
        self.assertEqual(player["test_balance_cents"],4500)
        self.assertEqual([c["id"] for c in player["hand"]],bot_cards)
        self.assertIn(player,room["players"])
        self.assertEqual(room["turn"],player["id"])
        self.assertEqual(room["pot_cents"],original_pot)
        self.assertEqual(len(room["players"]),2)
        self.assertTrue(game.info(room)["showcase"])
        self.assertEqual(sum(p["bot"] for p in room["players"]),1)
        self.assertEqual([x["amount_cents"] for x in player["wallet_history"]][-1],-500)
        self.assertIsNotNone(game.takeover_showcase_bot(room,player))
        self.assertEqual(player["test_balance_cents"],4500)

    async def test_leave_restores_bot_without_refunding_paid_test_entry(self):
        room=game.make_showcase_room("TST002","Teste de desistência",1000,3)
        player=game.create_player("Humano",None)
        self.assertIsNone(game.takeover_showcase_bot(room,player))
        self.assertEqual(player["test_balance_cents"],4000)
        acquired=[card["id"] for card in player["hand"]]
        self.assertTrue(game.restore_showcase_bot(room,player))
        self.assertIsNone(player["room"])
        self.assertFalse(player["hand"])
        self.assertEqual(player["test_balance_cents"],4000)
        self.assertEqual(len(room["players"]),3)
        self.assertTrue(any(p["bot"] and [c["id"] for c in p["hand"]]==acquired
                            for p in room["players"]))

    async def test_no_human_is_falsely_advertised_or_real_cash_requested(self):
        room=game.make_showcase_room("TST003","Bots gratuitos",0,2)
        preview=await game.room_preview(make_mocked_request("GET","/api/sala/TST003",
            match_info={"code":"TST003"}))
        data=json.loads(preview.body)
        self.assertTrue(data["showcase"])
        self.assertEqual(data["bots"],2)
        self.assertTrue(data["takeover"])
        self.assertEqual(data["wallet_type"],"test")
        self.assertEqual(data["stake_cents"],0)

    async def test_bot_room_cannot_accept_real_wallet(self):
        room=game.make_showcase_room("TST004","Bots",500,2)
        room["wallet_type"]="real"
        player=game.create_player("Pessoa",None)
        self.assertIsNotNone(game.takeover_showcase_bot(room,player))
        self.assertEqual(player["test_balance_cents"],5000)


if __name__=="__main__":
    unittest.main()
