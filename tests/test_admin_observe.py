import unittest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
import server as game


class AdminObservationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        game.ROOMS.clear()
        self.old_token = game.ADMIN_TOKEN
        game.ADMIN_TOKEN = 'test-secret'
        app = web.Application()
        app.router.add_get('/api/admin/rooms/{code}', game.admin_observe)
        self.client = TestClient(TestServer(app))
        await self.client.start_server()
        self.host = game.create_player('Alice', None)
        self.room = game.make_room(self.host, 'online', 500)
        self.host['hand'] = [{'id': 'private-card-id', 'color': 'red', 'rank': '5'}]

    async def asyncTearDown(self):
        await self.client.close()
        game.ADMIN_TOKEN = self.old_token
        game.ROOMS.clear()

    async def test_requires_authentication_and_logs_authorized_observation(self):
        url = '/api/admin/rooms/' + self.room['code']
        self.assertEqual((await self.client.get(url)).status, 401)
        with self.assertLogs('blefe.admin', level='INFO') as logs:
            response = await self.client.get(url, headers={'Authorization': 'Bearer test-secret'})
        self.assertEqual(response.status, 200)
        self.assertIn(self.room['code'], ' '.join(logs.output))
        self.assertNotIn('test-secret', ' '.join(logs.output))
        self.assertEqual(len(self.room['players']), 1)

    async def test_never_exposes_hidden_cards_or_session_tokens(self):
        self.room['pending'] = {'player': self.host['id'], 'claim': 'draw2', 'color': 'red',
                                'card': {'id': 'hidden-card-id', 'rank': '7', 'color': 'blue'}}
        self.room['hidden_top'] = True
        self.room['top'] = self.room['pending']['card']
        response = await self.client.get('/api/admin/rooms/' + self.room['code'],
                                         headers={'Authorization': 'Bearer test-secret'})
        text = await response.text()
        self.assertEqual(response.status, 200)
        self.assertNotIn('hidden-card-id', text)
        self.assertNotIn('private-card-id', text)
        self.assertNotIn(self.host['id'], text)
        self.assertNotIn('blue', text)

    async def test_observation_shows_public_moves_without_joining_the_game(self):
        other = game.create_player('Bob', None)
        self.room['players'].append(other)
        self.room.update(started=True, turn=self.host['id'], color='red',
                         top={'id':'top','rank':'1','color':'red'},
                         discard=[], deck=[])
        self.host['hand'].append({'id':'keep','rank':'3','color':'red'})
        self.assertIsNone(game.play(self.room, self.host, ['private-card-id']))
        before = (self.room['turn'], list(self.room['players']), list(self.host['hand']))
        response = await self.client.get('/api/admin/rooms/' + self.room['code'],
                                         headers={'Authorization': 'Bearer test-secret'})
        data = await response.json()
        self.assertEqual(data['top'], {'rank':'5','color':'red'})
        self.assertTrue(any('5 (red)' in event['text'] for event in data['events']))
        self.assertTrue(next(p for p in data['room']['players'] if p['name']=='Bob')['turn'])
        self.assertEqual(before, (self.room['turn'], self.room['players'], self.host['hand']))

