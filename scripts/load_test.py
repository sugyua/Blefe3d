#!/usr/bin/env python3
"""Blefe Color — carga moderada de WebSockets (sem voz ou vídeo).

Exemplos:
  python scripts/load_test.py --clients 4,8,16,32
  python scripts/load_test.py --url https://blefe3d-teste.onrender.com --clients 4,8,16 --allow-production

Não teste um servidor público sem autorização. O teste cria salas PRIVADAS
temporárias, inicia rodadas com valor de entrada fictício zero e libera
as conexões ao final. O limite seguro padrão é de até 64 conexões.
"""
import argparse
import asyncio
import math
import statistics
import time
from urllib.parse import urlparse

import aiohttp


async def receive_type(ws, target, timeout=8):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        msg=await asyncio.wait_for(ws.receive(),deadline-time.monotonic())
        if msg.type==aiohttp.WSMsgType.TEXT:
            try: obj=msg.json()
            except ValueError: continue
            if obj.get('type')=='error':
                raise RuntimeError(obj.get('message','Erro do servidor'))
            if obj.get('type')==target:return obj
        else:
            raise RuntimeError('WebSocket fechado antes de '+target)
    raise TimeoutError('Sem resposta '+target)


async def open_player(session,base,name):
    started=time.perf_counter()
    url=('wss' if base.startswith('https:') else 'ws')+'://'+urlparse(base).netloc+'/ws'
    ws=await session.ws_connect(url,heartbeat=15,timeout=aiohttp.ClientWSTimeout(ws_close=5))
    await ws.send_json({'type':'hello','name':name})
    await receive_type(ws,'welcome')
    return ws,round((time.perf_counter()-started)*1000,1)


async def one_group(session,base,number):
    clients=[];latencies=[]
    try:
        host,ms=await open_player(session,base,'Teste-'+str(number)+'-0')
        clients.append(host);latencies.append(ms)
        await host.send_json({'type':'create','mode':'online','stake':0,
                              'visibility':'private','wallet_type':'test'})
        state=await receive_type(host,'state')
        code=state['state']['code']
        for i in range(1,4):
            ws,ms=await open_player(session,base,f'Teste-{number}-{i}')
            clients.append(ws);latencies.append(ms)
            await ws.send_json({'type':'join','code':code,'accept_stake_cents':0,
                                'wallet_type':'test'})
            await receive_type(ws,'state')
        await host.send_json({'type':'start'})
        return clients,latencies
    except Exception:
        for ws in clients:
            await ws.close()
        raise


async def run_level(session,url,n,hold):
    groups=n//4;remainder=n%4
    # The server supports four per game. A remainder gets a lobby host.
    clients=[];latencies=[];errors=[];start=time.perf_counter()
    try:
        for i in range(groups):
            try:
                created,ms=await one_group(session,url,i)
                clients.extend(created);latencies.extend(ms)
            except Exception as e:errors.append(str(e))
        for i in range(remainder):
            try:
                ws,ms=await open_player(session,url,'Teste-extra-'+str(i))
                clients.append(ws);latencies.append(ms)
            except Exception as e:errors.append(str(e))
        await asyncio.sleep(hold)
        health_started=time.perf_counter()
        try:
            async with session.get(url+'/health',timeout=aiohttp.ClientTimeout(total=8)) as response:
                response.raise_for_status()
                await response.json()
            health_ms=round((time.perf_counter()-health_started)*1000,1)
        except Exception as e:
            health_ms='falhou: '+str(e)
        if latencies:
            observed=sorted(latencies)
            p95=observed[min(len(observed)-1,math.ceil(.95*len(observed))-1)]
            median=statistics.median(observed)
        else:p95=median=0
        return {
            'solicitadas':n,'conectadas':len(clients),
            'falhas':len(errors),'erros':errors[:3],
            'conexao_mediana_ms':round(median,1),
            'conexao_p95_ms':p95,
            'health_ms':health_ms,
            'duracao_s':round(time.perf_counter()-start,1)
        }
    finally:
        for ws in clients:
            try:await ws.send_json({'type':'leave'})
            except Exception:pass
        await asyncio.gather(*(ws.close() for ws in clients),return_exceptions=True)


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://localhost:8080')
    parser.add_argument('--clients',default='4,8,16,32',help='Níveis separados por vírgula')
    parser.add_argument('--hold',type=float,default=5.0)
    parser.add_argument('--allow-production',action='store_true',
                        help='Autorização explícita para testar um servidor fora de localhost')
    args=parser.parse_args()
    url=args.url.rstrip('/')
    target=urlparse(url)
    if target.scheme not in ('http','https'):parser.error('URL HTTP ou HTTPS inválida')
    if target.hostname not in ('localhost','127.0.0.1') and not args.allow_production:
        parser.error('Para executar em produção, use --allow-production.')
    try:levels=[int(x) for x in args.clients.split(',')]
    except ValueError:parser.error('--clients inválido')
    if not levels or any(n<1 or n>64 for n in levels):
        parser.error('Níveis devem ter entre 1 e 64 jogadores de teste.')
    if not 1<=args.hold<=15:parser.error('--hold deve estar entre 1 e 15 segundos.')
    print('Teste autorizado:',url,'| níveis:',levels,'| voz/vídeo: NÃO')
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=80)) as session:
        for level in levels:
            result=await run_level(session,url,level,args.hold)
            print(result,flush=True)
            if result['falhas'] or result['conectadas']<level:
                print('Interrompido: erros no nível atual, não aumentar a carga.')
                break
    print('Fim. O teste mede sinalização WebSocket, não a capacidade de câmera, microfone ou TURN.')


if __name__=='__main__':
    asyncio.run(main())
