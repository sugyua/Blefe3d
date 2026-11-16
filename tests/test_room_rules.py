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

    async def test_next_player_follows_reverse_direction_and_skips_out(self):
        players = [game.create_player(str(i), None) for i in range(4)]
        room = game.make_room(players[0], 'online', 0)
        room['players'] = players
        room['direction'] = -1
        players[1]['out'] = True
        players[2]['out'] = True
        self.assertIs(game.next_player(room, players[2]['id']), players[0])

    async def test_false_draw_stack_claim_penalizes_last_bluffer(self):
        first = game.create_player('Primeiro', None)
        second = game.create_player('Segundo', None)
        third = game.create_player('Terceiro', None)
        room = game.make_room(first, 'online', 0)
        room['players'] = [first, second, third]
        room['turn'] = first['id']
        room['color'] = 'red'
        first['hand'] = [{'id': 'a', 'rank': 'draw2', 'color': 'red'}, {'id': 'x', 'rank': '1', 'color': 'red'}]
        second['hand'] = [{'id': 'b', 'rank': 'draw4', 'color': 'wild'}, {'id': 'y', 'rank': '1', 'color': 'red'}]
        room['deck'] = [{'id': str(i), 'rank': '1', 'color': 'blue'} for i in range(10)]
        self.assertIsNone(game.play(room, first, ['a'], 'draw2'))
        self.assertIsNone(game.play(room, second, ['b'], 'draw2'))
        self.assertEqual(room['draw_stack'], 4)
        self.assertIsNone(game.resolve(room, third, True))
        self.assertEqual(len(second['hand']), 3)
        self.assertEqual(room['draw_stack'], 0)
        self.assertEqual(room['turn'], third['id'])

    async def test_truthful_stack_challenge_draws_total_plus_one(self):
        first = game.create_player('Primeiro', None)
        second = game.create_player('Segundo', None)
        third = game.create_player('Terceiro', None)
        room = game.make_room(first, 'online', 0)
        room['players'] = [first, second, third]
        room['turn'] = first['id']
        room['color'] = 'red'
        first['hand'] = [{'id': 'a', 'rank': 'draw2', 'color': 'red'}, {'id': 'x', 'rank': '1', 'color': 'red'}]
        second['hand'] = [{'id': 'b', 'rank': 'draw4', 'color': 'wild'}, {'id': 'y', 'rank': '1', 'color': 'red'}]
        third['hand'] = [{'id': 'z', 'rank': '1', 'color': 'blue'}]
        room['deck'] = [{'id': str(i), 'rank': '1', 'color': 'blue'} for i in range(10)]
        self.assertIsNone(game.play(room, first, ['a'], 'draw2'))
        self.assertIsNone(game.play(room, second, ['b'], 'draw4', 'blue'))
        self.assertIsNone(game.resolve(room, third, True))
        self.assertEqual(len(third['hand']), 8)
        self.assertEqual(room['last']['penalty'], 7)
        self.assertEqual(room['draw_stack'], 0)

    async def test_normal_card_cannot_be_stacked_as_draw_card(self):
        first = game.create_player('Primeiro', None)
        second = game.create_player('Segundo', None)
        room = game.make_room(first, 'online', 0)
        room['players'] = [first, second]
        room['turn'] = first['id']
        room['color'] = 'red'
        first['hand'] = [{'id': 'a', 'rank': 'draw2', 'color': 'red'}]
        second['hand'] = [{'id': 'b', 'rank': '1', 'color': 'red'}]
        self.assertIsNone(game.play(room, first, ['a'], 'draw2'))
        self.assertIsNotNone(game.play(room, second, ['b'], 'draw2'))
        self.assertEqual(room['draw_stack'], 2)
        self.assertEqual(len(second['hand']), 1)


if __name__ == "__main__":
    unittest.main()
