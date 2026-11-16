"""Regressões para o abandono de treinos e a separação de salas humanas.

Executar na raiz do projeto: python -m unittest discover -s tests -v
Todos os valores são de teste e ficam somente na memória do servidor.
"""
import unittest

import server as game


class BotRoomRulesTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        game.ROOMS.clear()
        game.USERS.clear()

    async def asyncTearDown(self):
        game.ROOMS.clear()
        game.USERS.clear()

    def training_room(self, amount):
        human = game.create_player("Pessoa de teste", None)
        room = game.make_room(human, "training", amount)
        for i in range(3):
            bot = game.create_player("Robô " + str(i), None)
            bot["bot"] = True
            bot["room"] = room["code"]
            room["players"].append(bot)
        return room, human

    async def test_abandon_paid_training_ends_room_without_refund(self):
        room, player = self.training_room(1500)
        code = room["code"]
        self.assertTrue(game.start(room))
        self.assertEqual(player["test_balance_cents"], 3500)
        self.assertEqual(room["pot_cents"], 6000)
        forfeited = game.close_training_room(room)
        self.assertEqual(forfeited, 1500)
        self.assertNotIn(code, game.ROOMS)
        self.assertIsNone(player["room"])
        self.assertEqual(player["test_balance_cents"], 3500)
        self.assertEqual(room["pot_cents"], 0)
        self.assertTrue(all(not member["hand"] for member in room["players"]))

    async def test_closing_before_start_does_not_charge_fee(self):
        room, player = self.training_room(2000)
        self.assertEqual(game.close_training_room(room), 0)
        self.assertEqual(player["test_balance_cents"], 5000)

    async def test_free_training_can_be_closed(self):
        room, player = self.training_room(0)
        self.assertTrue(game.start(room))
        self.assertEqual(game.close_training_room(room), 0)
        self.assertEqual(player["test_balance_cents"], 5000)

    async def test_online_room_rejects_bot_even_if_injected(self):
        human = game.create_player("Anfitrião", None)
        room = game.make_room(human, "online", 500, "public")
        bot = game.create_player("Robô", None)
        bot["bot"] = True
        bot["room"] = room["code"]
        room["players"].append(bot)
        self.assertFalse(game.start(room))
        self.assertEqual(human["test_balance_cents"], 5000)
        self.assertEqual(room["pot_cents"], 0)
        room["players"].remove(bot)
        second = game.create_player("Segundo humano", None)
        second["room"] = room["code"]
        room["players"].append(second)
        self.assertTrue(game.start(room))
        self.assertTrue(all(not p["bot"] for p in game.eligible(room)))
        self.assertEqual(human["test_balance_cents"], 4500)
        self.assertEqual(second["test_balance_cents"], 4500)

    async def test_real_wallet_matches_stay_unavailable(self):
        one = game.create_player("Uma pessoa", None)
        room = game.make_room(one, "online", 0)
        two = game.create_player("Outra pessoa", None)
        two["room"] = room["code"]
        room["players"].append(two)
        room["wallet_type"] = "real"
        self.assertFalse(game.start(room))
        self.assertFalse(room["started"])
        self.assertEqual(one["test_balance_cents"], 5000)


if __name__ == "__main__":
    unittest.main()
