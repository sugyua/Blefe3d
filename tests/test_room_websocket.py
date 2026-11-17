"""Smoke tests for room actions through the actual WebSocket endpoint."""
import asyncio
import unittest
from unittest.mock import patch

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
import server as game


class RoomWebSocketTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        game.ROOMS.clear()
        game.USERS.clear()
        app = web.Application()
        app.router.add_get('/ws', game.websocket)
        self.client = TestClient(TestServer(app))
        await self.client.start_server()
        self.sockets = []
        self.identities = {}
        self.auth_session_patch = patch.object(game.accounts,'from_session',
            side_effect=lambda token: self.identities.get(token))
        self.auth_history_patch = patch.object(game.accounts,'history',
            return_value=[{'amount_cents':5000,
                           'description':'Bônus único de boas-vindas para testes','at':0}])
        self.auth_events_patch = patch.object(game.accounts,'apply_events',
            side_effect=self.fake_wallet_entries)
        self.auth_session_patch.start()
        self.auth_history_patch.start()
        self.auth_events_patch.start()

    async def asyncTearDown(self):
        for ws in self.sockets:
            await ws.close()
        await self.client.close()
        self.auth_session_patch.stop()
        self.auth_history_patch.stop()
        self.auth_events_patch.stop()
        game.ROOMS.clear()
        game.USERS.clear()

    def fake_wallet_entries(self, entries):
        result=[]
        for account_id,delta,description,key in entries:
            player=game.USERS[account_id]
            new_amount=player['test_balance_cents']+delta
            if new_amount<0:raise game.accounts.AccountError('Saldo insuficiente')
            result.append((account_id,new_amount,True))
        return result

    async def connect(self, name):
        number=len(self.identities)+1
        token=f'test-login-session-{number}'
        account_id=f'authenticated-account-{number}'
        self.identities[token]={
            'id':account_id,'username':f'jogador{number}',
            'name':name,'test_balance_cents':5000,'ad_free':False
        }
        origin=str(self.client.make_url('/').origin())
        ws=await self.client.ws_connect('/ws',headers={
            'Origin':origin,'Cookie':f'blefe_session={token}'
        })
        self.sockets.append(ws)
        await ws.send_json({'type':'hello'})
        welcome=await self.receive_type(ws,'welcome')
        return ws,welcome['id']

    async def receive_type(self, ws, kind):
        async with asyncio.timeout(3):
            while True:
                message = await ws.receive_json()
                if message['type'] == kind:
                    return message

    async def test_current_player_leaves_and_turn_passes_to_next_player(self):
        host, host_id = await self.connect('Anfitrião')
        middle, middle_id = await self.connect('Segundo')
        last, last_id = await self.connect('Terceiro')
        await host.send_json({'type': 'create', 'mode': 'online', 'stake': 0})
        room_state = await self.receive_type(host, 'state')
        code = room_state['state']['code']
        for ws in (middle, last):
            await ws.send_json({'type': 'join', 'code': code, 'accept_stake_cents': 0})
            await self.receive_type(ws, 'state')
        await host.send_json({'type': 'start'})
        async with asyncio.timeout(3):
            while not game.ROOMS[code]['started']:
                await asyncio.sleep(0)
        room = game.ROOMS[code]
        room['turn'] = middle_id
        await middle.send_json({'type': 'leave'})
        await self.receive_type(middle, 'left')
        self.assertEqual(room['turn'], last_id)
        self.assertEqual([p['id'] for p in room['players']], [host_id, last_id])

    async def test_paid_training_disconnect_closes_room_without_refund(self):
        ws, player_id = await self.connect('Pessoa')
        await ws.send_json({'type': 'create', 'mode': 'training', 'stake': 500})
        state = await self.receive_type(ws, 'state')
        code = state['state']['code']
        self.assertEqual(game.USERS[player_id]['test_balance_cents'], 4500)
        await ws.close()
        async with asyncio.timeout(3):
            while code in game.ROOMS:
                await asyncio.sleep(0)
        self.assertIsNone(game.USERS[player_id]['room'])
        self.assertEqual(game.USERS[player_id]['test_balance_cents'], 4500)
