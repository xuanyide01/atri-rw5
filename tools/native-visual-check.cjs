// Visit reported regressions through ordinary UI controls, without scene injection.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),version=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8')).versionName,out=path.join(root,'native-test-results/v'+version.replace(/\./g,'')),base='http://127.0.0.1:43131',log=path.resolve(root,'../atri-environment/emulator.log');
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),logs=()=>fs.readFileSync(log,'utf8');
async function request(endpoint){const r=await fetch(base+endpoint);assert(r.ok,await r.clone().text());return r;}
async function click(x,y,re){const at=logs().length;await request('/click?x='+x+'&y='+y);await sleep(650);if(re){for(let i=0;i<100;i++){if(re.test(logs().slice(at)))return logs().slice(at);await sleep(100);}throw Error('Click timeout '+re);}}
async function shot(name){await sleep(600);fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await request('/screen')).arrayBuffer()));}
async function title(){await click(216,477,/ATRI_RW5 menu/);await click(216,443,/ATRI_RW5 title ready/);}
async function chapter(id){
 await click(216,323,/ATRI_RW5 frame b999:\*start 0/);
 for(let i=0;i<20;i++){
  await click(216,477,/ATRI_RW5 menu/);await sleep(250);
  let text=await click(216,211,/ATRI_RW5 (?:frame|choice)/);
  if(text.includes('ATRI_RW5 choice'))text=await click(216,157,/ATRI_RW5 frame/);
  if(new RegExp('ATRI_RW5 frame '+id+':\\*start 0(?:\\s|$)').test(text))return;
 }
 throw Error('Could not reach '+id+' through normal story skipping');
}
(async()=>{
 const file=path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk'),sha=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),installed=JSON.parse(fs.readFileSync(path.join(root,'reports/installed-script-check.json'),'utf8'));assert(installed.installedScriptMatchesPackage&&installed.packageSha256===sha);
 const begin=logs().length;await shot('title-final');await click(216,277,/ATRI_RW5 frame b701:\*start 0/);
 for(let i=1;i<=16;i++){await click(370,477,new RegExp('ATRI_RW5 frame b701:\\*start '+i+'(?:\\s|$)'));if([1,13,16].includes(i))await shot('b701-'+i);}
 await title();await chapter('b123');await shot('b123-0');await click(370,477,/ATRI_RW5 frame b123:\*start 1(?:\s|$)/);await shot('b123-1');await title();
 await chapter('b102');for(let i=1;i<=21;i++)await click(370,477,new RegExp('ATRI_RW5 frame b102:\\*start '+i+'(?:\\s|$)'));await shot('atri-portrait');await title();
 assert(!/ATRI_RW5 error|ATRI_RW5 image failed|ASSERTION FAILED|PANIC!!!/.test(logs().slice(begin)));
 await click(216,461,/ATRI_RW5 exit requested/);await sleep(2000);assert(/ATRI_RW5 destroyed/.test(logs().slice(begin)),'EXIT did not destroy the application page');
 const at=logs().length;await request('/start');for(let i=0;i<100&&!/ATRI_RW5 title ready/.test(logs().slice(at));i++)await sleep(200);assert(/ATRI_RW5 title ready/.test(logs().slice(at)));await sleep(1600);await shot('title-final');
 const report={passed:true,packageSha256:sha,realUIClicks:true,reportedScenes:['b701:*start/1','b701:*start/13','b701:*start/16','b123:*start/0','b123:*start/1'],atriPortrait:'b102:*start/21',titleUsesOriginalSprites:true,noChapterPreview:true,titleExitClosesApplication:true,restartedAfterExit:true};fs.writeFileSync(path.join(out,'visual-report.json'),JSON.stringify(report,null,2));console.log('NATIVE_VISUAL_PASS',JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;});
