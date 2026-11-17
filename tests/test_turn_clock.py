"""Turnos com prazo de 30s, penalidade de uma carta e avanço automático.

Esses testes usam prazos artificiais curtos; em produção TURN_SECONDS é 30.
"""
import asyncio
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import server as game


class TurnClockTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        game.ROOMS.clear()
        game.USERS.clear()
        self.first=game.create_player("Primeiro",None)
        self.second=game.create_player("Segundo",None)
        room=game.make_room(self.first,"online",0,"public")
        self.second["room"]=room["code"]
        room["players"].append(self.second)
        room["round"]=1
        room["started"]=True
        room["turn"]=self.first["id"]
        room["deck"]=[{"id":"d"+str(i),"rank":"2","color":"blue"} for i in range(50)]
        room["top"]={"id":"top","rank":"2","color":"green"}
        room["color"]="green"
        room["discard"]=[room["top"]]
        self.first["hand"]=[{"id":"f","rank":"7","color":"red"},
                            {"id":"f2","rank":"8","color":"red"}]
        self.second["hand"]=[{"id":"s","rank":"3","color":"yellow"}]
        self.room=room
        game.sync(room)

    async def asyncTearDown(self):
        task=self.room.get("_turn_clock_task")
        if task and not task.done():task.cancel()
        await asyncio.sleep(0)
        game.ROOMS.clear()
        game.USERS.clear()

    async def test_turn_has_30_seconds_and_sync_does_not_refresh(self):
        self.assertEqual(game.TURN_SECONDS,30)
        payload=game.info(self.room)
        self.assertEqual(payload["turn_seconds"],30)
        self.assertGreater(payload["turn_deadline_ms"]-payload["server_time_ms"],28000)
        deadline=self.room["_turn_deadline_mono"]
        game.sync(self.room)
        game.sync(self.room)
        self.assertEqual(self.room["_turn_deadline_mono"],deadline)

    async def test_time_out_draws_exactly_one_and_passes_to_next_player(self):
        self.room["_turn_deadline_mono"]=time.monotonic()-0.5
        self.assertTrue(game.enforce_turn_clock(self.room))
        self.assertEqual(len(self.first["hand"]),3)
        self.assertEqual(len(self.second["hand"]),1)
        self.assertEqual(self.room["turn"],self.second["id"])
        self.assertIn("30 segundos",self.room["public_events"][-1]["text"])
        self.assertGreater(self.room["_turn_deadline_mono"],time.monotonic()+29)

    async def test_action_after_time_limit_is_rejected_and_penalized(self):
        self.room["_turn_deadline_mono"]=time.monotonic()-0.5
        error=game.play(self.room,self.first,["f"])
        self.assertIn("30 segundos",error)
        self.assertEqual(len(self.first["hand"]),3)
        self.assertEqual(self.room["turn"],self.second["id"])

    async def test_pending_draw_stack_is_cleared_with_one_card_only(self):
        actor=self.second
        self.room["turn"]=self.first["id"]
        self.room["pending"]={
            "player":actor["id"],
            "card":{"id":"q","rank":"draw2","color":"green"},
            "claim":"draw2","color":"green","before_color":"green","stacked":False
        }
        self.room["draw_stack"]=2
        self.room["stack_count"]=1
        game.sync(self.room)
        self.room["_turn_deadline_mono"]=time.monotonic()-1
        self.assertTrue(game.enforce_turn_clock(self.room))
        self.assertEqual(len(self.first["hand"]),3)
        self.assertIsNone(self.room["pending"])
        self.assertEqual(self.room["draw_stack"],0)
        self.assertEqual(self.room["turn"],self.second["id"])
        self.assertEqual(self.room["color"],"green")

    async def test_pending_reverse_turn_is_resolved_automatically(self):
        self.room["pending"]={
            "player":self.second["id"],
            "card":{"id":"q-reverse","rank":"reverse","color":"green"},
            "claim":"reverse","color":"green","before_color":"green","stacked":False
        }
        game.sync(self.room)
        self.room["_turn_deadline_mono"]=time.monotonic()-1
        self.assertEqual(self.room["direction"],1)
        self.assertTrue(game.enforce_turn_clock(self.room))
        self.assertEqual(self.room["direction"],-1)
        self.assertEqual(len(self.first["hand"]),3)
        self.assertIsNone(self.room["pending"])

    async def test_acting_player_can_respond_after_a_lie_challenge(self):
        self.room["pending"]={
            "player":self.second["id"],
            "card":{"id":"q-lie","rank":"draw2","color":"red"},
            "claim":"draw2","color":"green","before_color":"green","stacked":False
        }
        self.room["draw_stack"]=2
        self.room["stack_count"]=1
        game.sync(self.room)
        before=self.room["_turn_clock_key"]
        self.assertIsNone(game.resolve(self.room,self.first,True))
        self.assertIsNone(self.room["pending"])
        self.assertEqual(self.room["turn"],self.first["id"])
        self.assertNotEqual(self.room["_turn_clock_key"],before)
        self.assertGreater(self.room["_turn_deadline_mono"],time.monotonic()+29)

    async def test_async_worker_expires_without_browser_or_player_action(self):
        with patch.object(game,"TURN_SECONDS",0.055):
            self.room["_turn_clock_key"]=None
            game.sync(self.room)
            async with asyncio.timeout(1):
                while self.room["turn"]==self.first["id"]:
                    await asyncio.sleep(0.005)
            self.assertEqual(len(self.first["hand"]),3)
            self.assertEqual(self.room["turn"],self.second["id"])

    async def test_new_player_takeover_receives_fresh_turn(self):
        # A pessoa assume exatamente a mão de um bot que estava na vez.
        bot=game.create_player("Bot da mesa",None)
        bot["bot"]=True
        bot["room"]=self.room["code"]
        bot["hand"]=[{"id":"bot-card","rank":"3","color":"green"}]
        bot["id"]="BOTID"
        self.room["mode"]="showcase"
        self.room["showcase"]=True
        self.room["players"]=[bot,self.second]
        self.room["turn"]=bot["id"]
        self.room["host"]=bot["id"]
        self.room["stake"]=0
        game.sync(self.room)
        old_key=self.room["_turn_clock_key"]
        incoming=game.create_player("Novo jogador",None)
        self.assertIsNone(game.takeover_showcase_bot(self.room,incoming))
        self.assertEqual(self.room["turn"],incoming["id"])
        self.assertEqual([c["id"] for c in incoming["hand"]],["bot-card"])
        self.assertNotEqual(self.room["_turn_clock_key"],old_key)
        self.assertGreater(self.room["_turn_deadline_mono"],time.monotonic()+29)


class TurnClockInterfaceTests(unittest.TestCase):
    def test_mobile_countdown_present_and_server_timestamp_used(self):
        root=Path(__file__).resolve().parents[1]/"public"
        html=(root/"index.html").read_text(encoding="utf-8")
        js=(root/"app.js").read_text(encoding="utf-8")
        css=(root/"style.css").read_text(encoding="utf-8")
        self.assertIn('id="turnTimer"',html)
        self.assertIn("function updateTurnTimer()",js)
        self.assertIn("setTurnDeadline(m.state)",js)
        self.assertIn("server_time_ms",js)
        self.assertIn("setInterval(updateTurnTimer,250)",js)
        self.assertIn(".turnTimer.urgent",css)


if __name__=="__main__":
    unittest.main()
