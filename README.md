
---

# 📊 AppFinanzAr

**AppFinanzAr** es una aplicación de análisis financiero desarrollada en **Streamlit**, diseñada para centralizar el seguimiento de **acciones, criptomonedas y ETFs**, con foco en experiencia de usuario, personalización y una arquitectura preparada para escalar de **modo DEMO a datos reales** con mínimos cambios.

---

## ✨ Características principales

### 🎯 Dashboard central

* Selector de activo unificado (acciones, criptos y ETFs)
* Visualización de precios con **gráfico OHLC + medias móviles**
* Selector de **rango temporal claro y flexible**

  * Semanal, quincenal, mensual, trimestral, anual
  * Rango personalizado con calendario
* Flags informativos del activo
* Estado del mercado en tiempo real (según tipo de activo)

---

### ⭐ Favoritos

* Agregar / quitar activos con un solo clic
* Persistencia por usuario
* Navegación directa desde sidebar
* Confirmación segura al eliminar
* Exportación de favoritos a CSV

---

### 🏆 Ranking personalizado

* Ranking basado **exclusivamente en tus favoritos**
* Métricas claras:

  * Score
  * Riesgo
  * Balance riesgo/retorno
* Selección directa de activos desde el ranking

---

### 🔀 Comparación rápida

* Comparación entre dos activos favoritos
* Incluye:

  * Gráfico comparativo
  * Score
  * Riesgo
  * Balance
  * Tipo de activo
  * Estado del mercado

---

### 🧠 Recomendado para vos

* Recomendación automática basada en:

  * Mejor balance riesgo / score
  * Excluye el activo actualmente seleccionado
* Navegación directa al activo recomendado

---

### 🧭 ETF Finder

* Búsqueda de ETFs por **categoría e industria**
* Tipos soportados:

  * Indexados
  * Temáticos
  * Sectoriales
  * Apalancados
  * Inversos
* Listado contextual de ETFs disponibles
* Selección directa al dashboard

---

### 📰 Noticias & Sentimiento

* Noticias simuladas por activo
* Clasificación visual:

  * Positivo
  * Neutral
  * Negativo

---

### ⚠️ Alertas

* Alertas de precio
* Alertas inteligentes (volatilidad, movimientos bruscos, pump)
* Métrica de riesgo consolidada por activo

---

## 🧱 Arquitectura

La app está diseñada con una **arquitectura desacoplada**, lista para pasar de DEMO a datos reales sin refactor del frontend.

```
appfinanzar/
│
├── app.py
│
├── ui/
│   └── dashboard_ui.py
│
├── core/
│   ├── favorites.py
│   └── scoring.py
│
├── services/        # futuro: APIs reales
│
└── README.md
```

### Principios clave

* UI independiente del origen de datos
* Estado centralizado con `st.session_state`
* Funciones DEMO intercambiables por servicios reales
* Sin dependencias cruzadas entre UI y datos

---

## 🔁 Modo DEMO → Datos reales

Actualmente la app funciona en **modo DEMO**.

Para pasar a datos reales:

* Se reemplazan funciones como:

  * `demo_ohlc`
  * `demo_overview`
  * scores simulados
* **No se modifica el dashboard ni el sidebar**
* La experiencia de usuario se mantiene intacta

---

## 🧪 Estado actual

✔ Autenticación funcional
✔ Estado por usuario aislado
✔ Persistencia de favoritos
✔ Flujos completos y estables
✔ UI cerrada y validada

---

## 🚀 Tecnologías utilizadas

* Python 3.11+
* Streamlit
* Pandas
* NumPy
* Plotly

---

## 📌 Roadmap (opcional)

* Integración con proveedor de datos financieros
* Persistencia en base de datos
* Alertas en tiempo real
* Backtesting de estrategias
* Deploy productivo

---

## 📝 Nota final

AppFinanzAr fue diseñada priorizando:

* claridad
* escalabilidad
* experiencia de usuario
* facilidad de mantenimiento

La base está lista para evolucionar a producción sin reescrituras.

