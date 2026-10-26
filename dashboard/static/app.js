'use strict';
const $ = s => document.querySelector(s);
const escapeHTML = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (x, digits=0) => x == null ? 'Unavailable' : Number(x).toLocaleString('en-IN',{maximumFractionDigits:digits,minimumFractionDigits:digits});
const pct = x => x == null ? 'Unavailable' : fmt(x,3)+'%';
const labels = {xgboost:'XGBoost',random_forest:'Random Forest',static:'Static',rule:'Rule-adaptive',adaptive:'Rule-adaptive',rl:'Trained RL',blind_rl:'Label-blind RL',zero_q:'Zero-Q',untrained_rl:'Zero-Q',high_value_burst:'High-value burst',slow_drain:'Slow drain',gradual_escalation:'Gradual escalation',beneficiary_hopping:'Beneficiary hopping'};
const label = x => labels[x] || x;
const pages = [
 ['overview','Overview','layout-dashboard','Recorded outcomes, not production guarantees.'],
 ['runner','Run Experiments','flask-conical','Choose a supported workflow. Preview the exact command before execution.'],
 ['terminal','Terminal & Logs','square-terminal','Actual subprocess output, timestamps and exit records.'],
 ['results','Results Explorer','table-2','Filter one experimental version. Inspect the records behind every result.'],
 ['detectors','Detector Comparison','split','Compare within the selected protocol, not across incompatible studies.'],
 ['attackers','Attacker Comparison','git-compare-arrows','Common online constraints do not imply equal offline training costs.'],
 ['campaigns','Campaign Analysis','list-tree','Follow the simulated money and intervention sequence.'],
 ['models','Data & Models','database','Artifact identities and provenance, including what remains unverified.'],
 ['validation','Validation & Tests','list-checks','Software correctness, evidence equality and scientific validity are separate.'],
 ['reports','Reports & Export','file-chart-column','Download scoped evidence and read the preserved research reports.'],
 ['settings','Settings','settings-2','Local runtime boundaries and display preferences.']
];
const state = {boot:null,run:'pilot-main',view:null,filters:{},page:'overview',sort:'detector',descending:false,offset:0,jobs:[],events:[],job:null,logCursor:0,logs:[],preview:null,serial:0,finished:new Set(),active:null};
state.loading=false;
let pollBusy=false;
function icons(){window.lucide?.createIcons();}
function error(message){$('#alert').textContent=message;$('#alert').hidden=!message;}
async function api(path, data){
 const options = data===undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json','X-Research-Token':state.boot.csrf},body:JSON.stringify(data)};
 const response=await fetch(path,options);const value=await response.json();
 if(!response.ok) throw new Error(value.error || 'Request failed');
 return value;
}
function qs(extra={}){return new URLSearchParams({run:state.run,...state.filters,...extra}).toString();}
function evidenceLink(source,text='Inspect source'){return source ? `<a href="${escapeHTML(source.url)}" download>${escapeHTML(text)} <i data-lucide="external-link"></i></a>` : '<span class="muted">Unavailable</span>';}
function version(){return state.view?.kind==='pilot'?'Mechanism pilot v1':'Academic prototype v1';}
function panel(title,body,subtitle='',actions=''){return `<section class="panel"><div class="panel-head"><div><h2>${title}</h2>${subtitle?`<small>${subtitle}</small>`:''}</div>${actions}</div>${body}</section>`;}
function empty(title,text){return `<div class="empty"><h2>${title}</h2><p>${text}</p></div>`;}
function nav(page){location.hash=page;}
function runOptions(){return state.boot.runs.map(r=>`<option value="${escapeHTML(r.id)}" ${r.id===state.run?'selected':''}>${escapeHTML(r.label)}</option>`).join('');}
function drawFilters(){
 if(!state.view)return;
 $('#filters').innerHTML = ['detector','strategy','family','block','outcome'].map(k=>{
 const values=k==='outcome'?['completed','stopped']:state.view.options[k];
 const plural=({block:'replications',family:'families',strategy:'strategies'})[k]||k+'s';
 return `<label>${({block:state.view.kind==='pilot'?'Block':'Seed',outcome:'Outcome'})[k]||k[0].toUpperCase()+k.slice(1)}<select data-filter="${k}" aria-label="Filter ${k}"><option value="">All ${plural}</option>${values.map(v=>`<option value="${escapeHTML(v)}" ${String(state.filters[k])===v?'selected':''}>${escapeHTML(label(v))}</option>`).join('')}</select></label>`;
 }).join('')+'<button class="text-button" id="reset-filters">Reset filters</button>';
}
async function loadView(renderPage=true){
 const request=++state.serial;
 state.loading=true;$('#content').setAttribute('aria-busy','true');
 $('#csv-export').setAttribute('aria-disabled','true');
 $('#protocol').textContent='Loading selected evidence…';
 error('');
 try{
 const view=await api('/api/summary?'+qs());
 if(request!==state.serial)return;
 state.view=view;
 state.loading=false;$('#content').removeAttribute('aria-busy');
 $('#csv-export').removeAttribute('aria-disabled');
 $('#protocol').textContent=version()+' / '+fmt(view.totals.campaigns)+' selected campaigns';
 $('#evidence-status').textContent=view.proof?.label || 'Parsed records; no independent verifier result for this run';
 $('#csv-export').href='/api/export?'+qs();
 drawFilters();if(renderPage)await render();
 }catch(e){if(request!==state.serial)return;state.loading=false;$('#content').removeAttribute('aria-busy');state.view=null;error(e.message);$('#page').innerHTML=empty('Evidence is unavailable','Choose another run or inspect the records. No values have been substituted.');}
 icons();
}
function metric(title,value,detail,definition){
 return `<div class="metric"><div class="metric-label">${title}<i data-lucide="info"></i></div><div class="metric-value">${value}</div><small>${detail}</small><details><summary>Definition and evidence</summary><p>${definition}</p><p>${evidenceLink(state.view.sources[0],'Selected run manifest')} · <button class="text-button" data-nav="campaigns">Underlying records</button></p></details></div>`;
}
function overview(){
 const t=state.view.totals;
 const rate=t.campaigns?100*t.completed/t.campaigns:null;
 const ledger='<div class="ledger">'+
 metric('Campaign completion',pct(rate),`${fmt(t.completed)} / ${fmt(t.campaigns)} campaigns`,'Simulated campaigns that reached the defined target. The denominator includes only the selected filters.')+
 metric('Transactions evaluated',fmt(t.transactions),`${fmt(t.allow)} allow / ${fmt(t.flag)} flag / ${fmt(t.block)} block`,'Recorded detector-evaluated transactions, not all rejected pre-execution proposals. Counts come from transaction rows.')+
 metric('Gross simulated transfer','₹'+fmt(t.gross,2),'Actual simulated source debit','Sum of amount_transferred in recorded transactions. This is neither real victim loss nor prevented loss.')+
 metric('Local execution ledger',`${state.jobs.filter(j=>j.status==='completed').length} / ${state.jobs.filter(j=>j.status==='failed').length}`,'Completed / failed dashboard jobs','Actual jobs started through this dashboard. Imported research runs are separate; cancelled and interrupted jobs are not counted as failed.')+'</div>';
 return ledger+`<div class="split"><div>${panel('Campaign outcomes',table(state.view.groups.slice(0,8),true),`${version()} · complete denominator within current filters`,`<button class="text-button" data-nav="results">View all results <i data-lucide="chevron-right"></i></button>`)}${panel('Execution activity',activity(), 'Local job activity and imported execution provenance')}</div><div>${benignPanel()}${panel('Interpretation boundary','<div class="panel-body finding">The comparison is <strong>exploratory and synthetic</strong>. A campaign completing is an attacker outcome, not evidence that a real payment system would fail.<p>Held-out GE means the declared pattern was excluded from registered development artifacts. Shared features may overlap; old detector ancestry remains unverified.</p><p>Gross debit is not unrecovered victim loss. Software test passes do not establish scientific validity.</p></div>')}</div></div>`;
}
function activity(){
 const events=state.events.slice(0,6);
 if(!events.length){
 const imported=state.boot.runs.filter(r=>r.execution).slice(0,4);
 return '<div class="panel-body">'+imported.map(r=>`<div class="activity-row"><i data-lucide="archive"></i><div>${escapeHTML(r.label)}<small>Imported execution record · exit ${r.execution.exit_code}</small></div><time>${escapeHTML(new Date(r.execution.end).toLocaleString())}</time></div>`).join('')+'<p class="notice">No local jobs yet. Imported completion times are preserved provenance, not jobs executed by this dashboard.</p></div>';
 }
 return '<div class="panel-body">'+events.map(e=>`<div class="activity-row"><i data-lucide="${e.action.includes('failed')?'circle-alert':'activity'}"></i><div>${escapeHTML(e.name||e.run||e.action)}<small>${escapeHTML(e.action.replaceAll('_',' '))}${e.exit_code!=null?' · exit '+e.exit_code:''}</small></div><time>${escapeHTML(new Date(e.timestamp).toLocaleTimeString())}</time></div>`).join('')+'</div>';
}
function benignPanel(){
 if(!state.view.benign.length)return panel('Benign controls unavailable','<div class="panel-body finding">The legacy experiment has no matched benign mechanism-shift stratum. No false-block value is invented. Select a pilot run to inspect the separate benign controls.</div>');
 const mimic=state.view.benign.filter(b=>b.stratum==='benign_mimic_test');
 return `<section class="panel warning-panel"><div class="panel-head"><div><h2>Benign mechanism shift</h2><small>Legitimate GE-mimic episodes blocked</small></div><i data-lucide="triangle-alert"></i></div><div class="panel-body">${mimic.map(b=>`<div class="activity-row"><i data-lucide="shield-alert"></i><div>${label(b.detector)}<small>${fmt(b.blocked)} / ${fmt(b.n)} benign episodes</small></div><strong class="warning-text">${pct(b.rate)}</strong></div>`).join('')}<p class="notice">These detector/block-filtered benign strata are independent of attacker/family/outcome filters. High false blocking limits useful fraud discrimination. This is not a deployment-ready operating point.</p><button class="text-button" data-nav="detectors">Inspect benign controls <i data-lucide="chevron-right"></i></button></div></section>`;
}
function table(groups,compact=false){
 if(!groups.length)return empty('No matching records','Reset filters to restore the recorded evaluation scope.');
 const sorted=[...groups].sort((a,b)=>{let x=a[state.sort],y=b[state.sort];return (typeof x==='number'?x-y:String(x).localeCompare(String(y)))*(state.descending?-1:1);});
 const headings=compact?[['detector','Detector'],['family','Mechanism'],['strategy','Strategy'],['campaigns','n'],['completion','Completed']]:
 [['detector','Detector'],['strategy','Strategy'],['family','Mechanism'],['campaigns','Attempted'],['completed','Completed'],['completion','Completion %'],['block_sd','Block SD (pp)'],['allow','Allow'],['flag','Flag'],['block','Block'],['mean_attempts','Mean attempts'],['gross','Gross transfer (INR)']];
 return `<div class="table-scroll"><table><thead><tr>${headings.map(([k,v])=>`<th class="${['detector','family','strategy'].includes(k)?'':'numeric'}"><button data-sort="${k}" title="Sort by ${v}">${v}${state.sort===k?(state.descending?' ↓':' ↑'):''}</button></th>`).join('')}</tr></thead><tbody>${sorted.map(g=>`<tr data-detail="${state.view.groups.indexOf(g)}" tabindex="0" role="button" aria-label="Explain ${label(g.detector)} ${label(g.strategy)} ${label(g.family)}">${headings.map(([k])=>`<td class="${['detector','family','strategy'].includes(k)?'':'numeric'}">${k==='completion'?`<span class="rate-cell"><span class="mini-bar"><span style="width:${g.completion}%"></span></span>${pct(g.completion)}</span>`:k==='block_sd'?g[k]==null?'—':fmt(g[k],2):k==='gross'?'₹'+fmt(g[k],2):k==='mean_attempts'?fmt(g[k],2):['detector','family','strategy'].includes(k)?escapeHTML(label(g[k])):fmt(g[k])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function results(){return panel('Recorded comparison cells',table(state.view.groups),`${version()} · ${fmt(state.view.totals.campaigns)} campaigns · click any row for an evidence-based explanation`)+panel('How to read this table','<div class="panel-body finding">Completion is completed campaigns / selected campaigns. Allow, FLAG and BLOCK are transaction counts, not mutually exclusive campaign outcomes. Block SD is the sample standard deviation of completion rates across selected independent blocks/seeds, in percentage points; one replication has no SD.<p>Outcome filters condition the denominator. A completed-only filter is not an overall success-rate estimate. Benign false-block rates are a separate episode denominator, shown in Detector Comparison rather than merged into attacker cells.</p><p>'+evidenceLink(state.view.sources[0],'Inspect selected protocol manifest')+'</p></div>');}
function chart(rows,metric='completion',title='Campaign completion (%)'){
 if(!rows.length)return empty('No comparable cells','Select a detector, strategy or mechanism with recorded outcomes.');
 const chartRows=rows.map(g=>({name:`${label(g.detector)} / ${label(g.strategy)}`,sub:label(g.family),value:g[metric],n:g.campaigns,sd:g.block_sd}));
 return `<div class="chart" data-chart="${escapeHTML(title)}">${chartRows.map(g=>`<div class="chart-row" title="${escapeHTML(title)}: ${pct(g.value)}; n=${g.n}; block SD ${g.sd==null?'unavailable':fmt(g.sd,2)+' pp'}"><div class="chart-label">${escapeHTML(g.name)}<small>${escapeHTML(g.sub)} · n=${fmt(g.n)}</small></div><div class="bar-track"><div class="bar-fill" style="width:${Math.max(0,Math.min(100,g.value))}%"></div></div><div class="numeric">${fmt(g.value,2)}%</div></div>`).join('')}<div class="axis"><span>0</span><span>25</span><span>50</span><span>75</span><span>100%</span></div><div class="chart-caption">${title} · ${version()}. Full 0–100% scale. Hover for n and block SD; table contains variability. Not a confidence interval.</div></div>`;
}
function benignChart(){
 if(!state.view.benign.length)return '';
 return panel('Ordinary benign vs mechanism-shift controls','<div class="chart">'+state.view.benign.map(b=>`<div class="chart-row" title="${fmt(b.blocked)} / ${fmt(b.n)} legitimate episodes blocked"><div class="chart-label">${label(b.detector)}<small>${b.stratum==='benign_test'?'Ordinary benign':'GE-mimic benign'} · n=${fmt(b.n)}</small></div><div class="bar-track"><div class="bar-fill ${b.stratum==='benign_mimic_test'?'warn':''}" style="width:${b.rate}%"></div></div><div>${fmt(b.rate,2)}%</div></div>`).join('')+'<div class="axis"><span>0</span><span>25</span><span>50</span><span>75</span><span>100%</span></div><p class="chart-caption">Benign false-block rate (%). Detector/block filters only. Episodes are clustered by block; no binomial-independence confidence interval is asserted.</p><p class="notice">'+evidenceLink(state.view.benign[0].sources[0],'Inspect underlying benign scores')+'</p></div>',version());
}
function comparison(){
 const groups=state.view.groups;
 return `<div class="split"><div>${panel(state.page==='detectors'?'Completion by detector':'Completion by attacker',chart(groups),'Same selected version and filters',`<button class="text-button" id="export-chart"><i data-lucide="image-down"></i> Export SVG</button>`)}${benignChart()}</div><div>${benignPanel()}${panel('Comparison contract','<div class="panel-body finding">'+(state.view.kind==='pilot'?'The pilot matches online legal actions, clipping, pacing opportunities and resource limits. Label-blind RL still observes detector-derived rewards during training; it is not detector-naive. Offline training cost is not equal to static/rule/zero-Q.':'Legacy arms have action-space/pacing/clipping asymmetries. A rate difference does not isolate adaptation as its cause.')+'<p>Only within-family, within-version cells should be paired. Policy/context samples sharing one fitted model are not independent model replications. Repeats/reloads are reproducibility checks, not new seeds.</p><button class="text-button" data-nav="results">Inspect underlying data</button></div>')}</div></div>`+panel('Variability and sample sizes',table(groups));
}
function explain(index){
 const g=state.view.groups[index];if(!g)return;
 $('#detail-title').textContent='Explain this result';
 $('#detail-body').innerHTML=`<p>${escapeHTML(label(g.detector))} / ${escapeHTML(label(g.strategy))} / ${escapeHTML(label(g.family))}</p><div class="facts"><div><small>Completed / attempted</small><strong>${g.completed} / ${g.campaigns}</strong></div><div><small>Campaign completion</small><strong>${pct(g.completion)}</strong></div><div><small>Independent blocks/seeds</small><strong>${g.blocks}</strong></div></div><p>Out of ${g.campaigns} evaluated campaigns, ${g.completed} completed successfully (${pct(g.completion)}). This is the observed rate for ${escapeHTML(state.run)} and the current filters; it does not establish similar performance in real payment systems.</p><p>Gross simulated transfer was ₹${fmt(g.gross,2)}, not actual victim loss. Block SD is ${g.block_sd==null?'unavailable for one replication':fmt(g.block_sd,3)+' percentage points'}. No causal explanation is inferred.</p><p>Validation: ${escapeHTML(state.view.proof?.label||'Parsed only; independent verification not recorded')}.</p><div class="actions"><button class="primary" id="inspect-group" data-group="${index}">Inspect campaign records</button>${evidenceLink(state.view.sources[0],'Protocol and model identities')}</div>`;
 $('#detail-dialog').showModal();icons();
}
async function campaigns(){
 const data=await api('/api/campaigns?'+qs({offset:state.offset}));
 return panel('Campaign evidence ledger',`<div class="table-scroll"><table><thead><tr><th>Campaign / original identity</th><th>Detector</th><th>Strategy</th><th>Mechanism</th><th>Seed/block</th><th>Outcome</th><th class="numeric">Gross (INR)</th><th>Evidence</th></tr></thead><tbody>${data.rows.map(r=>`<tr><td><button class="text-button mono" data-campaign="${r.index}">${escapeHTML(r.campaign_id)}</button></td><td>${label(r.detector)}</td><td>${label(r.strategy)}</td><td>${label(r.family)}</td><td>${r.block}</td><td>${r.success?'Completed':'Stopped'}</td><td class="numeric">${fmt(r.gross,2)}</td><td>${evidenceLink(r.source,'Record '+r.source_line)}</td></tr>`).join('')}</tbody></table></div><div class="table-foot"><span>${data.total?state.offset+1:0}–${Math.min(data.total,state.offset+50)} of ${fmt(data.total)} campaigns</span><div class="actions"><button id="previous-campaigns" class="secondary" ${state.offset===0?'disabled':''}>Previous</button><button id="next-campaigns" class="secondary" ${state.offset+50>=data.total?'disabled':''}>Next</button></div></div>`,version())+(data.total?'':empty('No campaigns match','Reset filters to inspect the full recorded run.'));
}
async function campaign(index){
 const data=await api('/api/campaign?'+qs({index})),r=data.record;
 $('#detail-title').textContent='Campaign '+r.campaign_id;
 $('#detail-body').innerHTML=`<div class="facts"><div><small>Termination</small><strong>${escapeHTML(r.reason)}</strong></div><div><small>Target</small><strong>₹${fmt(r.target,2)}</strong></div><div><small>Gross source debit</small><strong>₹${fmt(r.gross,2)}</strong></div><div><small>Completion</small><strong>${r.success?'Target reached':'Not completed'}</strong></div><div><small>Detector / strategy</small>${label(r.detector)} / ${label(r.strategy)}</div><div><small>Seed/block / start</small>${r.block} / ${escapeHTML(r.start)}</div></div><div class="table-scroll"><table><thead><tr><th>Step</th><th>Simulated time</th><th>Gap (s)</th><th>Proposed INR</th><th>Transferred INR</th><th>Decision</th><th>Terminal</th></tr></thead><tbody>${r.timeline.map(t=>`<tr><td>${t.step}</td><td class="mono">${escapeHTML(t.time)}</td><td>${fmt(t.gap,3)}</td><td>${fmt(t.amount,2)}</td><td>${fmt(t.transferred,2)}</td><td class="decision ${t.decision}">${t.decision}</td><td>${t.terminal?'Yes':'No / not recorded'}</td></tr>`).join('')}</tbody></table></div><p>FLAG is an alert; it may still transfer. BLOCK-proposed money is not actual debit or proven savings. A source file link downloads the original file; row ${r.source_line} identifies this campaign within it.</p><div class="actions">${evidenceLink(r.source,'Original record file')}${evidenceLink(data.manifest,'Configuration / model provenance')}</div><details><summary>Exact campaign record and configuration</summary><pre>${escapeHTML(JSON.stringify({record:r.raw,config:data.config},null,2))}</pre></details>`;
 $('#detail-dialog').showModal();icons();
}
async function models(){
 const all=await api('/api/models?'+qs()),rows=all.filter(r=>(!state.filters.detector||r.detector===state.filters.detector)&&(!state.filters.block||String(r.block)===state.filters.block));
 return panel('Detector artifact inventory',`<div class="table-scroll"><table><thead><tr><th>Detector</th><th>Block</th><th>SHA-256</th><th>Fit episodes</th><th>Provenance</th><th>Membership</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${label(r.detector)}</td><td>${r.block??'Legacy'}</td><td class="hash mono" title="${r.sha256}">${r.sha256}</td><td>${r.fitting??'Unverified'}</td><td>${escapeHTML(r.provenance)}<br>${evidenceLink(r.binding,'Fit binding')}</td><td>${evidenceLink(r.membership,'Dataset roles')}<br>${evidenceLink(r.evaluation,'Evaluation contexts')}</td></tr>`).join('')}</tbody></table></div>`,`${version()} · no model is deserialized by the dashboard`)+panel('Holdout and membership boundary','<div class="panel-body finding">New bindings associate pickle bytes with registered feature/label matrices, fitting episode IDs, seeds and source hashes. The registry separates fitting, validation, calibration and benign test roles. Attack evaluation contexts have a separate plan.<p>Only the declared GE generator/ancestry/prefix is excluded in the new study. Shared scalar features may overlap. Historical detector-family training exclusion is not established; no metadata inference upgrades that claim.</p><p>Membership files expose complete recorded roles, not a dashboard-generated lineage guess. Model files are hashed as bytes, never unpickled by this interface.</p></div>');
}
function freshName(prefix='demo'){return prefix+'-'+new Date().toISOString().replace(/\D/g,'').slice(0,14);}
function presets(){return `<div class="preset-list">${[['short','Short demonstration'],['tests','Selected tests'],['legacy','Legacy experiment'],['pilot','Mechanism pilot'],['repeat','Repeat experiment'],['reload','Saved checkpoints'],['verify','Verify outputs'],['export','Export report']].map(([k,v])=>`<button class="secondary" data-preset="${k}">${v}</button>`).join('')}</div>`;}
function runner(){
 const refs=state.boot.runs;
 return presets()+`<div class="runner-layout"><section class="panel"><form id="experiment-form"><div class="form-section"><h2>Execution workflow</h2><div class="form-grid"><label>Experiment type<select id="experiment-type"><option value="legacy">Legacy prototype</option><option value="pilot">Mechanism-holdout pilot</option><option value="tests">Test suite</option><option value="verify">Output verification</option><option value="checkpoint">Checkpoint reload / evaluation</option></select></label><label>Execution mode<select id="execution-mode"><option value="main">Main run</option><option value="repeat">Repeat</option><option value="reload">Checkpoint reload</option></select></label><label>Fresh output name<input id="output-name" value="${freshName()}" maxlength="48" required pattern="[a-z0-9][a-z0-9_-]{0,47}"></label></div><p class="notice">Names are restricted to a private dashboard output root. Existing directories cannot be overwritten.</p></div><div class="form-section" id="reference-fields"><h2>Registered reference evidence</h2><div class="form-grid">${['reference','repeat','reload'].map(k=>`<label id="${k}-label">${k[0].toUpperCase()+k.slice(1)} run<select id="${k}-run">${refs.map(r=>`<option value="${escapeHTML(r.id)}">${escapeHTML(r.label)} (${r.kind})</option>`).join('')}</select></label>`).join('')}</div><p class="notice">Repeat/reload inherit the selected reference configuration. Verification requires three runs of one protocol.</p></div><div class="form-section" id="configuration-fields"><h2>Attacker and detector contract</h2><div class="form-grid"><label>Detector<select id="detector-option"><option value="both">Both detectors</option><option value="xgboost">XGBoost</option><option value="random_forest">Random Forest</option></select></label><label>Attacker strategy<select id="attacker-option"><option value="all">All supported strategies</option><option value="static">Static</option><option value="adaptive">Rule-adaptive</option><option value="rl">Trained RL</option><option value="untrained_rl">Zero-Q control</option></select></label><label>Campaign family<select id="family-option" disabled><option>All supported families</option></select></label></div><p id="support-note" class="notice"></p><div class="form-grid"><label id="seed-label">Seeds (comma separated)<input id="seeds-option" value="101"></label><label id="block-label">Independent blocks<input id="blocks-option" type="number" value="1" min="1" max="9"></label><label>Policy training episodes<input id="episodes-option" type="number" value="60" min="1" max="300"></label><label id="campaign-label">Campaigns per legacy cell<input id="campaigns-option" type="number" value="6" min="1" max="40"></label><label id="context-label">Contexts per pilot mechanism<input id="contexts-option" type="number" value="3" min="1" max="40"></label><label id="step-label">Maximum steps<input id="steps-option" type="number" value="30" min="1" max="30"></label><label>Time constraint<input id="duration-option" readonly value="Protocol-defined; not a CLI flag"></label><label>Campaign budget<input id="budget-option" readonly value="Protocol-defined; not a CLI flag"></label></div><details id="pilot-advanced"><summary>Pilot detector-development sizes</summary><div class="form-grid">${[['train-episodes',1000,4,1000,'Detector-fit episodes'],['validation',400,1,400,'Validation episodes'],['calibration',1000,2,1000,'Benign calibration episodes'],['benign-test',400,1,400,'Each benign test stratum'],['seed-base',51000,0,2147483647,'Seed namespace base']].map(([k,v,min,max,t])=>`<label>${t}<input id="${k}-option" type="number" value="${v}" min="${min}" max="${max}"></label>`).join('')}</div></details></div><div class="form-section" id="test-fields"><h2>Fixed safe selection</h2><label>Test selection<select id="test-selection"><option value="rl">47-case existing RL suite</option><option value="regression">420-case integrated selected regression</option><option value="dashboard">Dashboard adapter and security tests</option></select></label><p class="notice">No unrestricted pytest, archived failure fixtures or Gate C command can be submitted.</p></div><div class="form-section"><div id="run-error" class="inline-error" role="alert"></div><button id="execute" class="primary" type="submit" disabled><i data-lucide="play"></i> Run experiment</button><span class="notice" id="duplicate-note"></span></div></form></section><div>${panel('Execution preview','<div class="panel-body"><span id="workload" class="tiny-label">Validating choices</span><pre id="command-preview" class="command">Reading supported command…</pre><div id="expensive-notice" class="notice"></div><p class="notice">Execution uses a fixed interpreter and repository. No shell strings, arbitrary paths, Git mutation, publication or Gate C actions are accepted.</p></div>')}${panel('Output and cancellation','<div class="panel-body finding">One process group may run at a time. A larger job requires confirmation. Cancellation sends TERM, then KILL after a grace period; partial outputs are preserved, not marked complete.<p>Live logs and exit records appear in Terminal & Logs. Completed experiment jobs open their own results automatically.</p><button class="text-button" data-nav="terminal">Open execution log</button></div>')}</div></div>`;
}
function formKind(){let k=$('#experiment-type').value;return k==='checkpoint'?(state.boot.runs.find(r=>r.id===$('#reference-run').value)?.kind||'pilot'):k;}
function configureForm(){
 const kind=formKind(),mode=$('#experiment-type').value==='checkpoint'?'reload':$('#execution-mode').value,ref=mode!=='main';
 $('#execution-mode').disabled=$('#experiment-type').value==='checkpoint'||['tests','verify'].includes(kind);
 $('#configuration-fields').hidden=!['legacy','pilot'].includes(kind)||ref;
 $('#test-fields').hidden=kind!=='tests';
 $('#reference-fields').hidden=!(ref||kind==='verify');
 for(const k of ['repeat','reload'])$('#'+k+'-label').hidden=kind!=='verify';
 $('#detector-option').disabled=kind==='pilot';$('#attacker-option').disabled=kind==='pilot';
 $('#block-label').hidden=kind!=='pilot';$('#context-label').hidden=kind!=='pilot';$('#pilot-advanced').hidden=kind!=='pilot';
 $('#seed-label').hidden=kind!=='legacy';$('#campaign-label').hidden=kind!=='legacy';$('#step-label').hidden=kind!=='legacy';
 $('#support-note').textContent=kind==='pilot'?'Pilot CLI fixes both detectors, all five arms (including label-blind RL), HVB and GE, 30 steps, 86,400 seconds and target-sized budget. No per-arm or per-family CLI selector exists.':'Legacy CLI supports four arms and both detectors. Family selection and budget/duration are not CLI flags; those protocol settings are not editable here. FLAG is an alert, not necessarily a rejection.';
 $('#family-option').options[0].textContent=kind==='pilot'?'HVB and GE (fixed)':'All four legacy families (fixed)';
 $('#duration-option').value=kind==='pilot'?'86,400 simulated seconds (fixed)':'No duration CLI flag';
 $('#budget-option').value=kind==='pilot'?'Target amount (fixed)':'No budget CLI flag';
}
function formData(){
 const type=formKind(),mode=$('#experiment-type').value==='checkpoint'?'reload':$('#execution-mode').value;
 const result={type,mode,name:$('#output-name').value};
 if(type==='tests')return {...result,mode:'main',selection:$('#test-selection').value};
 if(type==='verify')return {...result,mode:'main',reference:$('#reference-run').value,repeat:$('#repeat-run').value,reload:$('#reload-run').value};
 if(mode!=='main')return {...result,reference:$('#reference-run').value};
 if(type==='legacy')return {...result,detector:$('#detector-option').value,attacker:$('#attacker-option').value,seeds:$('#seeds-option').value.split(',').map(v=>Number(v.trim())),episodes:Number($('#episodes-option').value),campaigns:Number($('#campaigns-option').value),max_steps:Number($('#steps-option').value)};
 for(const k of ['blocks','episodes','contexts','train-episodes','validation','calibration','benign-test','seed-base'])result[k.replaceAll('-','_')]=Number($('#'+k+'-option').value);
 return result;
}
let previewTimer,previewSerial=0;
async function preview(){
 if(!$('#experiment-form'))return;
 configureForm();
 const serial=++previewSerial;
 try{const result=await api('/api/preview',formData());if(serial!==previewSerial||!$('#experiment-form'))return;state.preview=result;$('#command-preview').textContent=result.command;$('#workload').textContent=result.workload?`${fmt(result.workload.training_episodes)} policy-training episodes / ${fmt(result.workload.evaluation_campaigns)} evaluation campaigns`:'Fixed verification or test selection';$('#expensive-notice').textContent=result.expensive?'Larger run: explicit confirmation is required. No runtime estimate is claimed.':'';$('#run-error').textContent='';$('#execute').disabled=!!state.active;$('#duplicate-note').textContent=state.active?'A job is already active.':'';}catch(e){if(serial!==previewSerial||!$('#experiment-form'))return;state.preview=null;$('#run-error').textContent=e.message;$('#execute').disabled=true;}
}
async function startJob(confirmed=false){
 const data=formData();if(confirmed)data.confirm_expensive=true;
 try{const job=await api('/api/jobs',data);state.jobs.unshift(job);state.job=job.id;state.active=job.id;state.logCursor=0;state.logs=[];nav('terminal');await poll();}catch(e){if($('#run-error'))$('#run-error').textContent=e.message;else error(e.message);}
}
function applyPreset(key){
 if(key==='export'){nav('reports');return;}
 if(state.page!=='runner'){state.pendingPreset=key;nav('runner');return;}
 $('#output-name').value=freshName(key);
 $('#experiment-type').value=['pilot','tests','verify'].includes(key)?key:'legacy';
 if(['repeat','reload'].includes(key))$('#experiment-type').value=state.boot.runs.find(r=>r.id===state.run)?.kind||'legacy';
 $('#execution-mode').value=['repeat','reload'].includes(key)?key:'main';
 $('#reference-run').value=key==='repeat'||key==='reload'?state.run:'pilot-main';
 $('#repeat-run').value='pilot-repeat';$('#reload-run').value='pilot-reload';
 if(key==='legacy'){$('#episodes-option').value=300;$('#campaigns-option').value=24;$('#seeds-option').value='101,202,303';}
 if(key==='short'){$('#episodes-option').value=60;$('#campaigns-option').value=6;$('#seeds-option').value='101';}
 if(key==='pilot'){$('#episodes-option').value=10;$('#blocks-option').value=1;$('#contexts-option').value=3;}
 if(key==='tests')$('#test-selection').value='regression';
 preview();
}
function terminal(){
 const job=state.jobs.find(j=>j.id===state.job)||state.jobs[0];if(job&&!state.job)state.job=job.id;
 return presets()+panel('Execution stream',`<div class="job-summary"><select id="job-select" class="job-select" aria-label="Execution job">${state.jobs.map(j=>`<option value="${j.id}" ${j.id===state.job?'selected':''}>${escapeHTML(j.name)} · ${j.status}</option>`).join('')||'<option>No local executions</option>'}</select><span id="job-status" class="status ${job?.status||''}">${job?.status||'Idle'}</span><span id="job-exit">Exit ${job?.exit_code??'—'}</span><span id="job-elapsed">${job?fmt(job.elapsed,1)+' s':'—'}</span></div><div class="panel-body" id="job-command">${job?`<pre class="command">${escapeHTML(job.command)}</pre>`:'Choose a preset to run the real program. No sample terminal output is shown.'}</div><div class="panel-head"><span class="tiny-label">Timestamp / stream / output</span><div class="actions"><button id="copy-log" class="text-button" ${!job?'disabled':''}><i data-lucide="copy"></i> Copy</button><a id="download-log" ${job?`href="/api/log-download?job=${job.id}"`:''} class="text-button" download><i data-lucide="download"></i> Download</a><button id="cancel-job" class="secondary danger" ${!state.active?'disabled':''}><i data-lucide="square"></i> Stop</button></div></div><div id="log-output" class="terminal" role="log" aria-label="Process output">${state.logs.length?logHTML():job?'Waiting for output…':'No job has started.'}</div>`);
}
function logHTML(){return state.logs.slice(-3000).map(l=>`<div class="log-line ${l.channel}"><time title="${escapeHTML(l.timestamp)}">${escapeHTML(new Date(l.timestamp).toLocaleTimeString('en-GB'))}</time><span class="log-channel">${l.channel}</span><span class="log-text">${escapeHTML(l.text)}</span></div>`).join('');}
function validation(){
 const imported=state.boot.prior_tests.map(t=>`<div class="panel-body"><h3>${t.name==='prior-regression.xml'?'Imported prior selection':'Imported overlapping RL subset'}</h3><p>${t.counts.passed} passed / ${t.counts.failures} failed / ${t.counts.errors} errors / ${t.counts.skipped} skipped / ${t.counts.deselected} deselected</p><small>Recorded ${escapeHTML(t.counts.timestamp||'Unavailable')} · not a test run started by the dashboard</small><p>${evidenceLink(t.source,'JUnit report')}</p></div>`).join('');
 const local=state.jobs.filter(j=>['tests','verify'].includes(j.kind)).map(j=>`<div class="report-row"><div><h3>${escapeHTML(j.name)}</h3><span class="status ${j.status}">${j.status}</span> · exit ${j.exit_code??'—'} · ${fmt(j.elapsed,1)} s${j.counts?`<p>${j.counts.passed} passed / ${j.counts.failures} failed / ${j.counts.errors} errors / ${j.counts.skipped} skipped / ${j.counts.deselected??'unavailable'} deselected</p>`:''}${j.verification?`<p>Evidence complete: ${j.verification.evidence_complete}; scientific validity: not validated</p>`:''}<details><summary>Exact command</summary><pre class="command">${escapeHTML(j.command)}</pre></details></div><button class="text-button" data-job="${j.id}">View log</button></div>`).join('');
 return `<div class="split"><div>${panel('Local validation jobs',local||empty('No local validation yet','Run a fixed test selection or verify the registered output triplet.'),'Actual dashboard executions',`<button class="secondary" data-preset="tests">Run selected tests</button>`)}${panel('Preserved software-test evidence',imported)}</div><div>${panel('Selected evidence status',`<div class="panel-body finding">${escapeHTML(state.view?.proof?.label||'No independent validation attached to this run.')}<p>Evidence completeness asks whether required records exist and are valid. Byte equality asks whether selected artifacts reproduce. Neither establishes scientific validity.</p>${state.view?.proof?evidenceLink(state.view.proof.artifact,'Independent verification report'):''}</div>`)}${panel('Scientific status','<div class="panel-body finding">Exploratory synthetic results only. Benign-shift false blocking, limited features, partial mechanism coverage, nine independent blocks and no powered lockbox study remain limitations.<p>Gate C: <strong>HOLD</strong>. Software tests do not authorize downstream workflows.</p></div>')}</div></div>`;
}
async function reports(){
 const files=await api('/api/reports');
 return panel('Export current selection',`<div class="panel-body finding">Run: <strong>${escapeHTML(state.run)}</strong>. Filters: ${escapeHTML(JSON.stringify(state.filters))}. Exports retain the protocol identifier, sample counts and limitations.<div class="actions"><a class="primary" href="/api/export?${qs()}" download>Export filtered CSV</a><a class="secondary" href="/api/export?${qs({format:'markdown'})}" download>Generate evidence report</a><button class="secondary" id="export-chart">Export comparison SVG</button></div></div>`)+panel('Preserved research reports',files.map(f=>`<div class="report-row"><div><h3>${escapeHTML(f.name)}</h3><small>${fmt(f.bytes)} bytes · exact Markdown file</small></div>${evidenceLink(f,'Download')}</div>`).join(''));
}
function settings(){return panel('Local execution boundary',`<div class="panel-body"><div class="facts"><div><small>Network binding</small>127.0.0.1 only</div><div><small>Concurrent process groups</small>One</div><div><small>Execution limits</small>30 minutes / larger jobs 2 hours</div><div><small>Shell endpoint</small>Not available</div><div><small>Output location</small>Private dashboard-state/runs root</div><div><small>Gate C</small><span class="warning-text">HOLD</span></div></div><p class="finding">Only fixed Python commands and validated arguments can run. The browser cannot choose executable paths, arbitrary output paths or environment variables. Mutation requests require the local origin and a session token. This is a single-user tool, not an internet-facing multi-user service.</p></div>`)+panel('Inspected runtime',`<div class="panel-body"><p>Python ${escapeHTML(state.boot.environment.python)} · ${escapeHTML(state.boot.environment.status)}</p><pre class="command">${escapeHTML(JSON.stringify(state.boot.environment.packages,null,2))}</pre><p class="notice">${escapeHTML(state.boot.environment.note)} No secrets or inherited environment values are displayed.</p><button id="settings-theme" class="secondary">Switch theme</button></div>`);}
async function render(){
 const renderPage=state.page,renderSerial=state.renderSerial=(state.renderSerial||0)+1;
 const entry=pages.find(x=>x[0]===state.page)||pages[0];
 $('#page-title').textContent=entry[1];$('#breadcrumb').textContent=entry[1];$('#page-subtitle').textContent=entry[3];
 document.title=entry[1]+' | UPI Fraud Stress Lab';
 document.querySelectorAll('nav a').forEach(a=>{a.classList.toggle('active',a.dataset.page===state.page);a.setAttribute('aria-current',a.dataset.page===state.page?'page':'false');});
 const scoped=['overview','results','detectors','attackers','campaigns','models','reports'].includes(state.page);
 $('#scope-panel').hidden=!scoped;$('#filters').hidden=!['overview','results','detectors','attackers','campaigns','models'].includes(state.page);
 let html;
 if(state.page==='runner')html=runner();
 else if(state.page==='terminal')html=terminal();
 else if(state.page==='validation')html=validation();
 else if(state.page==='settings')html=settings();
 else if(state.page==='reports')html=await reports();
 else if(!state.view)html=empty('No evidence selected','Choose a recorded run. Metrics are unavailable until valid records load.');
 else if(state.page==='overview')html=overview();
 else if(state.page==='results')html=results();
 else if(['detectors','attackers'].includes(state.page))html=comparison();
 else if(state.page==='campaigns')html=await campaigns();
 else if(state.page==='models')html=await models()+await dataInventory();
 if(renderPage!==state.page||renderSerial!==state.renderSerial)return;
 $('#page').innerHTML=html;icons();
 if(state.page==='runner'){configureForm();preview();}
}
function theme(){
 const dark=document.documentElement.dataset.theme==='dark';document.documentElement.dataset.theme=dark?'light':'dark';
 $('#theme').innerHTML=`<i data-lucide="${dark?'moon':'sun'}"></i> ${dark?'Dark':'Light'} theme`;
 $('#theme').setAttribute('aria-label','Switch to '+(dark?'dark':'light')+' theme');icons();
}
async function dataInventory(){
 const files=await api('/api/datasets?'+qs());
 const models=await api('/api/models?'+qs());
 const policies=models.filter(r=>(!state.filters.detector||r.detector===state.filters.detector)&&(!state.filters.block||String(r.block)===state.filters.block)).flatMap(m=>(m.policies||[]).map(p=>({...p,detector:m.detector,block:m.block})));
 return panel('Dataset fingerprints',`<details class="panel-body"><summary>${files.length} available data and membership files (whole selected run)</summary><div class="table-scroll"><table><thead><tr><th>File</th><th>Role</th><th>SHA-256</th><th>Original bytes</th></tr></thead><tbody>${files.map(f=>`<tr><td>${escapeHTML(f.name)}</td><td>${escapeHTML(f.role)}</td><td class="hash mono">${f.sha256}</td><td>${evidenceLink(f.source,'Inspect')}</td></tr>`).join('')}</tbody></table></div></details>`)+panel('Persisted attacker policies',policies.length?`<details class="panel-body"><summary>${policies.length} filtered policy artifacts</summary><div class="table-scroll"><table><thead><tr><th>Detector / block</th><th>Policy</th><th>SHA-256</th><th>Original record</th></tr></thead><tbody>${policies.map(p=>`<tr><td>${label(p.detector)} / ${p.block}</td><td>${p.name}</td><td class="hash mono">${p.sha256}</td><td>${evidenceLink(p.source,'Inspect')}</td></tr>`).join('')}</tbody></table></div></details>`:'<div class="panel-body">Policy snapshots remain in the original campaign / manifest evidence; no legacy policy inventory is inferred.</div>');
}
function exportChart(){
 if(state.loading||!state.view){error('Wait for the selected evidence to load before exporting.');return;}
 const groups=state.view.groups, width=1100,height=110+groups.length*34;
 const text=x=>escapeHTML(x);
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="100%" height="100%" fill="#171b1d"/><g fill="#e5e7e3" font-family="sans-serif" font-size="12"><text x="20" y="24">${text(version())} / ${text(state.run)} / completion (%) / 0–100 scale</text>${[0,25,50,75,100].map(x=>`<text x="${400+x*5}" y="50">${x}%</text>`).join('')}${groups.map((g,i)=>`<text x="20" y="${80+i*34}">${text(label(g.detector)+' / '+label(g.strategy)+' / '+label(g.family))}</text><rect x="400" y="${67+i*34}" width="${g.completion*5}" height="14" fill="#83bca7"/><text x="915" y="${80+i*34}">${g.completion.toFixed(2)}% n=${g.campaigns}</text>`).join('')}</g></svg>`;
 const captioned=svg.replace('</g></svg>',`<text x="20" y="${height-12}">Synthetic environment, not real-world effectiveness. n = campaigns; block SD is available in the accompanying table.</text></g></svg>`);
 download(new Blob([captioned],{type:'image/svg+xml'}),'completion-comparison.svg');
}
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
async function poll(){
 if(pollBusy||!state.boot)return;pollBusy=true;
 try{
 const result=await api('/api/jobs');state.jobs=result.jobs;state.events=result.events;state.active=result.active;
 const activeJob=state.jobs.find(j=>j.id===result.active);
 $('#active-status').textContent=activeJob?`${activeJob.status}: ${activeJob.name}`:'No active job';
 const latestTest=state.jobs.find(j=>j.kind==='tests'&&j.status==='completed'&&j.counts);
 if(latestTest)$('#last-validation').textContent=`Last local validation: ${latestTest.counts.passed} passed`;
 if(latestTest)$('#last-validation').title='Completed '+latestTest.end;
 if(state.page==='terminal'&&state.job){
 const log=await api('/api/logs?job='+state.job+'&cursor='+state.logCursor);state.logCursor=log.cursor;state.logs.push(...log.lines);
 const el=$('#log-output');if(el&&log.lines.length){const follow=el.scrollHeight-el.scrollTop-el.clientHeight<90;el.innerHTML=logHTML();if(follow)el.scrollTop=el.scrollHeight;}
 const current=state.jobs.find(j=>j.id===state.job);
 if(current&&$('#job-status')){$('#job-status').textContent=current.status;$('#job-status').className='status '+current.status;$('#job-exit').textContent='Exit '+(current.exit_code??'—');$('#job-elapsed').textContent=fmt(current.status==='running'?(Date.now()-new Date(current.start))/1000:current.elapsed,1)+' s';$('#cancel-job').disabled=!state.active;}
 }
 for(const job of state.jobs){
 if(['completed','failed','cancelled','timed_out','interrupted'].includes(job.status)&&!state.finished.has(job.id)){
 state.finished.add(job.id);
 if(job.id===state.job&&job.status==='completed'&&['legacy','pilot'].includes(job.kind)){
 state.boot.runs=await api('/api/runs');state.run='run-'+job.name;state.filters={};$('#run-select').innerHTML=runOptions();await loadView(false);if(state.page==='results')await render();else nav('results');
 }else if(job.id===state.job&&job.status==='completed'&&['tests','verify'].includes(job.kind)){nav('validation');}
 }
 }
 if(state.page==='runner'&&$('#execute')){$('#execute').disabled=!state.preview||!!state.active;$('#duplicate-note').textContent=state.active?'A job is already active.':'';}
 }catch(e){error('Execution status unavailable: '+e.message);}finally{pollBusy=false;}
}
document.addEventListener('click',async event=>{
 const target=event.target.closest('button,a,[data-detail]');if(!target)return;
 if((state.loading&&(target.id==='export-chart'||target.matches('a[href^="/api/export?"]')))||target.getAttribute('aria-disabled')==='true'){
  event.preventDefault();error('Wait for the selected evidence to load before exporting.');return;
 }
 try{
 if(target.dataset.nav){nav(target.dataset.nav);return;}
 if(target.dataset.preset){applyPreset(target.dataset.preset);return;}
 if(target.dataset.sort){state.descending=state.sort===target.dataset.sort?!state.descending:false;state.sort=target.dataset.sort;await render();return;}
 if(target.dataset.detail!==undefined){explain(Number(target.dataset.detail));return;}
 if(target.dataset.campaign!==undefined){await campaign(Number(target.dataset.campaign));return;}
 if(target.dataset.job){state.job=target.dataset.job;state.logs=[];state.logCursor=0;nav('terminal');return;}
 switch(target.id){
 case 'menu':$('#rail').classList.toggle('open');target.setAttribute('aria-expanded',String($('#rail').classList.contains('open')));break;
 case 'run-short-top':nav('runner');break;
 case 'theme':case 'settings-theme':theme();break;
 case 'refresh':await loadView();break;
 case 'reset-filters':state.filters={};state.offset=0;await loadView();break;
 case 'close-detail':$('#detail-dialog').close();break;
 case 'inspect-group':{const g=state.view.groups[Number(target.dataset.group)];state.filters={detector:g.detector,strategy:g.strategy,family:g.family};state.offset=0;$('#detail-dialog').close();nav('campaigns');await loadView();break;}
 case 'next-campaigns':state.offset+=50;await render();break;
 case 'previous-campaigns':state.offset=Math.max(0,state.offset-50);await render();break;
 case 'copy-log':await navigator.clipboard.writeText(state.logs.map(l=>`${l.timestamp} [${l.channel}] ${l.text}`).join('\n'));target.textContent='Copied loaded log';break;
 case 'cancel-job':if(state.active)await api('/api/cancel',{job:state.active});break;
 case 'confirm-no':$('#confirm-dialog').close();break;
 case 'confirm-yes':$('#confirm-dialog').close();await startJob(true);break;
 case 'export-chart':exportChart();break;
 }
 }catch(e){error(e.message);}
});
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.matches('[data-detail]'))explain(Number(e.target.dataset.detail));if(e.key==='Escape'){$('#rail').classList.remove('open');$('#menu').setAttribute('aria-expanded','false');}});
document.addEventListener('change',async event=>{
 const t=event.target;
 if(t.dataset.filter){state.filters[t.dataset.filter]=t.value;state.offset=0;await loadView();}
 if(t.id==='run-select'){state.run=t.value;state.filters={};state.offset=0;await loadView();}
 if(t.id==='job-select'){state.job=t.value;state.logs=[];state.logCursor=0;await render();await poll();}
 if(t.closest('#experiment-form')){clearTimeout(previewTimer);preview();}
});
document.addEventListener('input',e=>{if(e.target.closest('#experiment-form')){clearTimeout(previewTimer);previewTimer=setTimeout(preview,180);}});
document.addEventListener('submit',async event=>{
 if(event.target.id!=='experiment-form')return;event.preventDefault();
 await preview();if(!state.preview||state.active)return;
 if(state.preview.expensive){$('#confirm-workload').textContent=$('#workload').textContent;$('#confirm-dialog').showModal();return;}
 await startJob();
});
window.addEventListener('hashchange',async()=>{
 const selected=location.hash.slice(1);state.page=pages.some(p=>p[0]===selected)?selected:'overview';
 $('#rail').classList.remove('open');$('#menu').setAttribute('aria-expanded','false');
 try{await render();if(state.pendingPreset&&state.page==='runner'){const preset=state.pendingPreset;state.pendingPreset=null;applyPreset(preset);}}catch(e){error(e.message);}
});
async function init(){
 try{
 state.boot=await api('/api/bootstrap');state.jobs=state.boot.jobs;
 state.jobs.forEach(j=>state.finished.add(j.id));
 state.run=state.boot.runs.find(r=>r.id==='pilot-main')?.id||state.boot.runs[0]?.id;
 $('#branch').textContent=state.boot.branch;$('#branch').title=state.boot.branch;
 $('#commit').textContent=state.boot.commit==='Unavailable'?'Unavailable':state.boot.commit.slice(0,9);$('#commit').title=state.boot.commit;
 $('#environment').textContent=`Python ${state.boot.environment.python} / ${state.boot.environment.status}`;
 const prior=state.boot.prior_tests.find(t=>t.name==='prior-regression.xml');
 $('#last-validation').textContent=prior?`Imported validation: ${prior.counts.passed} passed`:'Validation unavailable';
 if(prior)$('#last-validation').title='Recorded '+(prior.counts.timestamp||'Unavailable');
 $('#navigation').innerHTML=pages.map(([id,title,icon])=>`<a href="#${id}" data-page="${id}"><i data-lucide="${icon}"></i>${title}</a>`).join('');
 $('#run-select').innerHTML=runOptions();state.page=pages.some(p=>p[0]===location.hash.slice(1))?location.hash.slice(1):'overview';
 if(state.run)await loadView();else await render();
 await poll();setInterval(poll,1000);window.appReady=true;
 }catch(e){error('Cannot connect to the local backend: '+e.message);$('#page').innerHTML=empty('Backend unavailable','Start run_dashboard.py with the documented Python environment, then reload.');}
 icons();
}
init();
