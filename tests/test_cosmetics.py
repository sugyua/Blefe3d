"""Loja visual: segurança da propriedade, catálogo e integração PostgreSQL.

Os valores em price_hint_cents nunca são processados em pagamentos.
"""
import asyncio
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer, make_mocked_request

import accounts
import cosmetics
import server


class ShopCatalogTests(unittest.TestCase):
    def test_catalog_is_curated_and_all_purchase_flows_are_disabled(self):
        catalog=cosmetics.catalog()
        self.assertFalse(catalog['payments_enabled'])
        self.assertEqual(catalog['phase'],'visual_preview_no_payments')
        self.assertEqual(len(catalog['items']),12)
        self.assertEqual(len(cosmetics.FREE_IDS),9)
        self.assertEqual(len(set(x['id'] for x in catalog['items'])),12)
        self.assertEqual(set(cosmetics.DEFAULTS),{'back','table','frame'})
        for slot,product in cosmetics.DEFAULTS.items():
            self.assertEqual(cosmetics.item_for(slot,product)['slot'],slot)
            self.assertIn(product,cosmetics.FREE_IDS)
        for item in catalog['items']:
            if item['free']:
                self.assertIsNone(item['price_hint_cents'])
            else:
                self.assertGreater(item['price_hint_cents'],0)

    def test_reject_invalid_skins_or_categories(self):
        for slot,product in (
            ('bad','back_classic'),
            ('table','back_classic'),
            ('back','back_not_real'),
            ('frame','../../etc/passwd'),
        ):
            with self.subTest(slot=slot,product=product):
                with self.assertRaises(cosmetics.ShopError):
                    cosmetics.item_for(slot,product)

    def test_shop_interface_has_all_required_controls_and_no_checkout(self):
        root=Path(__file__).resolve().parents[1]/'public'
        html=(root/'index.html').read_text(encoding='utf-8')
        script=(root/'shop.js').read_text(encoding='utf-8')
        css=(root/'shop.css').read_text(encoding='utf-8')
        for marker in ('openShop','shopModal','shopTabs','shopGrid',
                       'shopPreviewScene','shopEquipButton','shopOwnedCount'):
            self.assertIn('id="'+marker+'"',html)
        self.assertIn('/api/shop/equip',script)
        self.assertIn('payments_enabled',str(cosmetics.catalog()))
        self.assertNotIn('/api/shop/purchase',script)
        self.assertIn('[data-skin="table_ocean"]',css)
        self.assertIn('body[data-shop-back="back_neon"]',css)


class ShopAuthTests(unittest.IsolatedAsyncioTestCase):
    async def test_catalog_is_public_but_inventory_needs_cookie(self):
        response=await server.api_shop_catalog(make_mocked_request(
            'GET','/api/shop/catalog'))
        payload=json.loads(response.body)
        self.assertFalse(payload['payments_enabled'])
        req=make_mocked_request('GET','/api/shop/me')
        with patch.object(accounts,'from_session',return_value=None),patch.object(
                accounts,'from_guest_session',return_value=None):
            with self.assertRaises(web.HTTPUnauthorized):
                await server.api_shop_me(req)

    async def test_equipping_is_blocked_cross_origin(self):
        req=make_mocked_request('POST','/api/shop/equip',headers={
            'Host':'blefe.example','Origin':'https://external.example'
        })
        with self.assertRaises(web.HTTPForbidden):
            await server.api_shop_equip(req)


@unittest.skipUnless(accounts.DATABASE_URL,"PostgreSQL temporário não configurado")
class ShopDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        accounts.setup()

    def setUp(self):
        self.account,self.cookie=accounts.create_guest()

    def tearDown(self):
        with accounts._db() as conn:
            conn.execute('DELETE FROM game_accounts WHERE id=%s',
                         (self.account['id'],))

    def test_guest_equips_free_skin_and_keeps_test_wallet_intact(self):
        start=accounts.cosmetic_state(self.account['id'])
        self.assertEqual(start['equipped'],dict(cosmetics.DEFAULTS))
        self.assertEqual(len(start['owned']),9)
        result=accounts.equip_cosmetic(self.account['id'],'table','table_ocean')
        self.assertEqual(result['equipped']['table'],'table_ocean')
        again=accounts.cosmetic_state(self.account['id'])
        self.assertEqual(again['equipped']['table'],'table_ocean')
        self.assertEqual(accounts.find_by_id(self.account['id'])['test_balance_cents'],5000)
        self.assertEqual(len(accounts.history(self.account['id'])),1)

    def test_free_card_and_avatar_frame_equipment_persist(self):
        accounts.equip_cosmetic(self.account['id'],'back','back_neon')
        accounts.equip_cosmetic(self.account['id'],'frame','frame_mint')
        again=accounts.cosmetic_state(self.account['id'])
        self.assertEqual(again['equipped']['back'],'back_neon')
        self.assertEqual(again['equipped']['frame'],'frame_mint')

    def test_locked_premium_skin_cannot_be_equipped(self):
        with self.assertRaises(cosmetics.LockedCosmetic):
            accounts.equip_cosmetic(self.account['id'],'table','table_galaxy')
        with self.assertRaises(cosmetics.LockedCosmetic):
            accounts.equip_cosmetic(self.account['id'],'back','back_royal')
        self.assertEqual(accounts.cosmetic_state(self.account['id'])['equipped'],
                         dict(cosmetics.DEFAULTS))

    def test_cross_slot_equip_fails_without_state_change(self):
        with self.assertRaises(cosmetics.ShopError):
            accounts.equip_cosmetic(self.account['id'],'frame','back_neon')
        self.assertEqual(accounts.cosmetic_state(self.account['id'])['equipped'],
                         dict(cosmetics.DEFAULTS))


@unittest.skipUnless(accounts.DATABASE_URL,"PostgreSQL temporário não configurado")
class ShopHttpTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await asyncio.to_thread(accounts.setup)
        self.account,self.cookie=await asyncio.to_thread(accounts.create_guest)
        app=web.Application()
        app.router.add_get('/api/shop/catalog',server.api_shop_catalog)
        app.router.add_get('/api/shop/me',server.api_shop_me)
        app.router.add_post('/api/shop/equip',server.api_shop_equip)
        self.client=TestClient(TestServer(app))
        await self.client.start_server()
        self.headers={'Cookie':'blefe_guest_session='+self.cookie,
                      'Origin':str(self.client.make_url('/').origin())}

    async def asyncTearDown(self):
        await self.client.close()
        with accounts._db() as conn:
            conn.execute('DELETE FROM game_accounts WHERE id=%s',
                         (self.account['id'],))

    async def test_http_guest_can_equip_free_skin_but_not_fake_buy_premium(self):
        response=await self.client.get('/api/shop/me',headers=self.headers)
        self.assertEqual(response.status,200)
        me=await response.json()
        self.assertEqual(me['equipped']['back'],'back_classic')
        response=await self.client.post('/api/shop/equip',
            headers=self.headers,
            json={'slot':'back','product_id':'back_sunset'})
        self.assertEqual(response.status,200)
        equipped=await response.json()
        self.assertEqual(equipped['equipped']['back'],'back_sunset')
        response=await self.client.post('/api/shop/equip',
            headers=self.headers,
            json={'slot':'back','product_id':'back_royal',
                  'price_hint_cents':0,'paid':True,'admin':True})
        self.assertEqual(response.status,403)
        self.assertEqual(accounts.cosmetic_state(self.account['id'])['equipped']['back'],
                         'back_sunset')

    async def test_http_anonymous_equipment_is_denied(self):
        response=await self.client.post('/api/shop/equip',
            headers={'Origin':self.headers['Origin']},
            json={'slot':'frame','product_id':'frame_mint'})
        self.assertEqual(response.status,401)


if __name__=='__main__':
    unittest.main()
