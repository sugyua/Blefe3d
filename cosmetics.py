"""Catálogo aprovado no servidor para a Loja do Blefe Color (fase 1).

Itens de demonstração: não há preços cobrados, compras, Pix ou moeda real.
Somente os itens marcados free=True podem ser equipados livremente.
As classes CSS no navegador usam exclusivamente IDs desta lista.
"""
from types import MappingProxyType

CATEGORIES = (
    {"id": "back", "name": "Versos de cartas", "icon": "🂠",
     "description": "Personalize as cartas viradas para baixo na sua mesa."},
    {"id": "table", "name": "Mesas temáticas", "icon": "♠",
     "description": "Escolha a atmosfera visual da mesa que você vê."},
    {"id": "frame", "name": "Molduras de perfil", "icon": "✦",
     "description": "Uma moldura diferente em torno do seu avatar."},
)

DEFAULTS = MappingProxyType({
    "back": "back_classic",
    "table": "table_emerald",
    "frame": "frame_slate",
})

# price_hint_cents é apenas hipótese de preço futuro: não pode ser cobrado.
_CATALOG = (
    {"id": "back_classic", "slot": "back", "name": "Clássico",
     "description": "O verso tradicional para começar a blefar.",
     "free": True, "price_hint_cents": None, "label": "Padrão"},
    {"id": "back_neon", "slot": "back", "name": "Neon Azul",
     "description": "Luzes frias e traços elétricos no verso das cartas.",
     "free": True, "price_hint_cents": None, "label": "Grátis"},
    {"id": "back_sunset", "slot": "back", "name": "Pôr do Sol",
     "description": "Rosa e laranja em um baralho vibrante.",
     "free": True, "price_hint_cents": None, "label": "Grátis"},
    {"id": "back_royal", "slot": "back", "name": "Ouro Real",
     "description": "Um acabamento dourado planejado para a loja premium.",
     "free": False, "price_hint_cents": 490, "label": "Em breve"},
    {"id": "table_emerald", "slot": "table", "name": "Esmeralda",
     "description": "A mesa verde clássica do Blefe Color.",
     "free": True, "price_hint_cents": None, "label": "Padrão"},
    {"id": "table_ocean", "slot": "table", "name": "Oceano",
     "description": "Azuis profundos em uma mesa elegante.",
     "free": True, "price_hint_cents": None, "label": "Grátis"},
    {"id": "table_ember", "slot": "table", "name": "Brasa",
     "description": "Vermelhos e cobre para quem gosta de blefar sob pressão.",
     "free": True, "price_hint_cents": None, "label": "Grátis"},
    {"id": "table_galaxy", "slot": "table", "name": "Galáxia",
     "description": "Estrelas e reflexos espaciais para futuras temporadas.",
     "free": False, "price_hint_cents": 990, "label": "Em breve"},
    {"id": "frame_slate", "slot": "frame", "name": "Aço",
     "description": "Uma moldura discreta para sua câmera e avatar.",
     "free": True, "price_hint_cents": None, "label": "Padrão"},
    {"id": "frame_mint", "slot": "frame", "name": "Verde Menta",
     "description": "Um contorno luminoso com toque esmeralda.",
     "free": True, "price_hint_cents": None, "label": "Grátis"},
    {"id": "frame_violet", "slot": "frame", "name": "Violeta",
     "description": "Um brilho violeta para destacar sua presença.",
     "free": True, "price_hint_cents": None, "label": "Grátis"},
    {"id": "frame_royal", "slot": "frame", "name": "Coroa Dourada",
     "description": "Moldura dourada planejada para o futuro catálogo.",
     "free": False, "price_hint_cents": 690, "label": "Em breve"},
)

ITEMS = MappingProxyType({item["id"]: MappingProxyType(item) for item in _CATALOG})
FREE_IDS = frozenset(item["id"] for item in _CATALOG if item["free"])


class ShopError(ValueError):
    pass


class LockedCosmetic(ShopError):
    pass


def item_for(slot, product_id):
    if not isinstance(slot,str) or slot not in DEFAULTS or not isinstance(product_id,str):
        raise ShopError("Categoria ou item desconhecido.")
    item = ITEMS.get(product_id)
    if not item or item["slot"] != slot:
        raise ShopError("Esse item não pertence à categoria escolhida.")
    return item


def catalog():
    return {
        "phase": "visual_preview_no_payments",
        "title": "Loja do Blefe Color",
        "notice": "Nesta fase, itens gratuitos podem ser equipados. Itens premium são prévias, sem compras ou pagamentos.",
        "categories": [dict(x) for x in CATEGORIES],
        "items": [dict(x) for x in _CATALOG],
        "defaults": dict(DEFAULTS),
        "payments_enabled": False,
    }
