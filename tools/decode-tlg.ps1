param([string]$InputRoot='', [string]$OutputRoot='')
$ErrorActionPreference='Stop'
$base=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../'))
if (!$InputRoot) {$InputRoot=Join-Path $base 'atri-probe/extracted/fgimage'}
if (!$OutputRoot) {$OutputRoot=Join-Path $base 'atri-probe/layers'}
$InputRoot=[IO.Path]::GetFullPath($InputRoot)
$OutputRoot=[IO.Path]::GetFullPath($OutputRoot)
$dll=Join-Path $base 'atri-tools/GARbro'
Add-Type -AssemblyName PresentationCore,WindowsBase
[Reflection.Assembly]::LoadFrom((Join-Path $dll 'GameRes.dll')) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $dll 'ArcFormats.dll')) | Out-Null
$format=New-Object GameRes.Formats.KiriKiri.TlgFormat
$report=New-Object System.Collections.Generic.List[object]
foreach($file in Get-ChildItem -LiteralPath $InputRoot -Recurse -Filter '*.tlg') {
  # The smallest original portrait set preserves all expression layers.
  if ($file.BaseName -notmatch '_s_\d+$') {continue}
  $relative=$file.FullName.Substring($InputRoot.Length).TrimStart('\','/')
  $destination=Join-Path $OutputRoot ([IO.Path]::ChangeExtension($relative,'.png'))
  [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
  $stream=[GameRes.BinaryStream]::FromFile($file.FullName)
  try {
    $meta=$format.ReadMetaData($stream)
    if (!$meta) {throw "Unsupported TLG: $relative"}
    $stream.Position=0
    $decoded=$format.Read($stream,$meta)
    $encoder=New-Object System.Windows.Media.Imaging.PngBitmapEncoder
    $encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($decoded.Bitmap))
    $output=[IO.File]::Create($destination)
    try {$encoder.Save($output)} finally {$output.Dispose()}
    $report.Add(@{file=$relative;width=$meta.Width;height=$meta.Height})
  } finally {$stream.Dispose()}
}
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputRoot 'decode-report.json') -Encoding UTF8
Write-Output "Decoded $($report.Count) portrait layers."
