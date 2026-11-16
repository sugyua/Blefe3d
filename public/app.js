'use strict';
const $=id=>document.getElementById(id);
const state={id:null,room:null,hand:[],selected:new Set(),ws:null,token:localStorage.getItem('blefe_token'),name:localStorage.getItem('blefe_name')||'',stream:null,pcs:new Map(),remoteStreams:new Map(),micEnabled:true,camEnabled:false,voiceReady:false,volumes:new Map(),selectedColor:'red',claim:null};
$('nickname').value=state.name;
function toast(s){const el=$('toast');el.textContent=s;el.style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.style.display='none',3500)}
function send(type,data={}){if(state.ws?.readyState===1)state.ws.send(JSON.stringify({type,...data}));else toast('Servidor desconectado. Reconectando...')}
function connection(){const proto=location.protocol==='https:'?'wss':'ws';const ws=new WebSocket(proto+'://'+location.host+'/ws');state.ws=ws;$('connection').textContent='● Conectando';
ws.onopen=()=>{$('connection').textContent='● Online';send('hello',{name:state.name||'Jogador',token:state.token})};
ws.onmessage=async e=>{let m;try{m=JSON.parse(e.data)}catch{return}
if(m.type==='welcome'){state.id=m.id;state.token=m.id;localStorage.setItem('blefe_token',m.id);if(m.room){$('lobby').hidden=true;$('game').hidden=false}}
else if(m.type==='state'){state.room=m.state;state.hand=m.hand||[];state.selected=new Set([...state.selected].filter(x=>state.hand.some(c=>c.id===x)));render()}
else if(m.type==='notice'){$('logline').textContent=m.message}
else if(m.type==='error')toast(m.message)
else if(m.type==='reveal')showReplay(m.result)
else if(m.type==='left'){state.room=null;state.hand=[];state.selected.clear();$('game').hidden=true;$('lobby').hidden=false;closeMedia()}
else if(m.type==='media_peer'){if(m.id!==state.id){if(m.ready&&state.voiceReady){const peer=state.room?.players.find(p=>p.id===m.id);if(peer?.media)await connectPeer(m.id,true)}else if(!m.ready)removePeer(m.id)}}
else if(m.type==='signal')await onSignal(m.sender,m.signal)};
ws.onclose=()=>{if(state.ws!==ws)return;$('connection').textContent='● Offline';for(const id of [...state.pcs.keys()])removePeer(id);setTimeout(connection,1600)};ws.onerror=()=>{}}
function startNamed(type,extra){const name=$('nickname').value.trim()||'Jogador';state.name=name;localStorage.setItem('blefe_name',name);if(!state.id){toast('Conectando ao servidor...');return}send(type,extra)}
$('training').onclick=()=>startNamed('create',{mode:'training'});
$('create').onclick=()=>startNamed('create',{mode:'online'});
$('join').onclick=()=>startNamed('join',{code:$('roomcode').value.trim().toUpperCase()});
$('startBtn').onclick=()=>send('start');$('leaveBtn').onclick=()=>{if(confirm('Sair da partida?'))send('leave')};
$('copyInvite').onclick=async()=>{const link=location.origin+'/?sala='+(state.room?.code||'');try{await navigator.clipboard.writeText(link);toast('Link da sala copiado!')}catch{prompt('Copie o convite:',link)}};
$('helpBtn').onclick=()=>{$('guide').hidden=false};$('closeGuide').onclick=()=>{$('guide').hidden=true};$('closeReplay').onclick=()=>{$('replay').hidden=true};
$('play').onclick=()=>{if(!state.selected.size)return;const c=state.hand.find(c=>state.selected.has(c.id));if(!c)return;if(['skip','draw2','reverse','draw4'].includes(c.rank)){state.claim=c.rank;$('claimPanel').hidden=false;$('colors').hidden=c.rank!=='draw4';return}if(c.rank==='wild'){state.claim=null;$('claimPanel').hidden=false;document.querySelector('.claimGrid').hidden=true;$('colors').hidden=false;return}send('play',{cards:[...state.selected]})};
$('challenge').onclick=()=>send('challenge');
$('accept').onclick=()=>send('accept');
$('draw').onclick=()=>send('draw');
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
$('tableTarget').querySelector('b').textContent=s.pending?('CARTA OCULTA — '+({skip:'BLOQUEIO',draw2:'+2',draw4:'+4',reverse:'INVERTER'})[s.pending.claim]):((s.top?.rank||'—')+' • '+(s.color||'—').toUpperCase());
$('tableCards').replaceChildren();
if(s.pending){const back=document.createElement('div');back.className='tableBack';$('tableCards').append(back)}
else if(s.top)$('tableCards').append(makeCard(s.top));
$('hand').replaceChildren();
for(const c of state.hand){const el=makeCard(c);el.classList.toggle('selected',state.selected.has(c.id));el.onclick=()=>{if(!myturn||s.pending)return;if(state.selected.has(c.id))state.selected.delete(c.id);else{state.selected.clear();state.selected.add(c.id)}renderHandOnly()};$('hand').append(el)}
$('challenge').disabled=!myturn||!s.pending;
$('accept').disabled=!myturn||!s.pending;
$('draw').disabled=!myturn||!!s.pending;
$('play').disabled=!myturn||!state.selected.size||!!s.pending;
$('play').textContent='JOGAR CARTA';
$('turnHint').textContent=winner?'Fim da partida. Crie outra sala para revanche.':!s.started?'Aguardando o anfitrião iniciar.':myturn?(s.pending?'Acredite na ação ou duvide da declaração.':'Selecione uma carta, ou compre uma e passe.'):'Aguardando '+(actor?.name||'jogador')+'...';
$('waitingTitle').textContent='Sala '+s.code;$('waitingList').textContent=s.players.map(x=>x.name+(x.id===s.host?' ★':'')).join('\\n')+'\\n'+s.players.length+'/4 jogadores';
$('startBtn').hidden=s.host!==state.id;$('startBtn').disabled=s.players.length<2;
renderPeers()}
function renderHandOnly(){for(const [i,el] of [...$('hand').children].entries())el.classList.toggle('selected',state.selected.has(state.hand[i].id));$('play').disabled=state.room?.turn!==state.id||!state.selected.size||!!state.room?.pending;$('play').textContent='JOGAR CARTA'}
function renderPeers(){const parent=$('peerCameras'),s=state.room;if(!s)return;
const others=s.players.filter(p=>p.id!==state.id);
const slots=[...others];slots.push(s.players.find(p=>p.id===state.id)||{id:state.id,name:'Você',bot:false,connected:true,cards:0});
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
function showReplay(r){const modal=$('replay');$('replayTitle').textContent=r.lie?'BLEFE DESCOBERTO!':'ERA VERDADE!';$('replayCards').replaceChildren();r.cards.forEach(c=>$('replayCards').append(makeCard(c)));$('replayText').textContent=r.accuser+' desconfiou de '+r.accused+'. '+r.loser+' recebeu uma penalidade'+(r.out?' e foi eliminado':'')+'.';modal.hidden=false;setTimeout(()=>{if(!modal.hidden)modal.hidden=true},5500)}
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