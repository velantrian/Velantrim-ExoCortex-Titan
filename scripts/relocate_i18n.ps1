$root = Split-Path $PSScriptRoot -Parent
$htmlPath = Join-Path $root "static\console\index.html"
$html = [IO.File]::ReadAllText($htmlPath)
$start = $html.IndexOf("    // --- VELANTRIM I18N START ---")
$end = $html.IndexOf("    // --- VELANTRIM I18N END ---")
if ($start -lt 0 -or $end -lt 0) { throw "i18n markers not found" }
$end = $end + "    // --- VELANTRIM I18N END ---".Length
$block = $html.Substring($start, $end - $start)
$html = $html.Remove($start, $end - $start)
$anchor = "    const el = (id) => document.getElementById(id);"
$pos = $html.IndexOf($anchor)
if ($pos -lt 0) { throw "anchor not found" }
$insertAt = $pos + $anchor.Length
$html = $html.Insert($insertAt, "`n`n" + $block + "`n")
[IO.File]::WriteAllText($htmlPath, $html)
Write-Host "i18n relocated after el()"
