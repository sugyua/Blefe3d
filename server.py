"""Blefe 3D - authoritative multiplayer server."""
import asyncio, json, random, secrets, string, time, os
from pathlib import Path
from aiohttp import web, WSMsgType

ROOT = Path(__file__).parent / 'public'
ROOMS = {}
USERS = {}
COLORS=['red','yellow','green','blue']
ACTIONS=['skip','draw2','reverse','draw4']
LABEL={'skip':'BLOQUEIO','draw2':'+2','reverse':'INVERTER','draw4':'+4'}
def build_deck():
    cards=[]
    for color in COLORS:
        cards.append({'id':secrets.token_hex(5),'color':color,'rank':'0'})
        for n in range(1,10):
            for _ in range(2):cards.append({'id':secrets.token_hex(5),'color':color,'rank':str(n)})
        for a in ('skip','draw2','reverse'):
            for _ in range(2):cards.append({'id':secrets.token_hex(5),'color':color,'rank':a})
    for _ in range(4):
        for rank in ('wild','draw4'):cards.append({'id':secrets.token_hex(5),'color':'wild','rank':rank})
    random.shuffle(cards)
    return cards

def draw(room,p,n):
    for _ in range(n):
        if not room['deck'] and len(room['discard'])>1:
            top=room['discard'].pop()
            room['deck']=room['discard'];random.shuffle(room['deck']);room['discard']=[top]
        if room['deck']:p['hand'].append(room['deck'].pop())

def advance(room,pid,steps=1):
    a=room['players'];idx=next(i for i,p in enumerate(a) if p['id']==pid)
    for _ in range(steps):
        for __ in range(len(a)):
            idx=(idx+room['direction'])%len(a)
            if not a[idx]['out']:break
    return a[idx]


def emit(ws, type_, **data):
    if ws is not None and not ws.closed:
        asyncio.create_task(ws.send_json({'type':type_, **data}))

def send_room(room, type_, **data):
    for p in room['players']:
        emit(p.get('ws'),type_,**data)

def info(room):
    pending=room['pending']
    return {'code':room['code'],'host':room['host'],'started':room['started'],'mode':room['mode'],
    'players':[{'id':p['id'],'name':p['name'],'bot':p['bot'],'connected':p.get('ws') is not None and not p['ws'].closed if p.get('ws') else p['bot'],'cards':len(p['hand']),'strikes':0,'out':p['out'],'media':p.get('media',False)} for p in room['players']],
    'turn':room['turn'],'color':room['color'],'top':({'rank':'hidden','color':room['color']} if room.get('hidden_top') else room['top']),'direction':room['direction'],
    'pending':{'player':pending['player'],'claim':pending['claim'],'color':pending['color']} if pending else None,
    'last':room['last'],'winner':room.get('winner'),'deck_count':len(room['deck'])}

def sync(room):
    payload=info(room)
    for p in room['players']:
        emit(p.get('ws'),'state',state=payload,hand=p['hand'])

def notice(room,msg):
    send_room(room,'notice',message=msg)

def make_room(player, mode):
    code=''.join(random.choices(string.ascii_uppercase+string.digits,k=6))
    while code in ROOMS: code=''.join(random.choices(string.ascii_uppercase+string.digits,k=6))
    room={'code':code,'host':player['id'],'players':[player],'started':False,'mode':mode,'turn':None,'color':None,'top':None,'deck':[],'discard':[],'direction':1,'hidden_top':False,'pending':None,'last':None,'winner':None,'created':time.time()}
    ROOMS[code]=room
    player['room']=code
    return room

def alive(room):
    return [p for p in room['players'] if not p['out']]

def player_by_id(room, pid):
    return next((p for p in room['players'] if p['id']==pid),None)

def next_player(room,pid):
    a=room['players']; idx=next((i for i,p in enumerate(a) if p['id']==pid),-1)
    for j in range(1,len(a)+1):
        p=a[(idx+j)%len(a)]
        if not p['out']: return p
    return None

def start(room):
    if len(room['players'])<2:return False
    room['deck']=build_deck()
    for p in room['players']:
        p['hand']=[];p['strikes']=0;p['out']=False
        draw(room,p,7)
    i=next(i for i,c in enumerate(room['deck']) if c['rank'].isdigit())
    card=room['deck'].pop(i)
    room.update(started=True,turn=random.choice(room['players'])['id'],color=card['color'],
        top=card,discard=[card],pending=None,direction=1,hidden_top=False,last=None,winner=None)
    sync(room);notice(room,'Descarte por cor ou número; ações ficam ocultas e podem ser blefes!')
    bots_schedule(room)
    return True

def finalize(room,p):
    if not p['hand']:
        room['winner']=p['id'];room['turn']=None
        notice(room,p['name']+' venceu!')
        sync(room)
        return True
    return False

def apply_action(room,actor,kind,newcolor):
    target=advance(room,actor['id'])
    if kind in ('draw2','draw4'):
        n=2 if kind=='draw2' else 4
        draw(room,target,n)
        notice(room,f"{target['name']} comprou {n} cartas.")
    if kind=='reverse':room['direction']*=-1
    if kind in ('skip','draw2','draw4'):target=advance(room,target['id'])
    room['color']=newcolor
    room['hidden_top']=True
    room['turn']=target['id']
    finalize(room,actor)
    sync(room);bots_schedule(room)

def play(room,p,ids,claim=None,newcolor=None):
    if room['winner'] or room['turn']!=p['id']:return 'Não é sua vez.'
    if room['pending']:return 'Primeiro, aceite ou duvide da carta oculta.'
    if not isinstance(ids,list) or len(ids)!=1:return 'Selecione somente uma carta.'
    card=next((c for c in p['hand'] if c['id']==ids[0]),None)
    if not card:return 'Carta inválida.'
    if claim is not None:
        if claim not in ACTIONS:return 'Declaração inválida.'
        if claim=='draw4':
            if newcolor not in COLORS:return 'Escolha uma cor para o +4.'
            targetcolor=newcolor
        else:targetcolor=room['color']
        p['hand'].remove(card)
        room['pending']={'player':p['id'],'card':card,'claim':claim,'color':targetcolor}
        room['turn']=advance(room,p['id'])['id']
        room['last']=None
        notice(room,p['name']+' declarou '+LABEL[claim]+' com a carta virada para baixo.')
        sync(room);bots_schedule(room)
        return None
    if card['rank'] in ACTIONS:return 'Cartas de ação precisam de declaração oculta.'
    if card['color']!='wild' and card['color']!=room['color'] and (room.get('hidden_top') or card['rank']!=room['top']['rank']):
        return 'A carta deve corresponder à cor ou ao número.'
    if card['color']=='wild' and newcolor not in COLORS:return 'Escolha uma cor.'
    p['hand'].remove(card);room['discard'].append(card);room['top']=card
    room['color']=newcolor if card['color']=='wild' else card['color'];room['hidden_top']=False
    room['turn']=advance(room,p['id'])['id']
    room['last']=None
    notice(room,p['name']+' jogou '+card['rank']+'.')
    finalize(room,p);sync(room);bots_schedule(room)
    return None

def resolve(room,p,doubt):
    q=room['pending']
    if not q or room['turn']!=p['id'] or room['winner']:return 'Não há blefe pendente para você.'
    actor=player_by_id(room,q['player'])
    actual=q['card'];claim=q['claim']
    truthful=(actual['rank']==claim and (actual['color']==room['color'] or actual['color']=='wild'))
    room['pending']=None
    room['discard'].append(actual);room['top']=actual;room['hidden_top']=False
    room['last']={'accuser':p['name'],'accused':actor['name'],'lie':not truthful,
        'cards':[actual],'loser':actor['name'] if not truthful else p['name'],'out':False,
        'claim':claim,'accepted':not doubt}
    if doubt:
        if truthful:
            n=(2 if claim=='draw2' else 4 if claim=='draw4' else 0)+1
            draw(room,p,n)
            notice(room,p['name']+f' duvidou errado e comprou {n} carta(s).')
            if claim=='reverse':room['direction']*=-1
            room['color']=q['color'];room['turn']=advance(room,p['id'])['id']
            finalize(room,actor)
        else:
            draw(room,actor,2)
            room['turn']=p['id']
            notice(room,actor['name']+' foi pego blefando e comprou 2 cartas!')
        send_room(room,'reveal',result=room['last'])
        sync(room);bots_schedule(room)
        return None
    if truthful:
        notice(room,p['name']+' aceitou '+LABEL[claim]+'.')
        apply_action(room,actor,claim,q['color'])
    else:
        # Undetected bluff: declared action takes effect.
        notice(room,p['name']+' acreditou no blefe.')
        apply_action(room,actor,claim,q['color'])
    return None

def draw_turn(room,p):
    if room['winner'] or room['turn']!=p['id'] or room['pending']:
        return 'Você não pode comprar agora.'
    draw(room,p,1)
    room['turn']=advance(room,p['id'])['id']
    notice(room,p['name']+' comprou uma carta e passou.')
    sync(room);bots_schedule(room)
    return None

def bots_schedule(room):
    if room['mode']!='training' or room['winner'] or not room['started']:return
    current=player_by_id(room,room['turn'])
    if not current or not current['bot']:return
    async def move(code,pid):
        await asyncio.sleep(1.1)
        r=ROOMS.get(code)
        if not r or r['winner'] or r['turn']!=pid:return
        bot=player_by_id(r,pid)
        if r['pending']:
            resolve(r,bot,random.random()<.32);return
        cards=bot['hand']
        playable=[c for c in cards if c['color']=='wild' or c['color']==r['color'] or (not r.get('hidden_top') and c['rank']==r['top']['rank'])]
        actions=[c for c in cards if c['rank'] in ACTIONS]
        if actions and random.random()<.33:
            card=random.choice(actions)
            claim=card['rank'] if random.random()<.78 else random.choice(ACTIONS)
            play(r,bot,[card['id']],claim,random.choice(COLORS));return
        if playable:
            card=random.choice(playable)
            if card['rank'] in ACTIONS:play(r,bot,[card['id']],card['rank'],random.choice(COLORS))
            else:play(r,bot,[card['id']],None,random.choice(COLORS))
        else:draw_turn(r,bot)
    asyncio.create_task(move(room['code'],current['id']))

def create_player(name,ws,token=None):
    pid=token or secrets.token_urlsafe(18)
    return {'id':pid,'name':str(name).strip()[:20] or 'Jogador','ws':ws,'hand':[],'strikes':0,'out':False,'bot':False,'room':None,'media':False}

def error(ws,message): emit(ws,'error',message=message)

async def websocket(request):
    ws=web.WebSocketResponse(heartbeat=20,max_msg_size=100000)
    await ws.prepare(request)
    p=None
    try:
        async for msg in ws:
            if msg.type!=WSMsgType.TEXT: continue
            try: d=json.loads(msg.data)
            except Exception: continue
            t=d.get('type')
            if t=='hello':
                token=d.get('token')
                if token in USERS:
                    p=USERS[token]
                    old=p.get('ws')
                    if old and old!=ws: await old.close()
                    p['ws']=ws
                    if p['room'] in ROOMS: sync(ROOMS[p['room']]);notice(ROOMS[p['room']],f"{p['name']} reconectou.")
                else:
                    p=create_player(d.get('name'),ws)
                    USERS[p['id']]=p
                emit(ws,'welcome',id=p['id'],room=p['room'])
                continue
            if not p: error(ws,'Identificação necessária.');continue
            room=ROOMS.get(p['room']) if p['room'] else None
            if t=='create':
                if room: error(ws,'Você já está em uma sala.');continue
                mode='training' if d.get('mode')=='training' else 'online'
                room=make_room(p,mode)
                if mode=='training':
                    for i in range(3):
                        b=create_player(['Bot Ana','Bot Beto','Bot Cris'][i],None);b['bot']=True;b['id']='BOT'+str(i)+room['code'];b['room']=room['code'];room['players'].append(b)
                    start(room)
                else: sync(room)
            elif t=='join':
                if room: error(ws,'Saia da sala anterior primeiro.');continue
                code=str(d.get('code','')).upper().strip();room=ROOMS.get(code)
                if not room: error(ws,'Sala não encontrada.');continue
                if room['started'] or len(room['players'])>=4 or room['mode']=='training': error(ws,'Sala indisponível.');continue
                room['players'].append(p);p['room']=code;sync(room);notice(room,f"{p['name']} entrou na sala.")
            elif t=='start':
                if not room or room['host']!=p['id']: error(ws,'Somente o anfitrião pode iniciar.');continue
                if not start(room): error(ws,'É preciso ter pelo menos dois jogadores.')
            elif t=='play':
                if not room or not room['started']: error(ws,'Partida não iniciada.');continue
                res=play(room,p,d.get('cards'),d.get('claim'),d.get('color'))
                if res: error(ws,res)
            elif t=='challenge':
                if not room: continue
                res=resolve(room,p,True)
                if res: error(ws,res)
            elif t=='accept' and room:
                res=resolve(room,p,False)
                if res:error(ws,res)
            elif t=='draw' and room:
                res=draw_turn(room,p)
                if res:error(ws,res)
            elif t=='leave':
                if room:
                    original=room['players']
                    if room['started']: p['out']=True
                    room['players']=[x for x in original if x['id']!=p['id']]
                    p['room']=None;p['hand']=[];p['media']=False
                    if not room['players'] or room['mode']=='training':
                        ROOMS.pop(room['code'],None)
                    else:
                        if room['host']==p['id']:room['host']=room['players'][0]['id']
                        if room['started']:
                            if room['turn']==p['id']:
                                nextp=next_player(room,p['id']);room['turn']=nextp['id'] if nextp else None
                            sync(room)
                        sync(room);notice(room,f"{p['name']} saiu.")
                    emit(ws,'left')
            elif t=='media_ready' and room:
                p['media']=bool(d.get('ready'))
                sync(room)
                send_room(room,'media_peer',id=p['id'],ready=p['media'])
            elif t=='signal' and room:
                dest=player_by_id(room,d.get('to'))
                if dest and not dest['bot']:
                    emit(dest.get('ws'),'signal',sender=p['id'],signal=d.get('signal'))
    finally:
        if p and p.get('ws') is ws:
            p['ws']=None;p['media']=False
            if p['room'] in ROOMS:
                r=ROOMS[p['room']];sync(r);send_room(r,'media_peer',id=p['id'],ready=False)
                notice(r,f"{p['name']} desconectou (pode reconectar).")
    return ws

async def index(request):return web.FileResponse(ROOT/'index.html')
async def health(request):return web.json_response({'ok':True,'rooms':len(ROOMS)})

app=web.Application()
app.router.add_get('/',index)
app.router.add_get('/ws',websocket)
app.router.add_get('/health',health)
app.router.add_static('/static/',ROOT)
if __name__=='__main__':
    port=int(os.getenv('PORT','8080'))
    print(f'Blefe 3D pronto: http://localhost:{port}')
    web.run_app(app,host='0.0.0.0',port=port)
