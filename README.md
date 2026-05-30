# Farmacia App — Guía de Mostrador

App Streamlit mobile-first para capacitación y consulta en mostrador de farmacia.

## Estructura

```
farmacia_app/
├── app.py                    # App principal
├── requirements.txt
├── .gitignore
├── assets/
│   └── guia_OS_general.pdf   # PDF de obras sociales (NO subir al repo, agregar a .gitignore)
└── .streamlit/
    └── secrets.toml          # NUNCA subir al repo (está en .gitignore)
```

## Deploy en Streamlit Community Cloud

### 1. Repo en GitHub
```bash
git init
git add app.py requirements.txt .gitignore README.md
git commit -m "initial commit"
git remote add origin https://github.com/TU_USUARIO/farmacia-app.git
git push -u origin main
```


## Actualizar el vademécum
Editar directamente el Google Sheet. La app refresca el cache cada 1 hora.
Para forzar refresco inmediato: menú hamburguesa → "Rerun" en la app.

## Agregar PDF de Obras Sociales
Subir el PDF como `assets/guia_OS_general.pdf` directamente en Streamlit Cloud
via Settings → File uploader, o incluirlo en el repo si no es confidencial.

## Columnas requeridas en Google Sheets

| Columna | Requerida | Descripción |
|---|---|---|
| Clasificacion | ✅ | Categoría (analgesicos, digestivos, etc.) |
| Droga | ✅ | Nombre de la droga |
| Definición | ✅ | Tipo/mecanismo |
| Dosis | ✅ | Dosis disponibles |
| Usos | ❌ | Indicaciones |
| Marcas | ❌ | Marcas comerciales separadas por coma |
| Forma Farmaceutica | ❌ | Comprimidos, jarabe, etc. separados por coma |
| Notas | ❌ | Info de stock, góndola |
| Alertas | ❌ | Contraindicaciones y precauciones |

Filas con Clasificacion, Droga, Definición o Dosis vacíos son ignoradas.
