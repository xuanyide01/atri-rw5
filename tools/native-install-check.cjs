// Focused validation for an installation/font-only change. No injected game state.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),version=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8')).versionName,out=path.join(root,'native-test-results/v'+version.replace(/\./g,''));
const base='http://127.0.0.1:43131',log=path.resolve(root,'../atri-environment/emulator.log'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
const logs=()=>fs.readFileSync(log,'utf8'),sha=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk'))).digest('hex');
async function request(endpoint){const r=await fetch(base+endpoint);assert(r.ok,await r.clone().text());return r;}
async function click(x,y,re){const at=logs().length;await request('/click?x='+x+'&y='+y);await sleep(650);if(!re)return;for(let i=0;i<100;i++){const s=logs().slice(at);if(re.test(s))return s;await sleep(200);}throw Error('Timeout '+re);}
async function shot(name){await sleep(650);fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await request('/screen')).arrayBuffer()));}
async function slot30(re){for(let i=0;i<7;i++)await click(360,477);return click(216,215,re);}
async function title(){await click(216,477,/ATRI_RW5 menu/);await sleep(250);await click(216,443,/ATRI_RW5 title ready/);}
async function confirmY(){
 const {createRequire}=require('module'),sharp=createRequire(path.resolve(root,'../legacy-toolkit/node_modules/aiot-toolkit/package.json'))('sharp');
 const {data,info}=await sharp(Buffer.from(await(await request('/screen')).arrayBuffer())).ensureAlpha().raw().toBuffer({resolveWithObject:true});let first=-1,ranges=[];
 // Probe the empty right side; left-aligned labels intersect a probe at x=60.
 for(let y=65;y<490;y++){const at=(y*info.width+380)*info.channels,match=Math.abs(data[at]-223)<10&&Math.abs(data[at+1]-237)<10&&Math.abs(data[at+2]-246)<10;if(match&&first<0)first=y;if(!match&&first>=0){if(y-first>25)ranges.push([first,y]);first=-1;}}
 assert.equal(ranges.length,2);return Math.round((ranges[0][0]+ranges[0][1])/2);
}
(async()=>{
 const installed=JSON.parse(fs.readFileSync(path.join(root,'reports/installed-script-check.json'),'utf8'));assert(installed.installedScriptMatchesPackage&&installed.packageSha256===sha);
 const begin=logs().length,boot=Math.max(0,logs().lastIndexOf('NuttShell (NSH)'));
 for(let i=0;i<240;i++){if(/Page show page_info:name:pages\/index/.test(logs().slice(boot)))break;if(i===239)throw Error('Cold boot page not ready');await sleep(250);}
 await sleep(2000);await shot('install-title');
 if(process.argv.includes('--prepare')){
  await click(216,323,/ATRI_RW5 frame b999:\*start 0/);await click(180,395,/ATRI_RW5 frame b999:\*start 1/);
  await click(216,477,/ATRI_RW5 menu/);await click(216,95,/ATRI_RW5 slots ready save/);
  let saved=await slot30(/ATRI_RW5 (?:slot saved|overwrite) 30(?:\s|$)/);if(saved.includes('ATRI_RW5 overwrite'))saved=await click(216,await confirmY(),/ATRI_RW5 slot saved 30 /);
  const position=saved.match(/ATRI_RW5 slot saved 30 (\S+) (\d+)/).slice(1);await title();
  fs.writeFileSync(path.join(out,'install-save-preparation.json'),JSON.stringify({packageSha256:sha,slot:30,position},null,2));console.log('INSTALL_SAVE_PREPARED',JSON.stringify(position));
 }else{
  const prepared=JSON.parse(fs.readFileSync(path.join(out,'install-save-preparation.json'),'utf8'));assert.equal(prepared.packageSha256,sha);
  const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  await click(216,369,/ATRI_RW5 slots ready load/);await shot('load-page-one');
  await slot30(new RegExp('ATRI_RW5 slot loaded 30 '+prepared.position.map(escape).join(' ')+'(?:\\s|$)'));await shot('cold-loaded-dialogue');
  await click(370,477,/ATRI_RW5 frame b999:\*start 2/);await title();
  await click(216,415);await sleep(600);await shot('font-gallery-list');await click(100,160,/ATRI_RW5 cg 0 0/);await click(216,200,/ATRI_RW5 cg 0 1/);await shot('install-cg-variant');await click(216,487);await click(216,477,/ATRI_RW5 title ready/);
  assert(!/ATRI_RW5 error|ATRI_RW5 image failed|ASSERTION FAILED|PANIC!!!/.test(logs().slice(begin)));
  const result={passed:true,packageSha256:sha,physicalDeviceTested:false,runtime:'official Vela Watch 5 SDK emulator, not physical REDMI Watch 5 firmware',freshInstallVerified:true,coldBootSlot30Restored:true,dialogueTapAndAdvance:true,pagedSaveAndLoad:true,galleryVariantCycle:true,all30SlotsRetested:false,scope:'Font-only revision: focused fresh install, cold start, actual UI save/load and CJK rendering; full route/save baseline retained under its original hash.'};
  fs.writeFileSync(path.join(out,'installation-report.json'),JSON.stringify(result,null,2));console.log('INSTALLATION_CHECK_PASS',JSON.stringify(result));
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
