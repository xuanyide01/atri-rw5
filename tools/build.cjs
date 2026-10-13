// Keep the compiler version used by the supplied working physical-watch app.
const fs=require('fs'),path=require('path');
const watchConfig=path.resolve('src/config-watch.json');
if(!fs.existsSync(watchConfig))throw Error('src/config-watch.json is required to generate the watch manifest');
JSON.parse(fs.readFileSync(watchConfig,'utf8'));
const toolkit=process.env.WATCH_COMPAT_TOOLKIT||path.join(__dirname,'compat-toolkit/node_modules/aiot-toolkit');
if(!fs.existsSync(path.join(toolkit,'package.json')))throw Error('Install the compatible compiler: npm install --prefix tools/compat-toolkit --ignore-scripts');
if(JSON.parse(fs.readFileSync(path.join(toolkit,'package.json'),'utf8')).version!=='1.1.0')throw Error('Compatible compiler must be aiot-toolkit 1.1.0');
const {compile}=require(path.join(toolkit,'lib/commands/compile'));
// The resource plugin otherwise requantizes every PNG larger than 10KB and
// recompresses JPEGs. Our offline conversion already chooses colors and alpha.
// Disable that one stage in this process; do not modify the shared compiler.
const Module=require('module');
const resourcePath=require.resolve('@aiot-toolkit/packager/lib/plugins/resource-plugin',{paths:[toolkit]});
const resourceCode=fs.readFileSync(resourcePath,'utf8');
const needle='_fsExtra.default.statSync(s).size/1024>=10';
if(!resourceCode.includes(needle))throw Error('Unknown resource plugin; review image preservation hook');
const resourceModule=new Module(resourcePath,module);resourceModule.filename=resourcePath;resourceModule.paths=Module._nodeModulePaths(path.dirname(resourcePath));
require.cache[resourcePath]=resourceModule;resourceModule._compile(resourceCode.replace(needle,'false'),resourcePath);
(async()=>{
 const result=await compile('native',process.argv.includes('--development')?'dev':'prod',false,{signMode:'BUILD'});
 if(result.compileError||result.stats.hasErrors())throw Error('Compatible compiler failed');
 const watchManifest=path.resolve('build/manifest-watch.json');
 if(!fs.existsSync(watchManifest)||JSON.parse(fs.readFileSync(watchManifest,'utf8')).package!=='com.codex.atri.rw5')throw Error('Watch-specific manifest was not generated correctly');
 const manifest=JSON.parse(fs.readFileSync('src/manifest.json','utf8'));
 const name=manifest.package+'.debug.'+manifest.versionName+'.rpk',file=path.join('dist',name);
 if(!fs.existsSync(file))throw Error('Current-version package was not produced');
 // Use the release wrapping that resolved the earlier Summer Pockets install issue.
 const packaging=await require('./repack-rpk.cjs').repackRpk(file,file,toolkit);
 console.log('R1_PACKAGING',JSON.stringify(packaging));
 const bytes=fs.statSync(file).size;if(bytes>15000000)throw Error('Package exceeds the 15,000,000-byte cap: '+bytes);
 console.log('BUILD_OUTPUT',name,bytes);
})().catch(e=>{console.error(e);process.exitCode=1;});
