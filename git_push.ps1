Set-Location -Path $PSScriptRoot

Write-Host "=========================="
Write-Host "  GIT: add/commit/push"
Write-Host "==========================`n"

# Validaciones
git --version | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Git no está instalado o no está en PATH." }

git rev-parse --is-inside-work-tree | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Esta carpeta no parece ser un repositorio Git." }

Write-Host "--- git status (antes) ---"
git status
Write-Host ""

Write-Host "--- git add . ---"
git add .
if ($LASTEXITCODE -ne 0) { throw "Falló git add ." }

$msg = Read-Host "Escribe el mensaje del commit (Enter para cancelar)"
if ([string]::IsNullOrWhiteSpace($msg)) {
  Write-Host "Cancelado (mensaje vacío)."
  exit 0
}

Write-Host "`n--- git commit -m `"$msg`" ---"
git commit -m $msg
if ($LASTEXITCODE -ne 0) {
  Write-Host "`nNota: si no había cambios para commitear, git puede fallar aquí."
  git status
  exit 0
}

Write-Host "`n--- git push ---"
git push
if ($LASTEXITCODE -ne 0) { throw "Falló git push (revisa login/remote/upstream)." }

Write-Host "`nOK: Cambios subidos."
git status
