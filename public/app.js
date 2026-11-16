'use strict';
const $=id=>document.getElementById(id);
const COR={red:'VERMELHO',yellow:'AMARELO',green:'VERDE',blue:'AZUL',wild:'CORINGA'};
const ACAO={skip:'BLOQUEIO',draw2:'+2',reverse:'INVERTER',draw4:'+4',wild:'CORINGA',hidden:'CARTA OCULTA'};
const dinheiroTeste=centavos=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(centavos||0)/100);
const nomeCarta=c=>!c?'carta':(ACAO[c.rank]||c.rank)+(c.color&&c.color!=='wild'?' '+(COR[c.color]||''):'');
const state={id:null,room:null,hand:[],selected:new Set(),ws:null,token:localStorage.getItem('blefe_token'),name:localStorage.getItem('blefe_name')||'',stream:null,pcs:new Map(),remoteStreams:new Map(),micEnabled:true,camEnabled:false,voiceReady:false,volumes:new Map(),selectedColor:'red',claim:null,previewStream:null,lastAnimatedMove:null,mediaConnecting:false,revealTimers:[],victoryShown:null,victoryTimer:null,wallet:{balance_cents:5000,test:{balance_cents:5000},real:{balance_cents:0,enabled:false},history:[],ad_free:false},publicConfig:null,roomPreview:null};
$('nickname').value=state.name;
function toast(s){const el=$('toast');el.textContent=s;el.style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.style.display='none',3500)}
function send(type,data={}){if(state.ws?.readyState===1)state.ws.send(JSON.stringify({type,...data}));else toast('Servidor desconectado. Reconectando...')}
function connection(){const proto=location.protocol==='https:'?'wss':'ws';const ws=new WebSocket(proto+'://'+location.host+'/ws');state.ws=ws;$('connection').textContent='● Conectando';
ws.onopen=()=>{$('connection').textContent='● Conectado';send('hello',{name:state.name||'Jogador',token:state.token})};
ws.onmessage=async e=>{let m;try{m=JSON.parse(e.data)}catch{return}
if(m.type==='welcome'){state.id=m.id;state.token=m.id;localStorage.setItem('blefe_token',m.id);if(m.wallet){state.wallet=m.wallet;updateWalletUI()}if(m.room){$('lobby').hidden=true;$('game').hidden=false;if(state.room)render();if(state.voiceReady)send('media_ready',{ready:true})}}
else if(m.type==='state'){state.room=m.state;state.hand=m.hand||[];state.selected=new Set([...state.selected].filter(x=>state.hand.some(c=>c.id===x)));render();if(m.state.move&&m.state.move.id!==state.lastAnimatedMove){state.lastAnimatedMove=m.state.move.id;animateMove(m.state.move)}}
else if(m.type==='wallet'){state.wallet=m.wallet;updateWalletUI();if(state.room?.winner&&!$('victory').hidden)populateVictory(state.room)}
else if(m.type==='notice'){$('logline').textContent=m.message}
else if(m.type==='error')toast(m.message)
else if(m.type==='reveal')showReplay(m.result)
else if(m.type==='left'){state.room=null;state.hand=[];state.selected.clear();clearTimeout(state.victoryTimer);$('victory').hidden=true;state.victoryShown=null;$('game').hidden=true;$('lobby').hidden=false;closeMedia()}
else if(m.type==='media_peer'){if(m.id!==state.id){if(m.ready&&state.voiceReady&&state.id<m.id){const peer=state.room?.players.find(p=>p.id===m.id);if(peer?.media)await connectPeer(m.id)}else if(!m.ready)removePeer(m.id)}}
else if(m.type==='signal')await onSignal(m.sender,m.signal)};
ws.onclose=()=>{if(state.ws!==ws)return;$('connection').textContent='● Desconectado';for(const id of [...state.pcs.keys()])removePeer(id,false);renderPeers();setTimeout(connection,1600)};ws.onerror=()=>{}}
function startNamed(type,extra){const name=$('nickname').value.trim()||'Jogador';state.name=name;localStorage.setItem('blefe_name',name);if(!state.id){toast('Conectando ao servidor...');return}send(type,{...extra,name,wallet_type:'test'})}
$('training').onclick=()=>startNamed('create',{mode:'training',stake:0});
$('create').onclick=()=>{
  const raw=$('createStake').value;
  if(raw===''){toast('Escolha primeiro o valor de entrada da sala.');$('createStake').focus();return}
  const amount=Number(raw);
  const balance=state.wallet?.test?.balance_cents??state.wallet?.balance_cents??0;
  if(amount>balance){toast('Seu saldo de teste é menor que o valor escolhido.');return}
  startNamed('create',{mode:'online',stake:amount});
};
let previewSequence=0;
async function previewRoom(code){
  code=String(code||'').trim().toUpperCase();
  const panel=$('joinPreview');panel.hidden=true;panel.replaceChildren();
  if(!/^[A-Z0-9]{6}$/.test(code)){toast('O código da sala deve ter seis letras ou números.');return}
  const seq=++previewSequence;
  try{
    const response=await fetch('/api/sala/'+encodeURIComponent(code),{cache:'no-store'});
    if(!response.ok){if(seq===previewSequence)toast('Sala não encontrada. Confira o código.');return}
    const data=await response.json();
    if(seq!==previewSequence)return;
    state.roomPreview=data;
    const title=document.createElement('strong');
    title.textContent='Sala '+data.code+' — '+data.host_name;
    const details=document.createElement('p');
    details.textContent='Entrada por participante: '+dinheiroTeste(data.stake_cents)+' de saldo fictício. Nenhum dinheiro real será cobrado.';
    const consent=document.createElement('button');
    consent.className='primary';
    const balance=state.wallet?.test?.balance_cents??state.wallet?.balance_cents??0;
    consent.textContent=data.joinable?'Aceitar entrada e participar':'Partida já iniciada / sala indisponível';
    consent.disabled=!data.joinable||data.stake_cents>balance;
    if(data.stake_cents>balance)details.textContent+=' Saldo de teste insuficiente.';
    consent.onclick=()=>startNamed('join',{code:data.code,accept_stake_cents:data.stake_cents});
    panel.append(title,details,consent);panel.hidden=false;
  }catch(error){if(seq===previewSequence)toast('Não foi possível consultar a sala. Verifique sua conexão.')}
}
$('join').onclick=()=>previewRoom($('roomcode').value);
$('roomcode').addEventListener('input',()=>{$('joinPreview').hidden=true;state.roomPreview=null});
$('startBtn').onclick=()=>send('start');$('leaveBtn').onclick=()=>{if(confirm('Sair da partida?'))send('leave')};
$('victoryClose').onclick=()=>{$('victory').hidden=true};
$('victoryLeave').onclick=()=>{$('victory').hidden=true;send('leave')};
$('victorySpectate').onclick=()=>{send('spectate');$('victory').hidden=true;toast('Você continuará na sala como espectador.')};
$('victoryAccept').onclick=()=>send('rematch_accept');
$('victoryRematch').onclick=()=>send('rematch_propose',{amount:Number($('rematchAmount').value),wallet_type:'test'});
$('rematchAmount').oninput=()=>{$('rematchAmountLabel').textContent=dinheiroTeste($('rematchAmount').value)+' de teste'};
$('openWallet').onclick=()=>{updateWalletUI();$('walletModal').hidden=false};
$('gameWallet').onclick=()=>{updateWalletUI();$('walletModal').hidden=false};
$('closeWallet').onclick=()=>{$('walletModal').hidden=true};
$('openDonation').onclick=()=>{$('donationModal').hidden=false;loadPublicConfig()};
$('closeDonation').onclick=()=>{$('donationModal').hidden=true};
$('copyDonationPix').onclick=async()=>{
  const key=state.publicConfig?.donation_pix_key;
  if(!key){toast('O Pix ainda não está configurado.');return}
  try{await navigator.clipboard.writeText(key);toast('Chave Pix copiada.')}
  catch(err){window.prompt('Copie a chave Pix de apoio:',key)}
};
function updateWalletUI(){
  const w=state.wallet||{test:{balance_cents:5000},real:{balance_cents:0},history:[]};
  const saldoTeste=w.test?.balance_cents??w.balance_cents??5000;
  for(const id of ['lobbyBalance','walletBigBalance','gameWallet'])
    $(id).textContent=dinheiroTeste(saldoTeste);
  $('walletRealBalance').textContent=dinheiroTeste(w.real?.balance_cents||0);
  const el=$('walletTransactions');el.replaceChildren();
  (w.history||[]).slice().reverse().slice(0,8).forEach(entry=>{
    const row=document.createElement('div');row.className='walletTransaction';
    const name=document.createElement('span');name.textContent=entry.description||'Movimentação de teste';
    const value=document.createElement('strong');value.textContent=(entry.amount_cents>=0?'+':'')+dinheiroTeste(entry.amount_cents);
    value.className=entry.amount_cents>=0?'positive':'negative';
    row.append(name,value);el.append(row);
  });
}
async function loadPublicConfig(){
  if(!state.publicConfig){
    try{const resp=await fetch('/config',{cache:'no-store'});if(resp.ok)state.publicConfig=await resp.json()}
    catch(err){console.warn('Configuração Pix indisponível',err)}
  }
  const config=state.publicConfig||{};
  $('donationSetup').hidden=!!config.donation_enabled;
  $('donationKeyPanel').hidden=!config.donation_enabled;
  $('donationPixKey').textContent=config.donation_pix_key||'';
  $('donationPixOwner').textContent=config.donation_pix_owner?'Destinatário: '+config.donation_pix_owner:'';
}
updateWalletUI();

$('helpBtn').onclick=()=>{$('guide').hidden=false};$('closeGuide').onclick=()=>{$('guide').hidden=true};$('closeReplay').onclick=closeReplay;
$('play').onclick=()=>{if(!state.selected.size)return;const c=state.hand.find(c=>state.selected.has(c.id));if(!c)return;if(['skip','draw2','reverse','draw4'].includes(c.rank)){state.claim=c.rank;$('claimPanel').hidden=false;$('colors').hidden=c.rank!=='draw4';return}if(c.rank==='wild'){state.claim=null;$('claimPanel').hidden=false;document.querySelector('.claimGrid').hidden=true;$('colors').hidden=false;return}send('play',{cards:[...state.selected]})};
$('challenge').onclick=()=>send('challenge');
$('accept').onclick=()=>send('accept');
$('draw').onclick=()=>send('draw');
$('bluff').onclick=()=>{if(!state.selected.size)return;state.claim=null;document.querySelector('.claimGrid').hidden=false;$('colors').hidden=true;$('claimPanel').hidden=false};
function inviteMessage(room){
  const url=new URL(location.pathname,location.origin);
  url.searchParams.set('sala',room.code);
  const host=room.players?.find(x=>x.id===room.host)?.name||'Anfitrião';
  return [
    'Convite para jogar BLEFE COLOR!',
    'Sala: '+room.code,
    'Anfitrião: '+host,
    'Entrada: '+dinheiroTeste(room.stake)+' de teste por participante',
    'Saldo fictício, sem dinheiro real ou saques.',
    'Entre pelo link:',
    url.toString()
  ].join('\n');
}
function updateInvitation(room){
  if(!room||room.mode==='training')return;
  const message=inviteMessage(room);
  $('whatsappInvite').href='https://wa.me/?text='+encodeURIComponent(message);
  $('whatsappInvite').setAttribute('aria-label','Enviar convite da sala '+room.code+' pelo WhatsApp');
  $('waitingStake').textContent='Entrada da sala: '+dinheiroTeste(room.stake)+' em saldo de teste por jogador';
}
$('whatsappInvite').addEventListener('click',event=>{
  if(!state.room){event.preventDefault();toast('Crie uma sala antes de convidar amigos.');return}
  updateInvitation(state.room);
});
$('copyInvite').onclick=async()=>{
  if(!state.room)return;
  const message=inviteMessage(state.room);
  try{await navigator.clipboard.writeText(message);toast('Convite com código e valor copiado!')}
  catch(error){window.prompt('Copie e envie o convite:',message)}
};
$('cancelClaim').onclick=()=>{$('claimPanel').hidden=true};
for(const el of document.querySelectorAll('[data-color]')){el.onclick=()=>{state.selectedColor=el.dataset.color;for(const b of document.querySelectorAll('[data-color]'))b.style.outline=b===el?'3px solid white':'';if(state.claim||document.querySelector('.claimGrid').hidden){send('play',{cards:[...state.selected],claim:state.claim,color:state.selectedColor});$('claimPanel').hidden=true;state.claim=null;document.querySelector('.claimGrid').hidden=false}}}
for(const el of document.querySelectorAll('[data-claim]')){el.onclick=()=>{state.claim=el.dataset.claim;if(state.claim==='draw4'){$('colors').hidden=false;toast('Selecione a cor do +4.')}else{send('play',{cards:[...state.selected],claim:state.claim,color:state.selectedColor});$('claimPanel').hidden=true;state.claim=null}}};
function makeCard(c){const el=document.createElement('div');el.className='card uno '+(c.color||'wild');const b=document.createElement('b');b.textContent=({skip:'⊘',draw2:'+2',draw4:'+4',reverse:'⇄',wild:'★'})[c.rank]||c.rank;el.append(b);return el}
function render(){const s=state.room;if(!s)return;
$('lobby').hidden=true;$('game').hidden=false;$('roomLabel').textContent=s.mode==='training'?'TREINAMENTO':'SALA '+s.code;$('waiting').hidden=s.started;
const me=s.players.find(p=>p.id===state.id),actor=s.players.find(p=>p.id===s.turn),myturn=!!s.started&&!s.winner&&s.turn===state.id,winner=s.players.find(p=>p.id===s.winner);
$('turnBanner').textContent=winner?'🏆 '+winner.name+' VENCEU!':!s.started?'AGUARDANDO JOGADORES':me?.spectator?'👁 ASSISTINDO À PARTIDA':myturn?'🟡 SUA VEZ DE JOGAR':'⏳ VEZ DE '+(actor?.name?.toUpperCase()||'...');
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
$('turnHint').textContent=winner?'Fim da partida. Confira o resultado e negocie a revanche.':!s.started?'Aguardando o anfitrião iniciar.':me?.spectator?'Você está assistindo à partida, sem participar das jogadas.':myturn?(s.pending?'Acredite na ação ou duvide da declaração.':'Selecione uma carta, ou compre uma e passe.'):'Aguardando '+(actor?.name||'jogador')+'...';
$('waitingTitle').textContent='Sala '+s.code;$('waitingList').textContent=s.players.map(x=>x.name+(x.id===s.host?' ★':'')).join('\\n')+'\\n'+s.players.length+'/4 jogadores';
$('startBtn').hidden=s.host!==state.id;$('startBtn').disabled=s.players.length<2;
renderPeers();updateVictory(s)}
function renderHandOnly(){for(const [i,el] of [...$('hand').children].entries())el.classList.toggle('selected',state.selected.has(state.hand[i].id));$('play').disabled=state.room?.turn!==state.id||!state.selected.size||!!state.room?.pending;$('bluff').disabled=$('play').disabled;$('play').textContent='JOGAR CARTA'}
function renderPeers(){
  const parent=$('peerCameras'),s=state.room;
  if(!s)return;
  const slots=s.players.filter(p=>p.id!==state.id).slice(0,3);
  while(slots.length<3)slots.push(null);
  slots.push(s.players.find(p=>p.id===state.id)||{id:state.id,name:'Você',connected:true,bot:false});
  slots.forEach((p,index)=>{
    const key=p?.id||'vazio-'+index;
    let box=parent.children[index];
    if(!box||box.dataset.peer!==key){
      const old=box;
      box=document.createElement('div');
      box.className='peer';box.dataset.peer=key;
      const avatar=document.createElement('div');avatar.className='avatar';box.append(avatar);
      const label=document.createElement('div');label.className='tag';box.append(label);
      if(old){
        const oldVideo=old.querySelector('video');
        if(oldVideo){oldVideo.pause();oldVideo.srcObject=null}
        parent.replaceChild(box,old);
      }else parent.append(box);
    }
    box.classList.toggle('current',!!p&&s.turn===p.id);
    let countBadge=box.querySelector('.cardsCountBadge');
    if(!countBadge){
      countBadge=document.createElement('div');countBadge.className='cardsCountBadge';
      countBadge.innerHTML='<span class="cardsIcon">▣</span><strong></strong>';
      box.append(countBadge);
    }
    const count=Number(p?.cards??0);
    countBadge.hidden=!p;
    countBadge.querySelector('strong').textContent=p?(p.spectator?'ASSISTE':count+' '+(count===1?'CARTA':'CARTAS')):'';
    countBadge.classList.toggle('isLow',!!p&&!p.spectator&&s.started&&count>0&&count<=2);
    const label=box.querySelector('.tag'),avatar=box.querySelector('.avatar');
    label.textContent=p?(p.id===state.id?'VOCÊ':p.name)+(p.connected?'':' • FORA')+(s.turn===p.id?' • VEZ':''):'AGUARDANDO';
    const stream=p?.id===state.id?state.previewStream:state.remoteStreams.get(p?.id);
    const visibleTrack=stream?.getVideoTracks()?.find(track=>track.readyState==='live');
    let video=box.querySelector('video');
    if(visibleTrack){
      if(!video){
        video=document.createElement('video');
        video.autoplay=true;video.playsInline=true;video.muted=true;video.setAttribute('playsinline','');
        video.setAttribute('webkit-playsinline','');
        if(p.id===state.id)video.classList.add('selfVideo');
        box.prepend(video);
      }
      if(video.srcObject!==stream){
        video.srcObject=stream;
        video.play().catch(()=>{});
      }
      avatar.hidden=true;
    }else{
      if(video){video.pause();video.srcObject=null;video.remove()}
      avatar.hidden=false;avatar.textContent=!p?'…':p.bot?'🤖':p.id===state.id?'EU':p.name.slice(0,1).toUpperCase();
    }
    if(p&&!p.bot&&p.id!==state.id){
      let vol=box.querySelector('.peerVolume');
      if(!vol){
        vol=document.createElement('input');vol.type='range';vol.min='0';vol.max='100';
        vol.value=String(state.volumes.get(p.id)??100);vol.className='peerVolume';
        vol.setAttribute('aria-label','Volume de '+p.name);
        vol.oninput=()=>{
          state.volumes.set(p.id,Number(vol.value));
          const audio=document.getElementById('audio-'+p.id);
          if(audio)audio.volume=Number(vol.value)/100;
        };
        box.append(vol);
      }
      if(stream)attachAudio(p.id,stream);
    }
  });
  while(parent.children.length>4){
    const old=parent.lastElementChild,video=old?.querySelector('video');
    if(video){video.pause();video.srcObject=null}
    old?.remove();
  }
}
function updateVictory(room){
  const modal=$('victory');
  if(!room?.winner){
    clearTimeout(state.victoryTimer);
    state.victoryShown=null;
    modal.hidden=true;
    return;
  }
  const key=room.code+':'+(room.round||1);
  if(state.victoryShown!==key){
    state.victoryShown=key;
    clearTimeout(state.victoryTimer);
    state.victoryTimer=setTimeout(()=>{
      if(state.room?.winner&&state.room.code===room.code&&state.room.round===room.round){
        populateVictory(state.room);
        modal.hidden=false;
      }
    },$('replay').hidden?450:5300);
  }
  if(!modal.hidden)populateVictory(room);
}
function populateVictory(room){
  const me=room.players.find(p=>p.id===state.id);
  const winner=room.players.find(p=>p.id===room.winner);
  if(!winner)return;
  const won=room.winner===state.id;
  const modal=$('victory');
  modal.classList.toggle('lost',!won);
  $('victoryEmblem').textContent=won?'🏆':'🥈';
  $('victoryEyebrow').textContent=won?'PARABÉNS!':'PARTIDA ENCERRADA';
  $('victoryTitle').textContent=won?'VOCÊ VENCEU!':winner.name+' VENCEU!';
  $('victoryMessage').textContent=(won?'Você descartou suas cartas e ganhou esta partida!':'O vencedor foi '+winner.name+'. Prepare uma revanche ou assista aos próximos jogadores.')+(room.stake>0?' Entrada: '+dinheiroTeste(room.stake)+' de teste por participante.':' Rodada gratuita.');
  const list=$('victoryPlayers');
  list.replaceChildren();
  const people=[...room.players].filter(p=>!p.spectator);
  people.sort((a,b)=>(a.id===room.winner?-1:b.id===room.winner?1:a.cards-b.cards));
  people.forEach((p,i)=>{
    const line=document.createElement('div');line.className='victoryPlayer'+(p.id===room.winner?' winner':'');
    const place=document.createElement('span');place.className='place';place.textContent=p.id===room.winner?'🏆':String(i+1)+'º';
    const name=document.createElement('span');name.className='playerName';name.textContent=p.name+(p.id===state.id?' (você)':'');
    const count=document.createElement('span');count.className='playerCards';count.textContent=p.cards+' '+(p.cards===1?'carta':'cartas');
    line.append(place,name,count);list.append(line);
  });
  const firstTime=modal.hidden&&!modal.dataset.celebrated;
  if(firstTime&&won&&window.matchMedia('(prefers-reduced-motion: no-preference)').matches){
    const pieces=$('victoryConfetti');pieces.replaceChildren();
    const palette=['#f4c75b','#66e2b4','#c480f4','#ff7680','#8dc9ff','#fff1c7'];
    for(let i=0;i<32;i++){
      const dot=document.createElement('span');
      dot.style.left=(3+(i*71%94))+'%';
      dot.style.setProperty('--confetti',palette[i%palette.length]);
      dot.style.setProperty('--delay',(i%9)*.09+'s');
      dot.style.setProperty('--duration',(2.8+(i%5)*.36)+'s');
      dot.style.setProperty('--sway',((i%2?-1:1)*(12+(i*7%50)))+'px');
      pieces.append(dot);
    }
  }
  if(room.round!==Number(modal.dataset.round||0)){
    modal.dataset.celebrated='';
    modal.dataset.round=String(room.round||1);
  }
  const observer=!!me?.spectator;
  const hosting=room.host===state.id&&!observer;
  const offer=room.proposal;
  const max=Math.max(0,Math.min(5000,Math.floor((state.wallet?.test?.balance_cents??state.wallet?.balance_cents??0)/500)*500));
  $('rematchAmount').max=String(max);
  if(Number($('rematchAmount').value)>max)$('rematchAmount').value=String(max);
  $('rematchAmountLabel').textContent=dinheiroTeste($('rematchAmount').value)+' de teste';
  $('rematchHostControls').hidden=!hosting;
  $('rematchProposal').hidden=!offer;
  $('victoryWaiting').hidden=!!offer||hosting||observer;
  $('victoryWaiting').textContent=observer?'Você está assistindo. Aguarde a próxima rodada.':'Aguardando o anfitrião propor a revanche.';
  $('victorySpectate').hidden=observer;
  $('victoryAccept').hidden=observer||!offer||offer.accepted.includes(state.id);
  $('victoryAccept').disabled=!!offer&&Number(state.wallet?.test?.balance_cents??state.wallet?.balance_cents??0)<offer.amount;
  if(offer){
    $('rematchProposedValue').textContent='Proposta: '+dinheiroTeste(offer.amount)+' de teste por participante — sem dinheiro real';
    const acceptance=$('rematchAcceptance');acceptance.replaceChildren();
    room.players.filter(p=>!p.spectator).forEach(p=>{
      const label=document.createElement('div');label.className='rematchVote';
      const ok=offer.accepted.includes(p.id);
      label.textContent=(ok?'✓ ':'… ')+p.name+(ok?' — aceitou':' — aguardando');
      label.classList.toggle('accepted',ok);
      acceptance.append(label);
    });
  }
  $('victoryRematch').textContent=offer?'Alterar proposta de revanche':'Propor revanche';
}

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
function erroPermissao(err,type){
  if(err?.name==='NotAllowedError'||err?.name==='PermissionDeniedError')
    return 'Autorize '+type+' nas permissões do Safari.';
  if(err?.name==='NotFoundError')return 'Não foi encontrado um dispositivo de '+type+'.';
  if(err?.name==='NotReadableError')return 'O dispositivo está sendo usado por outro aplicativo. Feche outros aplicativos e tente novamente.';
  return 'Não foi possível ativar '+type+'. Tente novamente.';
}
async function startVoice(){
  if(state.voiceReady||state.mediaConnecting)return;
  if(!navigator.mediaDevices?.getUserMedia){toast('O microfone exige uma conexão HTTPS.');return}
  state.mediaConnecting=true;
  try{
    state.stream=await navigator.mediaDevices.getUserMedia({
      audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false
    });
    state.voiceReady=true;state.micEnabled=true;
    $('voiceBtn').textContent='🎙 Voz ligada';$('micBtn').disabled=false;
    $('micBtn').textContent='🔊 Microfone ligado';
    send('media_ready',{ready:true});
    for(const p of state.room?.players||[]){
      if(!p.bot&&p.id!==state.id&&p.media&&state.id<p.id)await connectPeer(p.id);
    }
    renderPeers();
    toast('Microfone ativado. Você já pode conversar.');
  }catch(err){toast(erroPermissao(err,'microfone'))}
  finally{state.mediaConnecting=false}
}
$('voiceBtn').onclick=()=>{
  if(!state.voiceReady)startVoice();
  else{closeMedia();toast('Voz desativada.')}
};
$('micBtn').onclick=()=>{
  state.micEnabled=!state.micEnabled;
  for(const track of state.stream?.getAudioTracks()||[])track.enabled=state.micEnabled;
  $('micBtn').textContent=state.micEnabled?'🔊 Microfone ligado':'🔇 Microfone mudo';
};
async function toggleCamera(){
  if(!state.voiceReady){toast('Ative a voz antes de ligar a câmera.');return}
  if(state.camEnabled){
    state.camEnabled=false;
    for(const pc of state.pcs.values()){
      if(pc._videoSender){try{await pc._videoSender.replaceTrack(null)}catch(_){}}
    }
    for(const track of state.stream?.getVideoTracks()||[]){state.stream.removeTrack(track);track.stop()}
    state.previewStream=null;
    $('camBtn').textContent='📷 Ligar câmera';
    renderPeers();
    return;
  }
  try{
    const camera=await navigator.mediaDevices.getUserMedia({
      audio:false,video:{
        facingMode:'user',
        width:{ideal:320},height:{ideal:240},
        frameRate:{ideal:12,max:15}
      }
    });
    const track=camera.getVideoTracks()[0];
    if(!track)throw new Error('Sem vídeo');
    state.stream.addTrack(track);
    state.previewStream=new MediaStream([track]);
    state.camEnabled=true;
    track.onunmute=()=>renderPeers();
    track.onended=()=>{
      if(!state.camEnabled||state.previewStream?.getVideoTracks()?.[0]!==track)return;
      state.camEnabled=false;state.previewStream=null;
      state.stream?.removeTrack(track);
      $('camBtn').textContent='↻ Retomar câmera';renderPeers();
      toast('A câmera foi interrompida. Toque em Retomar câmera.');
    };
    $('camBtn').textContent='📷 Câmera ligada';
    renderPeers();
    for(const pc of state.pcs.values()){
      try{
        if(pc._videoSender)await pc._videoSender.replaceTrack(track);
        else pc._videoSender=pc.addTrack(track,state.stream);
      }catch(e){console.warn('Envio de câmera:',e)}
    }
  }catch(err){toast(erroPermissao(err,'câmera'))}
}
$('camBtn').onclick=toggleCamera;
async function connectPeer(id){
  if(!state.voiceReady||!state.stream||id===state.id||state.pcs.has(id))return;
  const pc=new RTCPeerConnection(rtcConfig);
  pc._makingOffer=false;pc._ignoreOffer=false;pc._needsOffer=false;pc._queuedIce=[];
  state.pcs.set(id,pc);
  pc.onicecandidate=e=>{
    if(e.candidate)send('signal',{to:id,signal:{candidate:e.candidate.toJSON()}});
  };
  pc.ontrack=e=>{
    let stream=state.remoteStreams.get(id);
    if(!stream){stream=e.streams?.[0]||new MediaStream();state.remoteStreams.set(id,stream)}
    if(!stream.getTracks().some(t=>t.id===e.track.id))stream.addTrack(e.track);
    e.track.onunmute=()=>renderPeers();
    e.track.onended=()=>{
      if(stream.getTracks().includes(e.track))stream.removeTrack(e.track);
      renderPeers();
    };
    if(e.track.kind==='audio')attachAudio(id,stream);
    renderPeers();
  };
  pc.onnegotiationneeded=()=>offer(pc,id);
  pc.oniceconnectionstatechange=()=>{
    if(pc.iceConnectionState==='failed'){
      try{pc.restartIce();offer(pc,id)}catch(_){toast('A conexão de mídia falhou. Tente desligar e ligar a voz.')}
    }
  };
  for(const track of state.stream.getTracks()){
    const sender=pc.addTrack(track,state.stream);
    if(track.kind==='video')pc._videoSender=sender;
  }
}
async function offer(pc,id){
  if(pc.signalingState==='closed')return;
  if(pc._makingOffer||pc.signalingState!=='stable'){pc._needsOffer=true;return}
  pc._makingOffer=true;pc._needsOffer=false;
  try{
    await pc.setLocalDescription(await pc.createOffer());
    send('signal',{to:id,signal:{description:pc.localDescription.toJSON()}});
  }catch(err){console.warn('Negociação de mídia:',err)}
  finally{pc._makingOffer=false}
}
async function onSignal(id,signal){
  if(!state.voiceReady||!signal)return;
  let pc=state.pcs.get(id);
  if(!pc){await connectPeer(id);pc=state.pcs.get(id)}
  if(!pc)return;
  try{
    if(signal.description){
      const desc=signal.description;
      const collision=desc.type==='offer'&&(pc._makingOffer||pc.signalingState!=='stable');
      const polite=state.id>id;
      pc._ignoreOffer=!polite&&collision;
      if(pc._ignoreOffer)return;
      if(collision&&polite)await pc.setLocalDescription({type:'rollback'});
      await pc.setRemoteDescription(desc);
      const queued=pc._queuedIce.splice(0);
      for(const ice of queued){try{await pc.addIceCandidate(ice)}catch(_){}}
      if(desc.type==='offer'){
        await pc.setLocalDescription(await pc.createAnswer());
        send('signal',{to:id,signal:{description:pc.localDescription.toJSON()}});
      }else if(pc._needsOffer&&pc.signalingState==='stable'){
        pc._needsOffer=false;offer(pc,id);
      }
    }else if(signal.candidate){
      if(pc._ignoreOffer)return;
      if(pc.remoteDescription)await pc.addIceCandidate(signal.candidate);
      else pc._queuedIce.push(signal.candidate);
    }
  }catch(err){console.warn('Sinalização de mídia:',err)}
}
function attachAudio(id,stream){
  if(!stream.getAudioTracks().length)return;
  let audio=document.getElementById('audio-'+id);
  if(!audio){
    audio=document.createElement('audio');
    audio.id='audio-'+id;audio.autoplay=true;audio.playsInline=true;
    document.body.append(audio);
  }
  if(audio.srcObject!==stream){
    audio.srcObject=stream;
    audio.play().catch(()=>{});
  }
  audio.volume=(state.volumes.get(id)??100)/100;
}
function removePeer(id,refresh=true){
  const pc=state.pcs.get(id);
  if(pc){
    pc.onnegotiationneeded=null;pc.ontrack=null;
    pc.onicecandidate=null;pc.oniceconnectionstatechange=null;
    pc.close();
  }
  state.pcs.delete(id);state.remoteStreams.delete(id);
  const audio=document.getElementById('audio-'+id);
  if(audio){audio.pause();audio.srcObject=null;audio.remove()}
  if(refresh&&state.room)renderPeers();
}
function closeMedia(){
  send('media_ready',{ready:false});
  for(const id of [...state.pcs.keys()])removePeer(id,false);
  for(const track of state.stream?.getTracks()||[])track.stop();
  state.stream=null;state.previewStream=null;
  state.voiceReady=false;state.camEnabled=false;state.micEnabled=true;
  $('voiceBtn').textContent='🎙 Ativar voz';
  $('camBtn').textContent='📷 Ligar câmera';
  $('micBtn').disabled=true;
  if(state.room)renderPeers();
}
document.addEventListener('visibilitychange',()=>{
  if(document.visibilityState!=='visible')return;
  for(const video of document.querySelectorAll('#peerCameras video')){
    if(video.srcObject&&video.paused)video.play().catch(()=>{});
  }
});
const invitation=new URLSearchParams(location.search).get('sala');if(invitation){$('roomcode').value=invitation.toUpperCase();previewRoom(invitation)}connection();