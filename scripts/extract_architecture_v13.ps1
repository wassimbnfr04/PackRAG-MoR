$ErrorActionPreference = 'Stop'
$projectTask = Split-Path -Parent $PSScriptRoot
$sourceTask = 'C:\Users\Fkagf\Downloads\PackRAG-MoR_Final_Architecture_Specification_v1.3.docx'
$outputTask = Join-Path $projectTask 'artifacts/v1.3/architecture'
New-Item -ItemType Directory -Path $outputTask -Force | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$streamTask = [IO.FileStream]::new($sourceTask,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
try {
    $memoryTask = [IO.MemoryStream]::new()
    $streamTask.CopyTo($memoryTask)
    $bytesTask = $memoryTask.ToArray()
    $memoryTask.Position = 0
    $zipTask = [IO.Compression.ZipArchive]::new($memoryTask,[IO.Compression.ZipArchiveMode]::Read,$true)
    try {
        $readerTask = [IO.StreamReader]::new($zipTask.GetEntry('word/document.xml').Open())
        try { [xml]$xmlTask = $readerTask.ReadToEnd() } finally { $readerTask.Dispose() }
        $nsTask = [Xml.XmlNamespaceManager]::new($xmlTask.NameTable)
        $nsTask.AddNamespace('w','http://schemas.openxmlformats.org/wordprocessingml/2006/main')
        $paragraphsTask = @()
        $indexTask = 0
        foreach ($paragraphTask in $xmlTask.SelectNodes('//w:body//w:p',$nsTask)) {
            $piecesTask = foreach ($nodeTask in $paragraphTask.SelectNodes('.//w:t|.//w:br|.//w:cr|.//w:tab',$nsTask)) {
                if ($nodeTask.LocalName -eq 't') { $nodeTask.InnerText }
                elseif ($nodeTask.LocalName -eq 'tab') { "`t" }
                else { "`n" }
            }
            $paragraphsTask += [ordered]@{ index=$indexTask; text=($piecesTask -join ''); in_table=($null -ne $paragraphTask.SelectSingleNode('ancestor::w:tc',$nsTask)) }
            $indexTask++
        }
        $encodingTask = [Text.UTF8Encoding]::new($false)
        [IO.File]::WriteAllBytes((Join-Path $outputTask 'architecture-v1.3.docx'),$bytesTask)
        [IO.File]::WriteAllText((Join-Path $outputTask 'paragraphs.json'),(ConvertTo-Json -InputObject $paragraphsTask -Depth 6),$encodingTask)
        [IO.File]::WriteAllText((Join-Path $outputTask 'architecture-v1.3.txt'),(($paragraphsTask | ForEach-Object { '['+$_.index+'] '+$_.text }) -join "`n"),$encodingTask)
        $hashTask = [Security.Cryptography.SHA256]::Create()
        try { $digestTask = [Convert]::ToHexString($hashTask.ComputeHash($bytesTask)).ToLowerInvariant() } finally { $hashTask.Dispose() }
        [IO.File]::WriteAllText((Join-Path $outputTask 'source.json'),(ConvertTo-Json -InputObject ([ordered]@{ source=$sourceTask; sha256=$digestTask; bytes=$bytesTask.Length; paragraphs=$paragraphsTask.Count; extraction='All body paragraphs including tables, breaks and tabs, in document order'; reference_only=$true; user_authorization='v1.3 implementation mission and later incremental integration instructions' }) -Depth 4),$encodingTask)
        Write-Output "Saved $($paragraphsTask.Count) paragraphs; source SHA256 $digestTask"
    } finally { $zipTask.Dispose(); $memoryTask.Dispose() }
} finally { $streamTask.Dispose() }
