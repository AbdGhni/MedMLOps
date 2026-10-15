param(
    [string]$Source = 'C:/home/USER
    [string]$Destination = 'C:/Projects/MedMLOps'
)
$ErrorActionPreference = 'Stop'
$sourceFull = (Resolve-Path -LiteralPath $Source).Path
$destinationFull = [IO.Path]::GetFullPath($Destination)
if ($destinationFull.StartsWith($sourceFull + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
    $destinationFull.Equals($sourceFull, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Destination must differ from source and must not be inside source.'
}
if (Test-Path -LiteralPath $destinationFull) {
    throw 'Destination already exists. Select a new empty destination; nothing is overwritten.'
}
$baseCommit = '[private-revision]'
git -C $sourceFull cat-file -e ($baseCommit + '^{commit}')
if ($LASTEXITCODE -ne 0) { throw 'Required v2 base commit missing in source.' }
$sourceHead = (git -C $sourceFull rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot identify source HEAD.' }
New-Item -ItemType Directory -Path $destinationFull -ErrorAction Stop | Out-Null
# Copy only; never /MIR, /PURGE, /MOVE, ACL changes or source cleanup.
robocopy $sourceFull $destinationFull /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /XD .venv .venv-phase3 __pycache__
$copyCode = $LASTEXITCODE
if ($copyCode -ge 8) { throw "Copy failed ($copyCode). Source and partial destination are retained." }
$destinationHead = (git -C $destinationFull rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $destinationHead -ne $sourceHead) { throw 'Copied HEAD differs from source.' }
git -C $destinationFull cat-file -e ($baseCommit + '^{commit}')
if ($LASTEXITCODE -ne 0) { throw 'v2 base commit not preserved.' }
git -C $destinationFull fsck --full
if ($LASTEXITCODE -ne 0) { throw 'Git integrity check failed.' }
Push-Location $destinationFull
try {
    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Post-copy test suite failed; do not discard source.' }
} finally { Pop-Location }
Write-Output "Copy and history validated at $destinationFull. Source remains untouched."
