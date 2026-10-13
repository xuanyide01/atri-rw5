const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),version=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8')).versionName,out=path.join(root,'native-test-results/v'+version.replace(/\./g,'')),base='http://127.0.0.1:43131',log=path.resolve(root,'../atri-environment/emulator.log');
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),logs=()=>fs.readFileSync(log,'utf8');
async function request(url){const r=await fetch(base+url);assert(r.ok,await r.clone().text());return r;}
async function click(x,y,pattern){const at=logs().length;await request('/click?x='+x+'&y='+y);await sleep(600);if(pattern){for(let i=0;i<100;i++){if(pattern.test(logs().slice(at)))return;await sleep(100);}throw Error('Click timeout '+pattern);}}
async function shot(name){await sleep(700);fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await request('/screen')).arrayBuffer()));}
(async()=>{
  const installed=JSON.parse(fs.readFileSync(path.join(root,'reports/installed-script-check.json'),'utf8'));assert(installed.installedScriptMatchesPackage);assert.equal(installed.packageSha256,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk'))).digest('hex'));
  const boot=Math.max(0,logs().lastIndexOf('NuttShell (NSH)'));for(let i=0;i<240;i++){if(/Page show page_info:name:pages\/index/.test(logs().slice(boot)))break;if(i===239)throw Error('Page did not become ready');await sleep(200);}await sleep(1800);
  await click(216,323,/ATRI_RW5 frame b999:\*start 0/);await click(180,395,/ATRI_RW5 frame b999:\*start 1/);
  await click(216,477,/ATRI_RW5 menu/);await click(216,211,/ATRI_RW5 frame b101:\*start 0/);
  for(let i=1;i<=28;i++)await click(370,477,new RegExp('ATRI_RW5 frame b101:\\*start '+i+'(?:\\s|$)'));await shot('long-text-before');
  const at=logs().length;await request('/drag?x0=300&y0=440&x1=300&y1=350');await sleep(600);assert(!/ATRI_RW5 frame/.test(logs().slice(at)),'Dragging advanced dialogue');await shot('long-text-scrolled');assert(!fs.readFileSync(path.join(out,'long-text-before.png')).equals(fs.readFileSync(path.join(out,'long-text-scrolled.png'))),'Long text did not scroll');
  await click(216,477,/ATRI_RW5 menu/);await click(216,327);await click(216,385);await shot('large-font');
  await click(216,477,/ATRI_RW5 menu/);await click(216,327);await click(216,385);
  for(let i=29;i<=32;i++)await click(370,477,new RegExp('ATRI_RW5 frame b101:\\*start '+i+'(?:\\s|$)'));
  await shot('portrait-face');await click(216,477,/ATRI_RW5 menu/);await click(216,443,/ATRI_RW5 title ready/);
  const extra={passed:true,packageSha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk'))).digest('hex'),dialogueDragDoesNotAdvance:true,dialogueScrollChangesVisibleContent:true,largeFontChecked:true,nonAtriPortraitRemovedScreenshot:'portrait-face.png'};fs.writeFileSync(path.join(out,'extra-report.json'),JSON.stringify(extra,null,2));console.log('NATIVE_EXTRA_PASS',JSON.stringify(extra));
})().catch(e=>{console.error(e);process.exitCode=1;});
