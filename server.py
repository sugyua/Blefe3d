"""Blefe 3D - authoritative multiplayer server."""
import asyncio, json, random, secrets, string, time, os
from pathlib import Path
from aiohttp import web, WSMsgType

ROOT = Path(__file__).parent / 'public'
ROOMS = {}
USERS = {}
SUITS = ['♠','♥','♣','♦']
RANKS = ['A','Q','K']

def emit(ws, type_, **data):
    if ws is not None and not ws.closed:
        asyncio.create_task(ws.send_json({'type':type_, **data}))

def send_room(room, type_, **data):
    for p in room['players']:
        emit(p.get('ws'),type_,**data)

def info(room):
    return {'code':room['code'], 'host':room['host'], 'started':room['started'], 'mode':room['mode'],
            'players':[{'id':p['id'],'name':p['name'],'bot':p['bot'],'connected':p.get('ws') is not None and not p['ws'].closed if p.get('ws') else p['bot'], 'cards':len(p['hand']), 'strikes':p['strikes'], 'out':p['out'], 'media':p.get('media',False)} for p in room['players']],
            'turn':room['turn'], 'target':room['target'], 'pending':{'player':room['pending']['player'],'count':len(room['pending']['cards'])} if room['pending'] else None,
            'last':room['last'], 'winner':room.get('winner')}

def sync(room):
    payload=info(room)
    for p in room['players']:
        emit(p.get('ws'),'state',state=payload,hand=p['hand'])

def notice(room,msg):
    send_room(room,'notice',message=msg)

def make_room(player, mode):
    code=''.join(random.choices(string.ascii_uppercase+string.digits,k=6))
    while code in ROOMS: code=''.join(random.choices(string.ascii_uppercase+string.digits,k=6))
    room={'code':code,'host':player['id'],'players':[player],'started':False,'mode':mode,'turn':None,'target':None,'pending':None,'last':None,'winner':None,'created':time.time()}
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

def new_target(): return random.choice(RANKS)

def start(room):
    players=room['players']
    if len(players)<2: return False
    deck=[{'id':secrets.token_hex(4),'rank':r,'suit':SUITS[i%4]} for r in RANKS for i in range(8)]
    deck += [{'id':secrets.token_hex(4),'rank':'J','suit':'★'} for _ in range(4)]
    random.shuffle(deck)
    for p in players:
        p['hand']=[deck.pop() for _ in range(5)]
        p['strikes']=0; p['out']=False
    room.update(started=True,turn=random.choice(players)['id'],target=new_target(),pending=None,last=None,winner=None)
    sync(room); notice(room,'A partida começou! J vale como coringa. Cada jogador pode receber até 3 penalidades.')
    bots_schedule(room)
    return True

def finish_if_winner(room):
    a=alive(room)
    if len(a)==1:
        room['winner']=a[0]['id']; room['turn']=None; room['pending']=None
        notice(room,f"{a[0]['name']} venceu a partida!")
        sync(room); return True
    return False

def commit_pending(room):
    pending=room['pending']
    if not pending: return False
    p=player_by_id(room,pending['player'])
    room['pending']=None
    if not p['hand'] and not p['out']:
        room['winner']=p['id']; room['turn']=None
        notice(room,f"{p['name']} ficou sem cartas e venceu!")
        sync(room); return True
    return False

def play(room,p,ids):
    if room['winner'] or room['turn'] != p['id'] or p['out']: return 'Não é sua vez.'
    if not isinstance(ids,list) or not (1<=len(ids)<=3) or len(set(ids))!=len(ids): return 'Selecione de 1 a 3 cartas.'
    selected=[c for c in p['hand'] if c['id'] in ids]
    if len(selected)!=len(ids): return 'Cartas inválidas.'
    if commit_pending(room): return 'A partida terminou.'
    p['hand']=[c for c in p['hand'] if c['id'] not in ids]
    room['pending']={'player':p['id'],'cards':selected}
    nxt=next_player(room,p['id']);room['turn']=nxt['id'] if nxt else None
    room['last']=None
    notice(room,f"{p['name']} declarou {len(selected)} carta(s) {room['target']}. Verdade ou blefe?")
    sync(room);bots_schedule(room)
    return None

def challenge(room,p):
    pending=room['pending']
    if room['winner'] or room['turn']!=p['id'] or not pending: return 'Não é possível duvidar agora.'
    accused=player_by_id(room,pending['player']); cards=pending['cards']
    lie=any(c['rank'] not in (room['target'],'J') for c in cards)
    loser=accused if lie else p
    loser['strikes']+=1
    if loser['strikes']>=3: loser['out']=True
    room['last']={'accuser':p['name'],'accused':accused['name'],'lie':lie,'cards':cards,'loser':loser['name'],'out':loser['out']}
    room['pending']=None
    send_room(room,'reveal',result=room['last'])
    notice(room,f"{'BLEFE!' if lie else 'VERDADE!'} {loser['name']} recebeu uma penalidade ({loser['strikes']}/3).")
    if finish_if_winner(room): return None
    if not accused['hand'] and not accused['out'] and not lie:
        room['winner']=accused['id'];room['turn']=None
        notice(room,f"{accused['name']} ficou sem cartas e venceu!");sync(room);return None
    room['target']=new_target()
    newturn=loser if not loser['out'] and loser['hand'] else next_player(room,loser['id'])
    if not newturn or not newturn['hand']:
        candidates=[x for x in alive(room) if x['hand']]
        newturn=candidates[0] if candidates else None
    if not newturn:
        a=alive(room); room['winner']=min(a,key=lambda x:x['strikes'])['id'] if a else None
        room['turn']=None
    else: room['turn']=newturn['id']
    sync(room); bots_schedule(room)
    return None

def bots_schedule(room):
    if room['mode']!='training' or not room['started'] or room['winner']: return
    p=player_by_id(room,room['turn'])
    if p and p['bot']:
        async def bot_move(code,pid):
            await asyncio.sleep(1.5)
            r=ROOMS.get(code)
            if not r or r['turn']!=pid or r['winner']: return
            b=player_by_id(r,pid)
            if r['pending'] and random.random()<0.30:
                challenge(r,b);return
            good=[c for c in b['hand'] if c['rank'] in (r['target'],'J')]
            chosen=random.choice(good) if good and random.random()<0.76 else random.choice(b['hand'])
            play(r,b,[chosen['id']])
        asyncio.create_task(bot_move(room['code'],p['id']))

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
                res=play(room,p,d.get('cards'))
                if res: error(ws,res)
            elif t=='challenge':
                if not room: continue
                res=challenge(room,p)
                if res: error(ws,res)
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
                            finish_if_winner(room)
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
