// Deterministic source crop for the user's requested title-background cover.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{createRequire}=require('module');
const root=path.resolve(__dirname,'..'),source=path.resolve(root,'../atri-probe/extracted/data/image/title_base2.png');
const toolkit=process.env.WATCH_COMPAT_TOOLKIT||path.resolve(root,'../legacy-toolkit/node_modules/aiot-toolkit');
const sharp=createRequire(path.join(toolkit,'package.json'))('sharp');
(async()=>{
 const crop={left:480,top:0,width:720,height:720};
 const mask=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192"><circle cx="96" cy="96" r="95" fill="white"/></svg>');
 const image=await sharp(source).extract(crop).resize(192,192,{kernel:'lanczos3'}).ensureAlpha().composite([{input:mask,blend:'dest-in'}]).png({compressionLevel:9}).toBuffer();
 const asset=path.join(__dirname,'assets/atri-title-icon.png');fs.mkdirSync(path.dirname(asset),{recursive:true});fs.writeFileSync(asset,image);fs.writeFileSync(path.join(root,'src/common/logo.png'),image);
 const report={source:'original post-clear title_base2.png',sourceSha256:crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),crop,focus:'Atri face and upper shoulders with the original ocean/sky',size:[192,192],circularTransparentCorners:true,repainted:false,method:'Original pixels cropped, Lanczos downsampled and circular alpha masked using the existing Sharp asset runtime. No generated artwork used.',imagegenAttempt:'Stopped after prolonged lack of a returned result; not used as a project asset.',iconBytes:image.length,iconSha256:crypto.createHash('sha256').update(image).digest('hex')};
 fs.writeFileSync(path.join(root,'reports/title-icon.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;});
