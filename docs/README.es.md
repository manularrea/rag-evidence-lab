# RAG Evidence Lab · Español

**Revisa citas y cifras sospechosas antes de publicar respuestas de tu RAG.**

La respuesta dice «90 días» y cita una política que dice «30 días». Esta herramienta señala la cifra que falta en la evidencia y genera un reporte fácil de revisar.

```bash
git clone https://github.com/manularrea/rag-evidence-lab.git
cd rag-evidence-lab
python -m rag_evidence_lab examples/demo.json --html report.html --json report.json
```

Abre `report.html`. No necesitas claves de API ni dependencias de ejecución. Requiere Python 3.10+.

Recibe respuestas, documentos recuperados y citas con formato `[id]`. Señala citas ausentes o desconocidas, números sin coincidencia y bajo solapamiento textual. Exporta tus datos con el [formato del README](../README.md#bring-your-own-rag-run).

La comparación numérica normaliza formatos comunes de inglés y español de forma conservadora: `1,000`, `1.000`, `1 000` y `1000` se comparan como el mismo valor; `1,5` se compara con `1.5`, no con `15`. El signo de porcentaje se conserva, así que `30%` no coincide con `30`. Los valores con cero inicial como `0.125` y `0,125` permanecen decimales; para formas ambiguas no nulas se conserva la regla de agrupación: `1.234` se interpreta como `1234`, mientras `1.2340` permanece decimal. No es un analizador completo de locales o unidades: unidades textuales, monedas, notación científica y agrupaciones ambiguas siguen siendo limitaciones.

**Es un filtro de revisión, no un verificador semántico.** No entiende negaciones, cálculos, unidades o contradicciones. Una respuesta sin alertas puede ser incorrecta. Las paráfrasis válidas también pueden producir alertas.

Para cambios de prompt o retrieval, `--baseline reporte-anterior.json` compara la cantidad de afirmaciones con alertas por caso. Mantén los mismos IDs y umbral; usa entradas comparables. `--max-flagged 0` falla cuando hay alguna afirmación con alertas.

Los reportes incluyen el texto de tus fuentes: revísalos antes de compartirlos. Para contribuir, usa ejemplos sintéticos, ejecuta las [pruebas](../CONTRIBUTING.md) y abre un PR pequeño que explique el comportamiento.

Si te ayuda a encontrar un error, dale una estrella al repo y cuéntanos el caso de uso.
