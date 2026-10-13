param([string]$SdkHome,[string]$EnvironmentHome,[string]$NodeModulesPath)
$project=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (!$EnvironmentHome) {$EnvironmentHome=Join-Path $project '../atri-environment'}
if (!$SdkHome) {$SdkHome=Join-Path $project '../vela-environment/sdk'}
if (!$NodeModulesPath) {$NodeModulesPath=Join-Path $project '../starry-rw5/node_modules'}
$env:NODE_PATH=[IO.Path]::GetFullPath($NodeModulesPath)
$env:STARRY_EMULATOR_HOME=[IO.Path]::GetFullPath($EnvironmentHome)
$env:WATCH_SDK_HOME=[IO.Path]::GetFullPath($SdkHome)
$env:WATCH_VVD_NAME='AtriRW5-432x514'
$taskNode=(Get-Command node).Source
$taskEmu=Start-Process -FilePath $taskNode -ArgumentList 'tools/emulator-server.cjs' -WorkingDirectory $project -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $env:STARRY_EMULATOR_HOME 'controller-stdout.log') -RedirectStandardError (Join-Path $env:STARRY_EMULATOR_HOME 'controller-stderr.log')
$taskEmu.Id
