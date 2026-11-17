"""Testes reais de conta, sessão e saldo fictício com PostgreSQL temporário.

O CI fornece DATABASE_URL para uma instância descartável. Nenhum dado de
produção é usado e o arquivo pode ser executado localmente sem o banco
(com testes de integração ignorados).
"""
import secrets
import unittest

import accounts


@unittest.skipUnless(accounts.DATABASE_URL, "PostgreSQL de teste não configurado")
class AccountDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        accounts.setup()

    def setUp(self):
        self.accounts=[]
        self.username="teste"+secrets.token_hex(5)
        self.password="SegredoForte-"+secrets.token_hex(8)

    def tearDown(self):
        if self.accounts:
            with accounts._db() as conn:
                for account_id in self.accounts:
                    conn.execute("DELETE FROM game_accounts WHERE id=%s",(account_id,))

    def make_account(self):
        username=self.username+str(len(self.accounts))
        account,token=accounts.create(username,self.password)
        self.accounts.append(account["id"])
        return account,token

    def test_register_login_session_logout_and_no_duplicate_bonus(self):
        user,token=self.make_account()
        self.assertEqual(user["test_balance_cents"],5000)
        self.assertEqual(accounts.from_session(token)["id"],user["id"])
        self.assertIsNone(accounts.from_session("invalid-token"))
        wallet=accounts.history(user["id"])
        self.assertEqual(len(wallet),1)
        self.assertEqual(wallet[0]["amount_cents"],5000)
        with self.assertRaises(accounts.AccountError):
            accounts.create(user["username"],self.password)
        with self.assertRaises(accounts.AuthError):
            accounts.login(user["username"],"SenhaErradaQueNaoServe")
        again,token2=accounts.login(user["username"],self.password)
        self.assertEqual(again["id"],user["id"])
        self.assertEqual(again["test_balance_cents"],5000)
        self.assertNotEqual(token2,token)
        accounts.logout(token2)
        self.assertIsNone(accounts.from_session(token2))
        self.assertEqual(accounts.from_session(token)["id"],user["id"])

    def test_test_credit_ledger_idempotent_and_persistent(self):
        user,_=self.make_account()
        entry=(user["id"],-1500,"Entrada fictícia","test-entry-"+user["id"])
        first=accounts.apply_events([entry])
        self.assertEqual(first,[(user["id"],3500,True)])
        same=accounts.apply_events([entry])
        self.assertEqual(same,[(user["id"],3500,False)])
        prize=(user["id"],2200,"Prêmio fictício","test-prize-"+user["id"])
        self.assertEqual(accounts.apply_events([prize]),[(user["id"],5700,True)])
        self.assertEqual(accounts.find_by_id(user["id"])["test_balance_cents"],5700)
        self.assertEqual(len(accounts.history(user["id"])),3)

    def test_atomic_batch_does_not_charge_anyone_if_one_lacks_credits(self):
        first,_=self.make_account()
        second,_=self.make_account()
        # The first can pay; the second cannot. The whole transaction rolls back.
        accounts.apply_events([(second["id"],-4500,"Teste","prefund-"+second["id"])])
        before1=accounts.find_by_id(first["id"])["test_balance_cents"]
        before2=accounts.find_by_id(second["id"])["test_balance_cents"]
        with self.assertRaises(accounts.AccountError):
            accounts.apply_events([
                (first["id"],-1000,"Entrada","batch1-"+first["id"]),
                (second["id"],-1000,"Entrada","batch2-"+second["id"]),
            ])
        self.assertEqual(accounts.find_by_id(first["id"])["test_balance_cents"],before1)
        self.assertEqual(accounts.find_by_id(second["id"])["test_balance_cents"],before2)
        self.assertFalse(any(e["description"]=="Entrada" for e in accounts.history(first["id"])))


if __name__=="__main__":
    unittest.main()
