// Focused auto-reading checks through actual emulator UI; no scene injection.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),version=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8')).versionName,out=path.join(root,'native-test-results/v'+version.replace(/\./g,''));
const base='http://127.0.0.1:43131',log=path.resolve(root,'../atri-environment/emulator.log'),sleep=ms=>new Promise(r=>setTimeout(r,ms)),logs=()=>fs.readFileSync(log,'utf8');
const {createRequire}=require('module'),sharp=createRequire(path.resolve(root,'../legacy-toolkit/node_modules/aiot-toolkit/package.json'))('sharp');
async function request(url){const r=await fetch(base+url);assert(r.ok,await r.clone().text());return r;}
async function wait(re,at,ms=20000){for(let i=0;i<ms/100;i++){const s=logs().slice(at);if(re.test(s))return s;await sleep(100);}throw Error('Timeout '+re);}
async function click(x,y,re){const at=logs().length;await request('/click?x='+x+'&y='+y);await sleep(250);return re?wait(re,at):logs().slice(at);}
async function shot(name){await sleep(350);fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await request('/screen')).arrayBuffer()));}
async function stable(ms){const at=logs().length;await sleep(ms);assert(!/ATRI_RW5 (?:auto advance|frame|choice)/.test(logs().slice(at)),'Story moved during a pause');}
async function crop(name,top){return sharp(path.join(out,name+'.png')).extract({left:40,top,width:350,height:38}).raw().toBuffer();}
(async()=>{
 fs.mkdirSync(out,{recursive:true});const raw=fs.readFileSync(path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk')),sha=crypto.createHash('sha256').update(raw).digest('hex');
 const installed=JSON.parse(fs.readFileSync(path.join(root,'reports/installed-script-check.json'),'utf8'));assert(installed.installedScriptMatchesPackage&&installed.packageSha256===sha);
 const begin=logs().length,boot=Math.max(0,logs().lastIndexOf('NuttShell (NSH)'));await wait(/Page show page_info:name:pages\/index/,boot);await sleep(1000);await shot('auto-title');
 await click(216,369,/ATRI_RW5 slots ready load/);await click(216,123,/ATRI_RW5 slot loaded 1 b999:\*start 2/);
 await click(216,477,/ATRI_RW5 menu/);await shot('auto-menu-default');
 await click(216,228,/ATRI_RW5 auto enabled true/);
 for(const speed of [2,0,1])await click(216,274,new RegExp('ATRI_RW5 auto speed '+speed));await shot('auto-menu-enabled');
 await stable(2200);const at=logs().length,start=Date.now();await click(216,412);
 await wait(/ATRI_RW5 auto advance b999:\*start 2/,at);await wait(/ATRI_RW5 frame b999:\*start 3/,at);const firstAutoAdvanceMs=Date.now()-start;
 await click(216,477,/ATRI_RW5 menu/);await stable(2500);
 await click(216,90,/ATRI_RW5 slots ready save/);await stable(2500);await shot('auto-save-paused');await click(216,477);
 await click(216,477,/ATRI_RW5 menu/);await click(216,136,/ATRI_RW5 slots ready load/);await stable(2500);await click(216,477);
 await click(216,477,/ATRI_RW5 menu/);await click(216,228,/ATRI_RW5 auto enabled false/);
 let choice=false;
 for(let i=0;i<8;i++){
   const s=await click(216,182,/ATRI_RW5 (?:frame|choice)/);
   if(s.includes('ATRI_RW5 choice')){choice=true;break;}
   await click(216,477,/ATRI_RW5 menu/);
 }
 assert(choice,'No real choice reached');await shot('auto-choice');
 await click(216,477,/ATRI_RW5 menu/);await click(216,228,/ATRI_RW5 auto enabled true/);await click(216,412);await stable(4500);
 const picked=logs().length;await click(216,83,/ATRI_RW5 frame/);await wait(/ATRI_RW5 auto advance/,picked);await shot('auto-after-choice');
 await click(50,477,/ATRI_RW5 frame/);await stable(2500);await click(216,477,/ATRI_RW5 menu/);await shot('auto-menu-previous-off');
 assert((await crop('auto-menu-default',208)).equals(await crop('auto-menu-previous-off',208)),'Previous did not display the off label');
 await click(216,274,/ATRI_RW5 auto speed 2/);await shot('auto-menu-fast');await click(216,458,/ATRI_RW5 title ready/);
 await click(216,461,/ATRI_RW5 exit requested/);await sleep(2000);const restarted=logs().length;await request('/start');await wait(/ATRI_RW5 title ready/,restarted);await sleep(1000);
 await click(216,323,/ATRI_RW5 frame b999:\*start 0/);await click(216,477,/ATRI_RW5 menu/);await shot('auto-menu-restarted');
 assert((await crop('auto-menu-default',208)).equals(await crop('auto-menu-restarted',208)),'Auto not off after restart');
 assert((await crop('auto-menu-fast',254)).equals(await crop('auto-menu-restarted',254)),'Speed preference was not preserved');
 await click(216,458,/ATRI_RW5 title ready/);
 assert(!/ATRI_RW5 error|ATRI_RW5 image failed|ASSERTION FAILED|PANIC!!!/.test(logs().slice(begin)));
 const report={passed:true,packageSha256:sha,realUIClicks:true,sceneInjection:false,legacySlot1Restored:true,automaticAdvanceAfterResume:true,firstAutoAdvanceMs,threeSpeedMenuCycle:true,menuPause:true,saveAndLoadPause:true,choiceNeverAutoSelected:true,resumesAfterManualChoice:true,previousDisablesAuto:true,autoOffAfterRestart:true,speedPersistsAfterRestart:true,physicalDeviceTested:false};
 fs.writeFileSync(path.join(out,'auto-reader-report.json'),JSON.stringify(report,null,2));console.log('NATIVE_AUTO_READER_PASS',JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;});
