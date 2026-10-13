$ErrorActionPreference='Stop'
$base=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../'))
$tools=Join-Path $base 'atri-tools/GARbro'
[Reflection.Assembly]::LoadFrom((Join-Path $tools 'GameRes.dll')) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $tools 'ArcFormats.dll')) | Out-Null
$v=Get-Content -LiteralPath (Join-Path $base 'atri-tools/atri-cx-scheme.json') -Raw | ConvertFrom-Json
$s=New-Object GameRes.Formats.KiriKiri.CxScheme
$s.Mask=$v.m_mask;$s.Offset=$v.m_offset;$s.PrologOrder=[byte[]]$v.PrologOrder
$s.OddBranchOrder=[byte[]]$v.OddBranchOrder;$s.EvenBranchOrder=[byte[]]$v.EvenBranchOrder;$s.ControlBlock=[uint32[]]$v.ControlBlock
$c=New-Object GameRes.Formats.KiriKiri.CxEncryption($s)
foreach($archive in @('bgimage','fgimage','data')){
 $entries=Get-Content -LiteralPath (Join-Path $base ('atri-probe/'+$archive+'.xp3.index.json')) -Raw | ConvertFrom-Json
 foreach($entry in $entries[1..4]){
  $p=Join-Path $base ('atri-probe/'+$archive+'-'+$entry.name+'.raw')
  if(!(Test-Path -LiteralPath $p)){continue}
  [byte[]]$b=[IO.File]::ReadAllBytes($p)
  $e=New-Object GameRes.Formats.KiriKiri.Xp3Entry;$e.Hash=[uint32]$entry.adler
  if($entry.name -ne 'startup.tjs'){$c.Decrypt($e,0,$b,0,$b.Length)}
  [IO.File]::WriteAllBytes(($p+'.decoded'),$b)
  Write-Output ($archive+' '+$entry.name+' '+[BitConverter]::ToString($b[0..15]))
 }
}
