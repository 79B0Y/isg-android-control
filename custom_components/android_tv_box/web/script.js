// Minimal stable web UI for Android TV Box
(function(){
  const $ = (id)=>document.getElementById(id);
  const toast = (msg, ok=true)=>{ const t=$('toast'); if(!t) return; t.textContent=msg; t.className='toast '+(ok?'':'error'); requestAnimationFrame(()=>{t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),1500);}); };

  async function api(path, opts){ const res = await fetch(path, opts||{}); if(!res.ok){ throw new Error(await res.text()); } return await res.json(); }

  async function refreshStatus(){
    try{ const j = await api('/api/status'); const s = j.data||{};
      $('v-power').textContent = s.device_powered_on? 'On':'Off';
      $('v-wifi').textContent = s.wifi_enabled? 'Enabled':'Disabled';
      $('v-app').textContent = s.current_app_name || s.current_app || '-';
      $('pill-adb').textContent = 'ADB: ' + (s.adb_connected? 'Connected':'Disconnected');
    }catch(e){ if($('pill-adb')) $('pill-adb').textContent = 'ADB: Error'; }
  }

  async function loadConfig(){
    try{ const j = await api('/api/config'); const c=j.data||{};
      if($('i-host')) $('i-host').value=c.host||'127.0.0.1';
      if($('i-port')) $('i-port').value=c.port||5555;
      if($('i-name')) $('i-name').value=c.name||'Android TV Box';
      if($('i-isg-enable')) $('i-isg-enable').checked = (c.isg_monitoring !== false);
      if($('i-isg-interval')) $('i-isg-interval').value = c.isg_check_interval || 30;
    }catch(e){}
  }
  async function saveConfig(){
    try{ const body={
        host:($('i-host')?.value)||'127.0.0.1',
        port:parseInt(($('i-port')?.value)||'5555',10),
        name:($('i-name')?.value)||'Android TV Box',
        isg_monitoring: !!($('i-isg-enable')?.checked),
        isg_check_interval: parseInt(($('i-isg-interval')?.value)||'30',10)
      };
      const j=await api('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      toast(j.success?'Configuration saved':'Save failed', j.success);
    }catch(e){toast('Save failed: '+e.message,false);} }
  async function connectADB(){ try{ const body={ host:($('i-host')?.value)||'127.0.0.1', port:parseInt(($('i-port')?.value)||'5555',10)}; const j=await api('/api/connect-adb',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); toast(j.success?'ADB connected':'Connect failed: '+j.error, j.success); setTimeout(refreshStatus,800);}catch(e){toast('Connection error: '+e.message,false);} }

  function renderApps(apps){ const tb=$('tb-apps'); const sel=$('sel-launch'); if(!tb||!sel) return; tb.innerHTML=''; sel.innerHTML=''; (apps||[]).forEach(a=>{ const tr=document.createElement('tr'); tr.innerHTML=`<td>${a.name}</td><td>${a.package}</td><td>${a.visible?'Yes':'No'}</td><td><button class="secondary" data-act="vis" data-id="${a.id}" data-next="${!a.visible}">${a.visible?'Hide':'Show'}</button> <button class="danger" data-act="del" data-id="${a.id}">Delete</button></td>`; tb.appendChild(tr); if(a.visible){ const o=document.createElement('option'); o.value=a.package; o.textContent=`${a.name} (${a.package})`; sel.appendChild(o);} }); tb.onclick=async(e)=>{ const b=e.target.closest('button'); if(!b)return; if(b.dataset.act==='del'){ if(!confirm('Delete this app?'))return; const j=await api('/api/apps/'+encodeURIComponent(b.dataset.id),{method:'DELETE'}); toast(j.success?'Deleted':'Delete failed: '+j.error,j.success); loadApps(); } else if(b.dataset.act==='vis'){ const j=await api('/api/apps/'+encodeURIComponent(b.dataset.id),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({visible:(b.dataset.next==='true')})}); toast(j.success?'Updated':'Update failed: '+j.error,j.success); loadApps(); } } }
  async function loadApps(){ try{ const j=await api('/api/apps'); renderApps(j.data||[]);}catch(e){ toast('加载应用失败',false);} }
  async function addApp(){ const name=$('i-app-name')?.value.trim(); const pkg=$('i-app-pkg')?.value.trim(); const vis=$('i-app-vis')?.checked; if(!name||!pkg){ toast('Name and package required',false); return; } const j=await api('/api/apps',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,package:pkg,visible:!!vis})}); toast(j.success?'Added':'Add failed: '+j.error,j.success); if(j.success){ if($('i-app-name')) $('i-app-name').value=''; if($('i-app-pkg')) $('i-app-pkg').value=''; if($('i-app-vis')) $('i-app-vis').checked=true; loadApps(); } }
  async function launchSelected(){ const sel=$('sel-launch'); const pkg=sel?.value; if(!pkg){ toast('Select an app',false); return; } const j=await api('/api/launch-app',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({package_name:pkg})}); toast(j.success?'Launch command sent':'Launch failed: '+j.error,j.success); setTimeout(refreshStatus,800); }

  function bind(){ $('btn-refresh')?.addEventListener('click',refreshStatus); $('btn-save')?.addEventListener('click',saveConfig); $('btn-connect')?.addEventListener('click',connectADB); $('btn-load-apps')?.addEventListener('click',loadApps); $('btn-add-app')?.addEventListener('click',addApp); $('btn-launch')?.addEventListener('click',launchSelected); }
  // iSG specific actions
  async function wakeISG(){ try{ const j=await api('/api/wake-isg',{method:'POST'}); toast(j.success?'iSG wake requested':'Wake failed: '+j.error, j.success); setTimeout(refreshStatus,800);}catch(e){toast('Wake error: '+e.message,false);} }
  async function restartISG(){ try{ const j=await api('/api/restart-isg',{method:'POST'}); toast(j.success?'iSG restart requested':'Restart failed: '+j.error, j.success); setTimeout(refreshStatus,1200);}catch(e){toast('Restart error: '+e.message,false);} }
  function bindISG(){ $('btn-isg-wake')?.addEventListener('click',wakeISG); $('btn-isg-restart')?.addEventListener('click',restartISG); $('btn-save-isg')?.addEventListener('click',saveConfig); }

  document.addEventListener('DOMContentLoaded', async ()=>{ bind(); bindISG(); await loadConfig(); await refreshStatus(); await loadApps(); setInterval(refreshStatus,5000); });
})();
