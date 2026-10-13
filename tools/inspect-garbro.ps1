$ErrorActionPreference='Stop'
$toolRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../atri-tools/GARbro'))
Set-Location -LiteralPath $toolRoot
[Reflection.Assembly]::LoadFrom((Join-Path $toolRoot 'GameRes.dll')) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $toolRoot 'ArcFormats.dll')) | Out-Null
Add-Type -TypeDefinition @'
using System;using System.Reflection;using System.IO;
public class ResolveGarbro { public static string Root; public static void Init(string root) { Root=root; AppDomain.CurrentDomain.AssemblyResolve+=(sender,args)=> {var n=new AssemblyName(args.Name).Name; foreach(var a in AppDomain.CurrentDomain.GetAssemblies()) if(a.GetName().Name==n)return a;var p=Path.Combine(Root,n+".dll");return File.Exists(p)?Assembly.LoadFrom(p):null;}; } }
'@
[ResolveGarbro]::Init($toolRoot)
$catalog=[GameRes.FormatCatalog]::Instance
$db=[IO.Path]::GetFullPath((Join-Path $toolRoot '../GARbro-Mod/GARbro-Mod-master/ArcFormats/Resources/Formats.dat'))
$stream=[IO.File]::OpenRead($db)
try{$catalog.DeserializeScheme($stream)}finally{$stream.Dispose()}
[GameRes.Formats.KiriKiri.Xp3Opener]::KnownSchemes.GetEnumerator() | Where-Object {$_.Key -match 'ATRI|Dear'} | ForEach-Object {Write-Output ($_.Key+' '+$_.Value.GetType().FullName)}
