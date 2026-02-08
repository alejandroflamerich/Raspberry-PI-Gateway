# 1) Ver estado (qué está modificado / sin track / stageado)
git status

# 2) Stage: agregar archivos al área de preparación
git add .                 # agrega todo (lo más común)
# o:
git add <archivo>         # agrega un archivo específico
git add -A                # agrega todo (incluye borrados)
git add -p                # modo interactivo (hunks)

# 3) Confirmar qué quedó en stage
git status
git diff --staged         # ver diferencias que vas a commitear

# 4) Commit: guardar el snapshot
git commit -m "Mensaje claro del cambio"

# 5) (Primera vez) definir rama principal si aplica
git branch -M main        # opcional, si quieres usar main

# 6) (Primera vez) agregar el remoto (GitHub/GitLab/Bitbucket)
git remote add origin <URL_DEL_REPO>

# 7) Ver remotos
git remote -v

# 8) Subir (push)
git push -u origin main   # primera vez (crea tracking)
# luego normalmente solo:
git push
