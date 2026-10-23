$ErrorActionPreference = 'Continue'
$rootTask = Split-Path -Parent $PSScriptRoot
$outTask = Join-Path $rootTask 'artifacts/week1/environment'
New-Item -ItemType Directory -Force -Path $outTask | Out-Null
$logTask = Join-Path $outTask 'environment.log'
Start-Transcript -Path $logTask -Force
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture
Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,AdapterRAM
foreach ($nameTask in @('python','py','git','cmake','ninja','java','javac','adb','nvcc','nvidia-smi','wsl','gradle')) {
  $cmdTask = Get-Command $nameTask -ErrorAction SilentlyContinue
  if ($cmdTask) { Write-Output "$nameTask : $($cmdTask.Source)" } else { Write-Output "$nameTask : NOT_ON_PATH" }
}
foreach ($pairTask in @(@('python','--version'),@('py','--list'),@('git','--version'),@('cmake','--version'),@('ninja','--version'),@('java','-version'),@('nvcc','--version'),@('nvidia-smi',''),@('adb','devices'))) {
  if (Get-Command $pairTask[0] -ErrorAction SilentlyContinue) { if ($pairTask[1]) { & $pairTask[0] $pairTask[1] } else { & $pairTask[0] } }
}
$sdkTask = Join-Path $env:LOCALAPPDATA 'Android/Sdk'
Write-Output "ANDROID_HOME=$env:ANDROID_HOME ANDROID_SDK_ROOT=$env:ANDROID_SDK_ROOT JAVA_HOME=$env:JAVA_HOME"
foreach ($pathTask in @($sdkTask, 'C:/Program Files/Android/Android Studio','C:/Program Files/Java','C:/Program Files/Microsoft','C:/Program Files/Microsoft Visual Studio/2022')) {
  if (Test-Path -LiteralPath $pathTask) { Get-ChildItem -LiteralPath $pathTask | Select-Object FullName } else { Write-Output "NOT_FOUND: $pathTask" }
}
$adbTask = Join-Path $sdkTask 'platform-tools/adb.exe'
if (Test-Path -LiteralPath $adbTask) { & $adbTask devices -l }
if (Test-Path -LiteralPath $sdkTask) { Get-ChildItem -LiteralPath $sdkTask -Filter source.properties -Recurse | ForEach-Object { Write-Output $_.FullName; Get-Content -LiteralPath $_.FullName } }
Stop-Transcript
