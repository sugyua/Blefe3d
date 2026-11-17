/* Loja cosmética Fase 1: somente catálogo, prévia e equipar itens grátis.
 * Preços futuros são informativos. Nunca há checkout, Pix ou saldo real aqui.
 */
(function(){
'use strict';
const byId=id=>document.getElementById(id);
const modal=byId('shopModal');
const grid=byId('shopGrid');
const scene=byId('shopPreviewScene');
const feedback=byId('shopMessage');
const equipButton=byId('shopEquipButton');
const shop={
  catalog:null,inventory:null,slot:'back',selectedId:null,loading:false,
  lastFocus:null,initializing:null,requestSerial:0
};
const validSlot=new Set(['back','table','frame']);

function errorMessage(error){
  return error instanceof Error?error.message:'Não foi possível carregar a loja.';
}
function message(value,isError){
  feedback.textContent=value||'';
  feedback.classList.toggle('isError',!!isError);
}
function formatPrice(cents){
  return (Number(cents)/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
}
function currentItems(){
  return (shop.catalog?.items||[]).filter(item=>item.slot===shop.slot);
}
function safeItem(id){
  return (shop.catalog?.items||[]).find(item=>item.id===id)||null;
}
function owned(item){
  return !!item&&(item.free||!!shop.inventory?.owned?.includes(item.id));
}
function equipped(item){
  return !!item&&shop.inventory?.equipped?.[item.slot]===item.id;
}
function elem(tag,className,textValue){
  const node=document.createElement(tag);
  if(className)node.className=className;
  if(textValue!==undefined&&textValue!==null)node.textContent=String(textValue);
  return node;
}
async function request(url,opts){
  const response=await fetch(url,{credentials:'same-origin',cache:'no-store',...opts});
  let data;
  try{data=await response.json()}catch(_){data={error:'Resposta inesperada do servidor.'}}
  if(!response.ok)throw new Error(data.error||'Falha na comunicação com o servidor.');
  return data;
}
function renderVisual(item){
  const visual=elem('div','shopTileVisual');
  visual.dataset.skin=item.id;
  if(item.slot==='back'){
    const card=elem('div','shopTileCardBack','♠');
    card.setAttribute('aria-hidden','true');
    visual.append(card);
  }else if(item.slot==='table'){
    const table=elem('div','shopTileTable','BLEFE');
    table.setAttribute('aria-hidden','true');
    visual.append(table);
  }else{
    const frame=elem('div','shopTileFrame','J');
    frame.setAttribute('aria-hidden','true');
    visual.append(frame);
  }
  return visual;
}
function renderGrid(){
  const items=currentItems();
  const cards=document.createDocumentFragment();
  for(const item of items){
    const selected=item.id===shop.selectedId;
    const isOwned=owned(item);
    const isEquipped=equipped(item);
    const tile=elem('button','shopItem');
    tile.type='button';
    tile.dataset.productId=item.id;
    tile.classList.toggle('isSelected',selected);
    tile.classList.toggle('isEquipped',isEquipped);
    tile.setAttribute('aria-pressed',String(selected));
    tile.setAttribute('aria-label',item.name+', '+(isEquipped?'equipado':isOwned?'disponível gratuitamente':'em breve'));
    tile.append(renderVisual(item));
    const info=elem('div','shopItemInfo');
    const top=elem('div','shopItemTop');
    top.append(elem('span','shopItemName',item.name));
    const status=elem('span','shopItemStatus'+(isOwned?'':' isLocked'),
      isEquipped?'EQUIPADO':isOwned?'GRÁTIS':'EM BREVE');
    top.append(status);
    info.append(top);
    info.append(elem('span','shopItemFooter',
      isEquipped?'✓ Em uso':isOwned?'Grátis para equipar':'Prévia premium'));
    tile.append(info);
    tile.addEventListener('click',()=>{
      shop.selectedId=item.id;
      renderGrid();
      renderPreview();
    });
    cards.append(tile);
  }
  grid.replaceChildren(cards);
  const category=(shop.catalog?.categories||[]).find(item=>item.id===shop.slot);
  byId('shopCategoryTitle').textContent=category?.name||'Coleção';
  byId('shopItemCount').textContent=items.length+' opções';
  for(const tab of byId('shopTabs').querySelectorAll('[data-shop-slot]')){
    const active=tab.dataset.shopSlot===shop.slot;
    tab.setAttribute('aria-pressed',String(active));
  }
}
function renderPreview(){
  const item=safeItem(shop.selectedId);
  if(!item){
    equipButton.disabled=true;
    byId('shopPreviewName').textContent='Selecione um item';
    return;
  }
  const isOwned=owned(item);
  const isEquipped=equipped(item);
  scene.dataset.slot=item.slot;
  scene.dataset.skin=item.id;
  byId('shopPreviewName').textContent=item.name;
  byId('shopPreviewDescription').textContent=item.description;
  const pill=byId('shopPreviewStatus');
  pill.classList.toggle('isLocked',!isOwned);
  pill.textContent=isEquipped?'EQUIPADO':isOwned?'GRÁTIS':'EM BREVE';
  byId('shopPreviewPrice').textContent=isOwned
    ?'Item gratuito • sem gastar saldo de teste'
    :'Item planejado • preço ilustrativo: '+formatPrice(item.price_hint_cents);
  equipButton.disabled=shop.loading||!isOwned||isEquipped;
  equipButton.textContent=shop.loading?'Salvando...':
    isEquipped?'✓ Item equipado':isOwned?'Equipar gratuitamente':'Compra indisponível';
}
function applyLook(){
  if(!shop.catalog||!shop.inventory)return;
  const result={};
  for(const slot of validSlot){
    const id=shop.inventory.equipped?.[slot]||shop.catalog.defaults?.[slot];
    const product=safeItem(id);
    result[slot]=product&&product.slot===slot&&owned(product)
      ?id:shop.catalog.defaults[slot];
  }
  document.body.dataset.shopBack=result.back;
  document.body.dataset.shopTable=result.table;
  document.dispatchEvent(new CustomEvent('blefe:cosmetics',{detail:result}));
}
async function loadCatalog(){
  if(shop.catalog)return shop.catalog;
  shop.catalog=await request('/api/shop/catalog');
  if(!Array.isArray(shop.catalog.items)||!Array.isArray(shop.catalog.categories))
    throw new Error('Catálogo indisponível.');
  return shop.catalog;
}
async function loadInventory(){
  const serial=++shop.requestSerial;
  const inventory=await request('/api/shop/me');
  if(serial!==shop.requestSerial)return;
  shop.inventory=inventory;
  byId('shopOwnedCount').textContent=String(inventory.owned?.length||0);
  applyLook();
  return inventory;
}
async function refresh(){
  if(shop.initializing)return shop.initializing;
  shop.initializing=(async()=>{
    await loadCatalog();
    await loadInventory();
    if(!shop.selectedId||!safeItem(shop.selectedId)||safeItem(shop.selectedId).slot!==shop.slot){
      shop.selectedId=shop.inventory?.equipped?.[shop.slot]||currentItems()[0]?.id;
    }
    if(!modal.hidden){renderGrid();renderPreview();}
  })();
  try{return await shop.initializing}
  finally{shop.initializing=null}
}
async function open(){
  if(!modal.hidden)return;
  shop.lastFocus=document.activeElement;
  modal.hidden=false;
  byId('shopDialog').focus();
  message('Carregando sua coleção...');
  try{
    await refresh();
    if(!shop.selectedId)shop.selectedId=shop.inventory?.equipped?.[shop.slot]||currentItems()[0]?.id;
    renderGrid();
    renderPreview();
    message('');
  }catch(err){
    grid.replaceChildren();
    message(errorMessage(err),true);
    equipButton.disabled=true;
    equipButton.textContent='Sem conexão';
  }
}
function close(){
  modal.hidden=true;
  message('');
  if(shop.lastFocus&&shop.lastFocus.isConnected)shop.lastFocus.focus();
}
function category(slot){
  if(!validSlot.has(slot))return;
  shop.slot=slot;
  shop.selectedId=shop.inventory?.equipped?.[slot]||
    (shop.catalog?.items||[]).find(item=>item.slot===slot)?.id||null;
  renderGrid();
  renderPreview();
  message('');
}
async function equipSelected(){
  if(shop.loading)return;
  const item=safeItem(shop.selectedId);
  if(!item||!owned(item)||equipped(item)){
    message('Este item não está disponível para equipar.',true);
    return;
  }
  shop.loading=true;
  renderPreview();
  message('Salvando sua escolha...');
  try{
    const data=await request('/api/shop/equip',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({slot:item.slot,product_id:item.id})
    });
    shop.inventory=data;
    applyLook();
    renderGrid();
    message(item.name+' equipado! A personalização já aparece nas partidas.');
  }catch(err){
    message(errorMessage(err),true);
  }finally{
    shop.loading=false;
    renderPreview();
  }
}

byId('openShop').addEventListener('click',open);
byId('shopClose').addEventListener('click',close);
byId('shopFooterClose').addEventListener('click',close);
equipButton.addEventListener('click',equipSelected);
byId('shopTabs').addEventListener('click',event=>{
  const tab=event.target.closest('[data-shop-slot]');
  if(tab&&validSlot.has(tab.dataset.shopSlot))category(tab.dataset.shopSlot);
});
modal.addEventListener('click',event=>{if(event.target===modal)close()});
document.addEventListener('keydown',event=>{
  if(event.key==='Escape'&&!modal.hidden){event.preventDefault();close()}
});
document.addEventListener('blefe:authenticated',()=>{
  // Trocas de conta nunca reutilizam o inventário anterior.
  shop.inventory=null;
  shop.selectedId=null;
  refresh().catch(()=>{ /* Se falhar, a loja exibirá o erro ao ser aberta. */ });
});
window.BlefeShop={open,refresh};
})();
