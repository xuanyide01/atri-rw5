const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'native-test-results/v011'),base='http://127.0.0.1:43131',log=path.resolve(root,'../atri-environment/emulator.log'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
const logs=()=>fs.readFileSync(log,'utf8');
async function request(e){const r=await fetch(base+e);assert(r.ok,await r.clone().text());return r;}
async function wait(at,re){for(let i=0;i<100;i++){if(re.test(logs().slice(at)))return;await sleep(200);}throw Error('Timeout '+re);}
async function click(x,y,re){const at=logs().length;await request('/click?x='+x+'&y='+y);await sleep(700);await wait(at,re);}
async function shot(name){fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await request('/screen')).arrayBuffer()));}
(async()=>{
 const delta=JSON.parse(fs.readFileSync(path.join(root,'reports/final-title-revision.json'),'utf8')),installed=JSON.parse(fs.readFileSync(path.join(root,'reports/installed-script-check.json'),'utf8'));assert(delta.passed&&installed.installedScriptMatchesPackage&&installed.packageSha256===delta.packageSha256);
 await wait(Math.max(0,logs().lastIndexOf('NuttShell (NSH)')),/ATRI_RW5 title ready/);await sleep(1800);await shot('title-final');
 await click(216,323,/ATRI_RW5 frame b999:\*start 0/);await click(180,395,/ATRI_RW5 frame b999:\*start 1/);await click(216,477,/ATRI_RW5 menu/);await click(216,443,/ATRI_RW5 title ready/);
 const at=logs().length;await click(216,461,/ATRI_RW5 exit requested/);await wait(at,/ATRI_RW5 destroyed/);await sleep(2000);const restart=logs().length;await request('/start');await wait(restart,/ATRI_RW5 title ready/);await sleep(1600);await shot('title-final');
 const report={passed:true,packageSha256:delta.packageSha256,baselinePackageSha256:delta.baselinePackageSha256,finalTitleTested:true,startAndDialogueTapTested:true,exitDestroyedPage:true,restartSucceeded:true};fs.writeFileSync(path.join(out,'final-title-report.json'),JSON.stringify(report,null,2));console.log('FINAL_TITLE_PASS',JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;});
