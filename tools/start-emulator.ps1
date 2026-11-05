param([string]$SdkHome,[string]$EnvironmentHome)
$taskProject=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (!$EnvironmentHome) {$EnvironmentHome=[IO.Path]::GetFullPath((Join-Path $taskProject '../开发记录/模拟器环境'))}
if (!$SdkHome) {$SdkHome=Join-Path $EnvironmentHome 'sdk'}
$env:NODE_PATH=Join-Path $taskProject 'tools/emulator-toolkit/node_modules'
$env:STARRY_EMULATOR_HOME=$EnvironmentHome
$env:WATCH_SDK_HOME=$SdkHome
$env:WATCH_VVD_NAME='AtriBand8Pro-336x480'
$taskNode=(Get-Command node).Source
$taskEmu=Start-Process -FilePath $taskNode -ArgumentList 'tools/emulator-server.cjs' -WorkingDirectory $taskProject -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $EnvironmentHome 'controller-stdout.log') -RedirectStandardError (Join-Path $EnvironmentHome 'controller-stderr.log')
$taskEmu.Id

