"""Sessões anônimas seguras e isolamento da carteira de teste.

Integração em PostgreSQL temporário do CI; saldos reais permanecem desativados.
"""
import secrets
import unittest
import accounts
import server


@unittest.skipUnless(accounts.DATABASE_URL,"Banco de testes ausente")
class GuestDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        accounts.setup()

    def setUp(self):
        self.ids=[]

    def tearDown(self):
        with accounts._db() as conn:
            for account_id in self.ids:
                conn.execute("DELETE FROM game_accounts WHERE id=%s",(account_id,))

    def guest(self):
        account,token=accounts.create_guest()
        self.ids.append(account["id"])
        return account,token

    def test_guest_has_own_balance_and_secret_session_not_ip(self):
        first,token1=self.guest()
        second,token2=self.guest()
        self.assertTrue(first["guest"])
        self.assertTrue(second["guest"])
        self.assertNotEqual(first["id"],second["id"])
        self.assertNotEqual(token1,token2)
        self.assertEqual(accounts.from_guest_session(token1)["id"],first["id"])
        self.assertEqual(accounts.from_guest_session(token2)["id"],second["id"])
        self.assertIsNone(accounts.from_guest_session("invalid"))
        self.assertEqual(first["test_balance_cents"],5000)
        self.assertEqual(second["test_balance_cents"],5000)

    def test_guest_test_wallet_persists_and_stays_separate(self):
        first,token=self.guest()
        second,other_token=self.guest()
        accounts.apply_events([(first["id"],-1000,"Entrada teste","guest-entry-"+first["id"])])
        self.assertEqual(accounts.from_guest_session(token)["test_balance_cents"],4000)
        self.assertEqual(accounts.from_guest_session(other_token)["test_balance_cents"],5000)
        self.assertEqual(accounts.find_by_id(second["id"])["test_balance_cents"],5000)
        with self.assertRaises(accounts.AuthError):
            accounts.login(first["username"],"tentativa-qualquer-senha")

    def test_guest_registration_names_cannot_be_claimed(self):
        with self.assertRaises(accounts.AccountError):
            accounts._username("visitante_12345")

    def test_wallet_public_does_not_enable_real_money(self):
        first,token=self.guest()
        player=server.create_player(first["name"],None,first["id"])
        player["wallet_persistent"]=True
        player["test_balance_cents"]=first["test_balance_cents"]
        result=server.wallet_public(player)
        self.assertEqual(result["real"]["balance_cents"],0)
        self.assertFalse(result["real_money_enabled"])
        with self.assertRaises(ValueError):
            server.wallet_change(player,100,"Depósito",wallet_type="real")


if __name__=="__main__":
    unittest.main()
