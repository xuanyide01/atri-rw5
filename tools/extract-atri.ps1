param([string]$Mode='scripts')
$ErrorActionPreference='Stop'
$base=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../'))
$tools=Join-Path $base 'atri-tools/GARbro'
[Reflection.Assembly]::LoadFrom((Join-Path $tools 'GameRes.dll')) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $tools 'ArcFormats.dll')) | Out-Null
Add-Type -Path (Join-Path $PSScriptRoot 'extract-atri.cs') -ReferencedAssemblies @((Join-Path $tools 'GameRes.dll'),(Join-Path $tools 'ArcFormats.dll'),'System.Core','System.Web.Extensions','System.IO.Compression')
[ExtractAtri]::Run('G:/SteamLibrary/steamapps/common/ATRI -My Dear Moments-',(Join-Path $base 'atri-probe/extraction-manifest.json'),(Join-Path $base 'atri-tools/atri-cx-scheme.json'),(Join-Path $base 'atri-probe/extracted'),$Mode)
