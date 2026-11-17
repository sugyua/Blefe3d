"""Testes de segurança de autenticação e movimentações fictícias.

Não usam banco de produção, WebSocket real ou dados de jogadores.
"""
import unittest
from unittest.mock import patch

import accounts
import server
from aiohttp import web
from aiohttp.test_utils import make_mocked_request


class CredentialRules(unittest.TestCase):
    def test_username_rules(self):
        self.assertEqual(accounts._username(" Jogador_123 "),"jogador_123")
        for bad in ("", "x", "ábc", "x y", "a"*25, "a/b"):
            with self.subTest(bad=bad), self.assertRaises(accounts.AccountError):
                accounts._username(bad)

    def test_password_constraints(self):
        for bad in ("abc", "123456789", "x"*129, None):
            with self.subTest(bad=bad), self.assertRaises(accounts.AccountError):
                accounts._password(bad)
        self.assertEqual(accounts._password("passw0rd-long"),"passw0rd-long")

    def test_argon2_hash_is_not_plaintext(self):
        secret="UmSegredoDeTeste_123"
        digest=accounts.HASHER.hash(secret)
        self.assertNotIn(secret,digest)
        self.assertTrue(accounts.HASHER.verify(digest,secret))

    def test_missing_session_is_not_authenticated(self):
        self.assertIsNone(accounts.from_session(None))
        self.assertIsNone(accounts.from_session(""))


class AccountServerGuards(unittest.IsolatedAsyncioTestCase):
    async def test_websocket_rejects_unauthenticated_player(self):
        request=make_mocked_request("GET","/ws",
            headers={"Host":"blefe.example","Origin":"https://blefe.example"})
        with patch.object(accounts,"from_session",return_value=None):
            with self.assertRaises(web.HTTPUnauthorized):
                await server.websocket(request)

    async def test_websocket_rejects_cross_origin(self):
        request=make_mocked_request("GET","/ws",
            headers={"Host":"blefe.example","Origin":"https://attacker.example"})
        with self.assertRaises(web.HTTPForbidden):
            await server.websocket(request)

    async def test_cookie_is_http_only(self):
        request=make_mocked_request("POST","/api/auth/login",
            headers={"Host":"blefe.example","Origin":"https://blefe.example"})
        response=web.json_response({"ok":True})
        server.set_auth_cookie(request,response,"random_example_session")
        cookie=response.cookies[server.AUTH_COOKIE]
        self.assertTrue(cookie["httponly"])
        self.assertTrue(cookie["secure"])
        self.assertEqual(cookie["samesite"],"Lax")


class TestWalletAccounting(unittest.TestCase):
    def test_accepted_fake_credit_updates_authenticated_player(self):
        player=server.create_player("player",None,"account-1")
        player["authenticated"]=True
        player["test_balance_cents"]=5000
        with patch.object(accounts,"apply_events",
                          return_value=[("account-1",4500,True)]) as apply:
            server.wallet_change(player,-500,"Entrada de teste",event_key="evt-1")
        self.assertEqual(player["test_balance_cents"],4500)
        self.assertEqual(len(player["wallet_history"]),2)
        self.assertEqual(apply.call_args[0][0],
                         [("account-1",-500,"Entrada de teste","evt-1")])

    def test_duplicate_event_is_not_counted_twice(self):
        player=server.create_player("player",None,"account-1")
        player["authenticated"]=True
        previous=len(player["wallet_history"])
        with patch.object(accounts,"apply_events",
                          return_value=[("account-1",5000,False)]):
            server.wallet_change(player,-500,"Entrada de teste",event_key="evt-dup")
        self.assertEqual(player["test_balance_cents"],5000)
        self.assertEqual(len(player["wallet_history"]),previous)

    def test_room_debits_all_human_accounts_in_one_transaction(self):
        room_owner=server.create_player("p1",None,"p1")
        player2=server.create_player("p2",None,"p2")
        for p in (room_owner,player2):
            p["authenticated"]=True
        room=server.make_room(room_owner,"online",500)
        room["players"].append(player2)
        with patch.object(accounts,"apply_events",
                          return_value=[("p1",4500,True),("p2",4500,True)]) as apply:
            server.charge_stakes(room,[room_owner,player2],500)
        self.assertEqual(apply.call_count,1)
        self.assertEqual(len(apply.call_args[0][0]),2)
        self.assertEqual(room_owner["test_balance_cents"],4500)
        self.assertEqual(player2["test_balance_cents"],4500)
        server.ROOMS.pop(room["code"],None)


if __name__=="__main__":
    unittest.main()
