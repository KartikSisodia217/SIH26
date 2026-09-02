# OceanEmbed Backend REST API (Member 3)

This is the backend API service for **OceanEmbed (SIH 2026)**. It serves ConvFormer 3D subsurface ocean temperature predictions, 2D horizontal depth slices, and Tropical Cyclone Heat Potential (TCHP) / $D_{26}$ isotherm derivations over the North Indian Ocean domain ($5^\circ\text{N}–30^\circ\text{N}$, $45^\circ\text{E}–105^\circ\text{E}$).

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch API Server
```bash
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open Interactive Swagger UI
Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) in your web browser.

---

## 🛰️ API Endpoints Reference

### 1. Health Check
* **Endpoint**: `GET /health`
* **Response**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "model_loaded": false,
  "mode": "mock_fallback"
}
```

---

### 2. Vertical Subsurface Temperature Profile (Member 4 Main Interface)
Returns predicted temperatures across all 15 target depth levels ($0\text{m}$ down to $1000\text{m}$) and the $D_{26}$ isotherm depth for a given coordinate.

* **Endpoint**: `GET /predict/profile` or `POST /predict/profile`
* **Query Parameters**:
  * `latitude`: float (5.0 to 30.0 °N) — e.g. `15.0`
  * `longitude`: float (45.0 to 105.0 °E) — e.g. `65.0`
  * `date`: string (optional, default `"latest"`)

#### Example Response (Ocean Coordinate):
```json
{
  "latitude": 15.0,
  "longitude": 65.0,
  "depths_m": [0, 5, 10, 20, 30, 50, 75, 100, 125, 150, 200, 300, 500, 700, 1000],
  "temperatures_c": [28.5, 28.5, 28.0, 27.5, 27.0, 25.0, 22.0, 18.0, 15.0, 13.0, 11.0, 8.0, 6.0, 5.0, 4.0],
  "d26_depth_m": 62.5,
  "surface_temp_c": 28.5,
  "bottom_temp_c": 4.0,
  "is_land": false,
  "units": "°C"
}
```

---

### 3. 2D Horizontal Depth Map Slice
Returns a $101 \times 241$ grid of ocean temperatures at a chosen depth level for map rendering.

* **Endpoint**: `GET /predict/slice` or `POST /predict/slice`
* **Query Parameters**:
  * `depth_m`: float (e.g. `0`, `5`, `50`, `100`, `200`, `1000`)
  * `date`: string (optional, default `"latest"`)

#### Example Response:
```json
{
  "depth_m": 50.0,
  "grid_shape": [101, 241],
  "latitudes": [5.0, 5.25, ..., 30.0],
  "longitudes": [45.0, 45.25, ..., 105.0],
  "temperatures_2d": [
    [25.4, 25.6, null, ...],
    ...
  ],
  "units": "°C"
}
```

---

### 4. D26 Isotherm Depth
Returns the exact thermocline depth where temperature drops to 26.0°C.

* **Endpoint**: `GET /predict/d26` or `POST /predict/d26`
* **Query Parameters**:
  * `latitude`: float (5.0 to 30.0 °N)
  * `longitude`: float (45.0 to 105.0 °E)

---

## 💻 Member 4 JavaScript Integration Examples

### Fetching Vertical Profile for Chart.js / Recharts
```javascript
async function getVerticalProfile(lat, lon) {
  const url = `http://localhost:8000/predict/profile?latitude=${lat}&longitude=${lon}`;
  const response = await fetch(url);
  
  if (!response.ok) {
    const error = await response.json();
    alert(`Error: ${error.detail}`);
    return;
  }
  
  const data = await response.json();
  console.log("Depths:", data.depths_m);
  console.log("Temperatures (°C):", data.temperatures_c);
  console.log("D26 Isotherm Depth (m):", data.d26_depth_m);
  return data;
}
```

---

## 🛡️ Guarantees & Error Handling

1. **Boundary Validation**: Coordinates outside $5^\circ\text{N}–30^\circ\text{N}$ or $45^\circ\text{E}–105^\circ\text{E}$ return `HTTP 400 Bad Request`.
2. **Land Mass Masking**: Land coordinates return `is_land: true` and `null` values for temperatures.
3. **Latency SLA**: Response latency is $< 2.0$ seconds.
4. **Graceful Fallback**: If `final_model.pt` is missing, the backend automatically operates in fallback mode with realistic synthetic ocean physics.
