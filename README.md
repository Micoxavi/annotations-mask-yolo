# 📄 Annotations-mask-yolo

**✨ PEP 8-compliant multiregion segmentation tool with YOLO export.**

---

## 🖼️ Descripción

Este script proporciona una interfaz gráfica (PyQt5) para:
- Segmentar múltiples regiones en una imagen 🖌️
- Guardar una máscara binaria 🟫
- Exportar las anotaciones en formato YOLO 📦

---

## ⚙️ Requisitos

- 🐍 Python 3.7+
- 📷 OpenCV (`cv2`)
- 🔢 NumPy
- 🖥️ PyQt5

Instálalos con:

```
pip install opencv-python numpy pyqt5
```

---
## 🚀 Uso

1. Ejecuta el script:

    ```
    python segmentation_mask_yolo.py
    ```

2. Dentro de la interfaz:

   - **🖼️ Cargar imagen**: selecciona una imagen para segmentar.  
   - **✏️ Dibujar polígonos**: haz clic para añadir vértices; doble clic izquierdo para cerrar el polígono.  
   - **🎯 Clase activa**: selecciona el ID de clase para la región dibujada.  
   - **💾 Guardar máscara**: exporta la máscara binaria en formato PNG.  
   - **📑 Guardar YOLO**: exporta las cajas delimitadoras normalizadas en un archivo `.txt` compatible con YOLO.  
   - **↩️ Deshacer polígono**: elimina el último polígono dibujado.  
   - **🗑️ Borrar todo**: reinicia la imagen y las anotaciones.  

---

## 📂 Estructura de archivos

- `segmentation_mask_yolo.py`: código principal.  
- Opcionalmente, carpeta `datasets/` para guardar imágenes y resultados.  

---

## 🔍 Explicación rápida

- **ZoomableGraphicsView**: permite hacer zoom con la rueda y cerrar polígonos con doble clic.  
- **SegmentationApp**: maneja la interfaz, eventos de dibujo y exportación.  
- **_poly_to_bbox_norm**: convierte un polígono a una caja YOLO normalizada `(cx, cy, bw, bh)`.  

---

## 🤝 Contribuciones

Si encuentras errores o quieres mejorar el script, ¡haz un fork y envía un pull request! 🛠️  

---
