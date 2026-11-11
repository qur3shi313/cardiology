$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$episode = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $PSScriptRoot 'scenes.json') | ConvertFrom-Json
$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer
$audioDir = Join-Path $PSScriptRoot 'audio'
New-Item -ItemType Directory -Force -Path $audioDir | Out-Null
try {
    $voice.SelectVoice('Microsoft David Desktop')
    $voice.Rate = -2
    $voice.Volume = 100
    foreach ($route in @('radial', 'femoral')) {
        for ($index = 0; $index -lt $episode.$route.Count; $index++) {
            $scene = $episode.$route[$index]
            if (-not $scene.voice) { continue }
            $name = '{0}-{1:D2}.wav' -f $route, $index
            $voice.SetOutputToWaveFile((Join-Path $audioDir $name))
            $voice.Speak($scene.voice)
            $voice.SetOutputToNull()
        }
    }
} finally {
    $voice.Dispose()
}
