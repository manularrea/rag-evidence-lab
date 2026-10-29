# RAG Evidence Lab · Español

**Revisa citas y cifras sospechosas antes de publicar respuestas de tu RAG.**

La respuesta dice «90 días» y cita una política que dice «30 días». Esta herramienta señala la cifra que falta en la evidencia y genera un reporte fácil de revisar.

```bash
git clone https://github.com/manularrea/rag-evidence-lab.git
cd rag-evidence-lab
python -m rag_evidence_lab examples/demo.json --html report.html --json report.json
```

Abre `report.html`. No necesitas claves de API ni dependencias de ejecución. Requiere Python 3.10+.

Recibe respuestas, documentos recuperados y citas con formato `[id]`. Señala citas ausentes o desconocidas, números sin coincidencia y bajo solapamiento textual. Exporta tus datos con el [formato del README](../README.md#bring-your-own-rag-run). Si usas LangChain, la [receta para RetrievalQA](../examples/recipes/README.md) convierte la exportación sin importar LangChain.

La comparación numérica normaliza un conjunto acotado de formatos comunes de inglés y español. Los grupos válidos de tres dígitos separados por espacios ordinarios, no separables o estrechos se normalizan: `1 000` coincide con `1000`. También se admiten grupos repetidos como `1,234,567` y `1.234.567`. Cuando aparecen coma y punto, el último separador sólo se interpreta como decimal si el otro forma grupos válidos de miles: `1,000.50` coincide con `1.000,50`.

Un único punto o coma seguido de tres dígitos, con un grupo inicial no nulo de uno a tres dígitos, es **ambiguo**. Sin evidencia del formato regional, `1.234`, `1,234`, `1,000` y `1.000` se comparan como literales etiquetados: no se interpretan automáticamente como miles ni decimales. La misma escritura puede coincidir consigo misma, pero `1.234` no coincide con `1234` ni con `1.2340`; permanece una alerta para revisión. Se aceptan más alertas de formato para no ocultar una posible diferencia real. Los grupos iniciales compuestos sólo de ceros, incluidos `0.125`, `0,125` y `00.125`, permanecen fraccionarios. `1,5` coincide con `1.5`, no con `15`. El porcentaje se conserva: `30%` no coincide con `30`, y `30 %` sí coincide con `30%`. El reporte conserva la escritura original del número sin coincidencia. Unidades textuales, monedas, notación científica, grupos mal formados y otras convenciones siguen siendo limitaciones; no es un analizador completo de locales o unidades.

**Es un filtro de revisión, no un verificador semántico.** No entiende negaciones, cálculos, unidades o contradicciones. Una respuesta sin alertas puede ser incorrecta. Las paráfrasis válidas también pueden producir alertas.

Para cambios de prompt o retrieval, `--baseline reporte-anterior.json` compara la cantidad de afirmaciones con alertas por caso. Mantén los mismos IDs y umbral; usa entradas comparables y genera ambos reportes con la misma versión de la herramienta: una actualización puede cambiar los conteos. `--max-flagged 0` falla cuando hay alguna afirmación con alertas.

Los reportes incluyen el texto de tus fuentes: revísalos antes de compartirlos. Para contribuir, usa ejemplos sintéticos, ejecuta las [pruebas](../CONTRIBUTING.md) y abre un PR pequeño que explique el comportamiento.

Si te ayuda a encontrar un error, dale una estrella al repo y cuéntanos el caso de uso.
