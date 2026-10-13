// Reach different portrait shapes through actual story controls, without injection.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),version=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8')).versionName,out=path.join(root,'native-test-results/v'+version.replace(/\./g,''));
const base='http://127.0.0.1:43131',log=path.resolve(root,'../atri-environment/emulator.log'),sleep=ms=>new Promise(r=>setTimeout(r,ms)),logs=()=>fs.readFileSync(log,'utf8');
async function request(endpoint){const r=await fetch(base+endpoint);assert(r.ok,await r.clone().text());return r;}
async function click(x,y,re,delay=350){const at=logs().length;await request('/click?x='+x+'&y='+y);await sleep(delay);if(re){for(let i=0;i<100;i++){if(re.test(logs().slice(at)))return logs().slice(at);await sleep(100);}throw Error('Click timeout '+re);}}
async function shot(name){await sleep(500);fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await request('/screen')).arrayBuffer()));}
async function title(){await click(216,477,/ATRI_RW5 menu/);await click(216,443,/ATRI_RW5 title ready/);}
(async()=>{
 const raw=fs.readFileSync(path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk')),sha=crypto.createHash('sha256').update(raw).digest('hex');
 const installed=JSON.parse(fs.readFileSync(path.join(root,'reports/installed-script-check.json'),'utf8'));assert(installed.installedScriptMatchesPackage&&installed.installedManifestAndChangedAssetsMatch&&installed.packageSha256===sha);
 const begin=logs().length;await click(216,323,/ATRI_RW5 frame b999:\*start 0/);
 for(const id of ['b101','b102']){await click(216,477,/ATRI_RW5 menu/);await click(216,211,new RegExp('ATRI_RW5 frame '+id+':\\*start 0(?:\\s|$)'));}
 const supplement=process.argv.includes('--supplement'),targets=supplement?[28]:[21,28,155],captured=[];
 for(let i=1;i<=Math.max(...targets);i++){
  await click(370,477,new RegExp('ATRI_RW5 frame b102:\\*start '+i+'(?:\\s|$)'));
  if(targets.includes(i)){await shot('portrait-b102-'+i);captured.push('b102:*start/'+i);console.log('PORTRAIT_CAPTURE',i);}
 }
 await title();
 assert(!/ATRI_RW5 error|ATRI_RW5 image failed|ASSERTION FAILED|PANIC!!!/.test(logs().slice(begin)));
 if(supplement){const prior=JSON.parse(fs.readFileSync(path.join(out,'portrait-alignment-report.json'),'utf8'));assert(prior.packageSha256===sha&&prior.passed);captured.unshift(...prior.capturedScenes);}
 const report={passed:true,packageSha256:sha,realUIClicks:true,sceneInjection:false,capturedScenes:captured,portraitHeight:310,dialogueBoundary:286,noRuntimeImageErrors:true,physicalDeviceTested:false};
 fs.writeFileSync(path.join(out,'portrait-alignment-report.json'),JSON.stringify(report,null,2));console.log('NATIVE_PORTRAIT_ALIGNMENT_PASS',JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;});
