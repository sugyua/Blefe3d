'use strict';
const $=id=>document.getElementById(id);
const COR={red:'VERMELHO',yellow:'AMARELO',green:'VERDE',blue:'AZUL',wild:'CORINGA'};
const ACAO={skip:'BLOQUEIO',draw2:'+2',reverse:'INVERTER',draw4:'+4',wild:'CORINGA',hidden:'CARTA OCULTA'};
const nomeCarta=c=>!c?'carta':(ACAO[c.rank]||c.rank)+(c.color&&c.color!=='wild'?' '+(COR[c.color]||''):'');
const state={id:null,room:null,hand:[],selected:new Set(),ws:null,token:localStorage.getItem('blefe_token'),name:localStorage.getItem('blefe_name')||'',stream:null,pcs:new Map(),remoteStreams:new Map(),micEnabled:true,camEnabled:false,voiceReady:false,volumes:new Map(),selectedColor:'red',claim:null,previewStream:null,lastAnimatedMove:null,mediaConnecting:false,revealTimers:[]};
$('nickname').value=state.name;
function toast(s){const el=$('toast');el.textContent=s;el.style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.style.display='none',3500)}
function send(type,data={}){if(state.ws?.readyState===1)state.ws.send(JSON.stringify({type,...data}));else toast('Servidor desconectado. Reconectando...')}
function connection(){const proto=location.protocol==='https:'?'wss':'ws';const ws=new WebSocket(proto+'://'+location.host+'/ws');state.ws=ws;$('connection').textContent='● Conectando';
ws.onopen=()=>{$('connection').textContent='● Conectado';send('hello',{name:state.name||'Jogador',token:state.token})};
ws.onmessage=async e=>{let m;try{m=JSON.parse(e.data)}catch{return}
if(m.type==='welcome'){state.id=m.id;state.token=m.id;localStorage.setItem('blefe_token',m.id);if(m.room){$('lobby').hidden=true;$('game').hidden=false;if(state.voiceReady)send('media_ready',{ready:true})}}
else if(m.type==='state'){state.room=m.state;state.hand=m.hand||[];state.selected=new Set([...state.selected].filter(x=>state.hand.some(c=>c.id===x)));render();if(m.state.move&&m.state.move.id!==state.lastAnimatedMove){state.lastAnimatedMove=m.state.move.id;animateMove(m.state.move)}}
else if(m.type==='notice'){$('logline').textContent=m.message}
else if(m.type==='error')toast(m.message)
else if(m.type==='reveal')showReplay(m.result)
else if(m.type==='left'){state.room=null;state.hand=[];state.selected.clear();$('game').hidden=true;$('lobby').hidden=false;closeMedia()}
else if(m.type==='media_peer'){if(m.id!==state.id){if(m.ready&&state.voiceReady&&state.id<m.id){const peer=state.room?.players.find(p=>p.id===m.id);if(peer?.media)await connectPeer(m.id)}else if(!m.ready)removePeer(m.id)}}
else if(m.type==='signal')await onSignal(m.sender,m.signal)};
ws.onclose=()=>{if(state.ws!==ws)return;$('connection').textContent='● Desconectado';for(const id of [...state.pcs.keys()])removePeer(id,false);renderPeers();setTimeout(connection,1600)};ws.onerror=()=>{}}
function startNamed(type,extra){const name=$('nickname').value.trim()||'Jogador';state.name=name;localStorage.setItem('blefe_name',name);if(!state.id){toast('Conectando ao servidor...');return}send(type,{...extra,name})}
$('training').onclick=()=>startNamed('create',{mode:'training'});
$('create').onclick=()=>startNamed('create',{mode:'online'});
$('join').onclick=()=>startNamed('join',{code:$('roomcode').value.trim().toUpperCase()});
$('startBtn').onclick=()=>send('start');$('leaveBtn').onclick=()=>{if(confirm('Sair da partida?'))send('leave')};
$('copyInvite').onclick=async()=>{const link=location.origin+'/?sala='+(state.room?.code||'');try{await navigator.clipboard.writeText(link);toast('Link da sala copiado!')}catch{prompt('Copie o convite:',link)}};
$('helpBtn').onclick=()=>{$('guide').hidden=false};$('closeGuide').onclick=()=>{$('guide').hidden=true};$('closeReplay').onclick=closeReplay;
$('play').onclick=()=>{if(!state.selected.size)return;const c=state.hand.find(c=>state.selected.has(c.id));if(!c)return;if(['skip','draw2','reverse','draw4'].includes(c.rank)){state.claim=c.rank;$('claimPanel').hidden=false;$('colors').hidden=c.rank!=='draw4';return}if(c.rank==='wild'){state.claim=null;$('claimPanel').hidden=false;document.querySelector('.claimGrid').hidden=true;$('colors').hidden=false;return}send('play',{cards:[...state.selected]})};
$('challenge').onclick=()=>send('challenge');
$('accept').onclick=()=>send('accept');
$('draw').onclick=()=>send('draw');
$('bluff').onclick=()=>{if(!state.selected.size)return;state.claim=null;document.querySelector('.claimGrid').hidden=false;$('colors').hidden=true;$('claimPanel').hidden=false};
$('whatsappInvite').onclick=()=>{const code=state.room?.code||'';const link=location.origin+'/?sala='+code;const message='Vem jogar Blefe Color comigo! Sala: '+code+'\\n'+link;window.open('https://wa.me/?text='+encodeURIComponent(message),'_blank','noopener,noreferrer')};
$('cancelClaim').onclick=()=>{$('claimPanel').hidden=true};
for(const el of document.querySelectorAll('[data-color]')){el.onclick=()=>{state.selectedColor=el.dataset.color;for(const b of document.querySelectorAll('[data-color]'))b.style.outline=b===el?'3px solid white':'';if(state.claim||document.querySelector('.claimGrid').hidden){send('play',{cards:[...state.selected],claim:state.claim,color:state.selectedColor});$('claimPanel').hidden=true;state.claim=null;document.querySelector('.claimGrid').hidden=false}}}
for(const el of document.querySelectorAll('[data-claim]')){el.onclick=()=>{state.claim=el.dataset.claim;if(state.claim==='draw4'){$('colors').hidden=false;toast('Selecione a cor do +4.')}else{send('play',{cards:[...state.selected],claim:state.claim,color:state.selectedColor});$('claimPanel').hidden=true;state.claim=null}}};
function makeCard(c){const el=document.createElement('div');el.className='card uno '+(c.color||'wild');const b=document.createElement('b');b.textContent=({skip:'⊘',draw2:'+2',draw4:'+4',reverse:'⇄',wild:'★'})[c.rank]||c.rank;el.append(b);return el}
function render(){const s=state.room;if(!s)return;
$('lobby').hidden=true;$('game').hidden=false;$('roomLabel').textContent=s.mode==='training'?'TREINAMENTO':'SALA '+s.code;$('waiting').hidden=s.started;
const me=s.players.find(p=>p.id===state.id),actor=s.players.find(p=>p.id===s.turn),myturn=!!s.started&&!s.winner&&s.turn===state.id,winner=s.players.find(p=>p.id===s.winner);
$('turnBanner').textContent=winner?'🏆 '+winner.name+' VENCEU!':!s.started?'AGUARDANDO JOGADORES':myturn?'🟡 SUA VEZ DE JOGAR':'⏳ VEZ DE '+(actor?.name?.toUpperCase()||'...');
$('turnBanner').classList.toggle('myturn',myturn);
$('strikes').textContent=state.hand.length+' CARTAS';
$('tableTarget').querySelector('b').textContent=s.pending?('CARTA OCULTA — '+({skip:'BLOQUEIO',draw2:'+2',draw4:'+4',reverse:'INVERTER'})[s.pending.claim]):((s.top?.rank==='hidden'?'CARTA OCULTA':(ACAO[s.top?.rank]||s.top?.rank||'—'))+' • '+(COR[s.color]||'—'));
$('tableCards').replaceChildren();
if(s.pending||s.top?.rank==='hidden'){const back=document.createElement('div');back.className='tableBack';back.setAttribute('aria-label','Carta virada para baixo');$('tableCards').append(back)}
else if(s.top)$('tableCards').append(makeCard(s.top));
$('hand').replaceChildren();
for(const c of state.hand){const el=makeCard(c);el.classList.toggle('selected',state.selected.has(c.id));el.onclick=()=>{if(!myturn||s.pending)return;if(state.selected.has(c.id))state.selected.delete(c.id);else{state.selected.clear();state.selected.add(c.id)}renderHandOnly()};$('hand').append(el)}
$('challenge').disabled=!myturn||!s.pending;
$('accept').disabled=!myturn||!s.pending;
$('draw').disabled=!myturn||!!s.pending;
$('bluff').disabled=!myturn||!state.selected.size||!!s.pending;
$('play').disabled=!myturn||!state.selected.size||!!s.pending;
$('play').textContent='JOGAR CARTA';
$('turnHint').textContent=winner?'Fim da partida. Crie outra sala para revanche.':!s.started?'Aguardando o anfitrião iniciar.':myturn?(s.pending?'Acredite na ação ou duvide da declaração.':'Selecione uma carta, ou compre uma e passe.'):'Aguardando '+(actor?.name||'jogador')+'...';
$('waitingTitle').textContent='Sala '+s.code;$('waitingList').textContent=s.players.map(x=>x.name+(x.id===s.host?' ★':'')).join('\\n')+'\\n'+s.players.length+'/4 jogadores';
$('startBtn').hidden=s.host!==state.id;$('startBtn').disabled=s.players.length<2;
renderPeers()}
function renderHandOnly(){for(const [i,el] of [...$('hand').children].entries())el.classList.toggle('selected',state.selected.has(state.hand[i].id));$('play').disabled=state.room?.turn!==state.id||!state.selected.size||!!state.room?.pending;$('bluff').disabled=$('play').disabled;$('play').textContent='JOGAR CARTA'}
function renderPeers(){const parent=$('peerCameras'),s=state.room;if(!s)return;
const others=s.players.filter(p=>p.id!==state.id);
const slots=[...others];while(slots.length<3)slots.push(null);slots.push(s.players.find(p=>p.id===state.id)||{id:state.id,name:'Você',bot:false,connected:true,cards:0});
parent.replaceChildren();
for(let i=0;i<4;i++){
const p=slots[i];const box=document.createElement('div');box.className='peer';
if(p&&s.turn===p.id)box.classList.add('current');
if(!p){const avatar=document.createElement('div');avatar.className='avatar';avatar.textContent='+';box.append(avatar);parent.append(box);continue}
box.dataset.peer=p.id;let stream=p.id===state.id?state.stream:state.remoteStreams.get(p.id);
const track=stream?.getVideoTracks()?.find(t=>t.readyState==='live');
if(track){const video=document.createElement('video');video.autoplay=true;video.playsInline=true;video.muted=true;video.srcObject=stream;if(p.id===state.id)video.style.transform='scaleX(-1)';box.append(video);video.play().catch(()=>{})}
else{const avatar=document.createElement('div');avatar.className='avatar';avatar.textContent=p.bot?'🤖':p.name.slice(0,1).toUpperCase();box.append(avatar)}
const tag=document.createElement('div');tag.className='tag';tag.textContent=(p.id===state.id?'VOCÊ':p.name)+(p.connected?'':' (offline)')+(s.turn===p.id?' • VEZ':'');box.append(tag);
if(!p.bot&&p.id!==state.id){const vol=document.createElement('input');vol.type='range';vol.min='0';vol.max='100';vol.value=String(state.volumes.get(p.id)??100);vol.className='peerVolume';vol.title='Volume individual de '+p.name;vol.oninput=()=>{state.volumes.set(p.id,Number(vol.value));const a=document.getElementById('audio-'+p.id);if(a)a.volume=Number(vol.value)/100};box.append(vol)}
parent.append(box);if(stream&&p.id!==state.id)attachAudio(p.id,stream)
}}
function closeReplay(){for(const t of state.revealTimers)clearTimeout(t);state.revealTimers=[];$('replay').hidden=true}
function showReplay(r){
  closeReplay();
  const modal=$('replay'),flip=$('revealFlip'),card=r.cards?.[0];
  const real=makeCard(card||{rank:'?',color:'wild'});
  real.id='revealActual';$('revealActual').replaceWith(real);
  flip.classList.remove('isFlipped');modal.classList.remove('showResult','correct','incorrect');modal.hidden=false;
  $('replayTitle').textContent='SERÁ QUE ERA BLEFE?';
  $('verdictEyebrow').textContent='REVELANDO A CARTA OCULTA';
  $('replayText').textContent=r.accuser+' desafiou '+r.accused+'.';
  $('penaltyLabel').textContent='';
  state.revealTimers.push(setTimeout(()=>flip.classList.add('isFlipped'),650));
  state.revealTimers.push(setTimeout(()=>{
    const acertou=!!r.lie, nome=r.accuser===state.room?.players.find(x=>x.id===state.id)?.name?'Você':r.accuser;
    modal.classList.add('showResult',acertou?'correct':'incorrect');
    $('replayTitle').textContent=acertou?'ACERTOU AO DUVIDAR!':'ERROU AO DUVIDAR!';
    $('verdictEyebrow').textContent=acertou?'ERA BLEFE!':'ERA VERDADE!';
    $('replayText').textContent=nome+' desconfiou de '+r.accused+'. A carta real era '+nomeCarta(card)+', e a declaração foi '+(ACAO[r.claim]||r.claim)+'.';
    $('penaltyLabel').textContent=r.loser+' comprou '+(r.penalty||2)+' carta(s).';
  },1250));
  state.revealTimers.push(setTimeout(()=>closeReplay(),6500));
}
function animateMove(move){
  const game=$('game');if(game.hidden||!move)return;
  const target=$('tableCards');if(!target)return;
  const layer=$('effectsLayer'),card=move.hidden?document.createElement('div'):makeCard(move.card||{rank:'?',color:'wild'});
  if(move.hidden){card.className='flightBack';card.textContent='?';}
  card.classList.add('flyingCard');
  const from=move.player===state.id?$('hand'):(document.querySelector('.peer[data-peer="'+CSS.escape(move.player)+'"]')||$('topArea'));
  const a=from.getBoundingClientRect(),b=target.getBoundingClientRect();
  card.style.left=(a.left+a.width/2-30)+'px';card.style.top=(a.top+a.height/2-43)+'px';
  layer.append(card);
  const dx=b.left+b.width/2-(a.left+a.width/2),dy=b.top+b.height/2-(a.top+a.height/2);
  if(card.animate){
    const anim=card.animate([{transform:'translate3d(0,0,0) rotate(-19deg) scale(1.08)',opacity:.93},{transform:'translate3d('+dx+'px,'+dy+'px,0) rotate(8deg) scale(.78)',opacity:1}],{duration:650,easing:'cubic-bezier(.2,.85,.25,1)',fill:'forwards'});
    anim.onfinish=()=>{card.remove();target.classList.remove('landed');void target.offsetWidth;target.classList.add('landed')};
    setTimeout(()=>card.remove(),900);
  }else{card.style.transform='translate('+dx+'px,'+dy+'px)';setTimeout(()=>card.remove(),700)}
  if(move.hidden){$('tableTarget').classList.remove('hiddenFlash');void $('tableTarget').offsetWidth;$('tableTarget').classList.add('hiddenFlash')}
}
const rtcConfig={iceServers:[{urls:'stun:stun.l.google.com:19302'},{urls:'stun:stun1.l.google.com:19302'}]};
async function startVoice(){if(!navigator.mediaDevices?.getUserMedia){toast('Voz/câmera exigem HTTPS ou localhost.');return}try{state.stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true},video:false});state.voiceReady=true;state.micEnabled=true;renderPeers();$('voiceBtn').textContent='🎙 Voz ligada';$('micBtn').disabled=false;send('media_ready',{ready:true});for(const p of (state.room?.players||[]))if(p.id!==state.id&&p.media)await connectPeer(p.id,true);toast('Microfone ativado.')}catch(e){toast('Permita o acesso ao microfone: '+e.message)}}
$('voiceBtn').onclick=()=>{if(!state.voiceReady)startVoice();else{closeMedia();toast('Voz desativada.')}};
$('micBtn').onclick=()=>{state.micEnabled=!state.micEnabled;for(const t of state.stream?.getAudioTracks()||[])t.enabled=state.micEnabled;$('micBtn').textContent=state.micEnabled?'🔊 Mic ligado':'🔇 Mic mudo'};
$('camBtn').onclick=async()=>{if(!state.voiceReady){toast('Ative a voz primeiro.');return}if(!state.camEnabled){try{const s=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:320,height:240}});const track=s.getVideoTracks()[0];state.stream.addTrack(track);state.camEnabled=true;renderPeers();$('camBtn').textContent='📷 Câmera ligada';for(const [id,pc] of state.pcs){pc.addTrack(track,state.stream);await offer(pc,id)}}catch(e){toast('Não foi possível abrir a câmera: '+e.message)}}else{for(const t of state.stream.getVideoTracks()){t.stop();state.stream.removeTrack(t)}state.camEnabled=false;renderPeers();$('camBtn').textContent='📷 Câmera';for(const [id,pc] of state.pcs){for(const sender of pc.getSenders())if(sender.track?.kind==='video')pc.removeTrack(sender);await offer(pc,id)}}};
async function connectPeer(id,initiator=false){if(!state.voiceReady||id===state.id||state.pcs.has(id))return;const pc=new RTCPeerConnection(rtcConfig);state.pcs.set(id,pc);for(const track of state.stream.getTracks())pc.addTrack(track,state.stream);pc.onicecandidate=e=>{if(e.candidate)send('signal',{to:id,signal:{candidate:e.candidate}})};pc.ontrack=e=>{const stream=e.streams[0]||new MediaStream([e.track]);state.remoteStreams.set(id,stream);renderPeers()};if(initiator)await offer(pc,id)}
async function offer(pc,id){try{if(pc.signalingState!=='stable')return;await pc.setLocalDescription(await pc.createOffer());send('signal',{to:id,signal:{description:pc.localDescription.toJSON()}})}catch(e){console.warn('offer',e)}}
async function onSignal(id,signal){if(!state.voiceReady||!signal)return;let pc=state.pcs.get(id);if(!pc){await connectPeer(id);pc=state.pcs.get(id)}try{if(signal.description){const desc=signal.description;if(desc.type==='offer'){if(pc.signalingState!=='stable')await pc.setLocalDescription({type:'rollback'});await pc.setRemoteDescription(desc);await pc.setLocalDescription(await pc.createAnswer());send('signal',{to:id,signal:{description:pc.localDescription.toJSON()}})}else if(desc.type==='answer'&&pc.signalingState==='have-local-offer')await pc.setRemoteDescription(desc)}else if(signal.candidate)await pc.addIceCandidate(signal.candidate)}catch(e){console.warn('WebRTC',e)}}
function attachAudio(id,stream){let audio=document.getElementById('audio-'+id);if(!audio){audio=document.createElement('audio');audio.id='audio-'+id;audio.autoplay=true;document.body.append(audio)}if(audio.srcObject!==stream)audio.srcObject=stream;audio.volume=(state.volumes.get(id)??100)/100;audio.play().catch(()=>{})}
function removePeer(id){state.pcs.get(id)?.close();state.pcs.delete(id);state.remoteStreams.delete(id);document.getElementById('audio-'+id)?.remove();if(state.room)renderPeers()}
function closeMedia(){send('media_ready',{ready:false});for(const id of [...state.pcs.keys()])removePeer(id);for(const t of state.stream?.getTracks()||[])t.stop();state.stream=null;state.voiceReady=false;state.camEnabled=false;if(state.room)renderPeers();$('voiceBtn').textContent='🎙 Ativar voz';$('camBtn').textContent='📷 Câmera';$('micBtn').disabled=true}
const invitation=new URLSearchParams(location.search).get('sala');if(invitation){$('roomcode').value=invitation;toast('Informe seu nome e entre na sala pelo código.')}connection();