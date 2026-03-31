document.addEventListener("DOMContentLoaded", () => {
  const mapContainer = document.getElementById("map");
  if (!mapContainer) return;

  // Simple log to verify script is running
  // eslint-disable-next-line no-console
  console.log("Awaaz map: initializing");

  // eslint-disable-next-line no-undef
  const map = new maplibregl.Map({
    container: "map",
    style: "https://demotiles.maplibre.org/style.json",
    center: [77.5946, 12.9716], // Bengaluru
    zoom: 11,
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");

  const INCIDENTS_SOURCE_ID = "awaaz-incidents";
  const PENDING_LAYER_ID = "awaaz-incidents-pending";
  const ACTIVE_LAYER_ID = "awaaz-incidents-active";
  let lastRequestId = 0;

  function bboxParamFromBounds(bounds) {
    const south = bounds.getSouth().toFixed(6);
    const west = bounds.getWest().toFixed(6);
    const north = bounds.getNorth().toFixed(6);
    const east = bounds.getEast().toFixed(6);
    return `${south},${west},${north},${east}`;
  }

  function incidentPopupHtml(incident) {
    const title = `${incident.type} • ${incident.severity}`;
    const desc = incident.description ? incident.description : "";
    const place = `${incident.city || ""}${incident.state ? `, ${incident.state}` : ""}`;
    const href = `/incident/${incident.id}`;
    return `
      <div style="max-width: 240px;">
        <div style="font-weight: 600; margin-bottom: 0.25rem;">${title}</div>
        <div style="font-size: 0.9rem; margin-bottom: 0.25rem;">${place}</div>
        ${desc ? `<div style="font-size: 0.9rem; margin-bottom: 0.5rem;">${desc}</div>` : ""}
        <a href="${href}">View</a>
      </div>
    `;
  }

  function coordsFromLocation(location) {
    if (!location) return null;

    if (typeof location === "object") {
      if (location.type === "Point" && Array.isArray(location.coordinates)) {
        const [lng, lat] = location.coordinates;
        if (typeof lng === "number" && typeof lat === "number") return [lng, lat];
      }
      return null;
    }

    if (typeof location === "string") {
      const match = location.match(/POINT\\s*\\(\\s*([0-9.+-]+)\\s+([0-9.+-]+)\\s*\\)/i);
      if (!match) return null;
      const lng = parseFloat(match[1]);
      const lat = parseFloat(match[2]);
      if (Number.isFinite(lng) && Number.isFinite(lat)) return [lng, lat];
    }

    return null;
  }

  async function fetchAndRenderIncidents() {
    const requestId = ++lastRequestId;
    const url = "/api/v1/incidents/";

    const response = await fetch(url);
    if (!response.ok) return;
    const incidents = await response.json();
    if (requestId !== lastRequestId) return;

    // eslint-disable-next-line no-console
    console.log("Awaaz map: incidents fetched", incidents.length);

    const features = [];
    for (const incident of incidents) {
      let lng = incident.longitude;
      let lat = incident.latitude;
      if (typeof lng !== "number" || typeof lat !== "number") {
        const coords = coordsFromLocation(incident.location);
        if (!coords) continue;
        [lng, lat] = coords;
      }
      features.push({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [lng, lat],
        },
        properties: {
          id: incident.id,
          status: String(incident.status || "").toUpperCase(),
          popupHtml: incidentPopupHtml(incident),
        },
      });
    }

    const source = map.getSource(INCIDENTS_SOURCE_ID);
    if (source) {
      source.setData({
        type: "FeatureCollection",
        features,
      });
    }
  }

  let refreshTimer = null;
  function scheduleRefresh() {
    if (refreshTimer) window.clearTimeout(refreshTimer);
    refreshTimer = window.setTimeout(() => {
      fetchAndRenderIncidents().catch(() => {});
    }, 250);
  }

  map.on("load", () => {
    map.addSource(INCIDENTS_SOURCE_ID, {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features: [],
      },
    });

    map.addLayer({
      id: PENDING_LAYER_ID,
      type: "circle",
      source: INCIDENTS_SOURCE_ID,
      filter: ["==", ["get", "status"], "PENDING"],
      paint: {
        "circle-radius": 6,
        "circle-color": "#3b82f6",
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    });

    map.addLayer({
      id: ACTIVE_LAYER_ID,
      type: "circle",
      source: INCIDENTS_SOURCE_ID,
      filter: ["==", ["get", "status"], "ACTIVE"],
      paint: {
        "circle-radius": 6,
        "circle-color": "#ef4444",
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    });

    function onIncidentClick(e) {
      const feature = e.features?.[0];
      if (!feature) return;
      const coordinates = feature.geometry?.coordinates;
      const popupHtml = feature.properties?.popupHtml;
      if (!Array.isArray(coordinates) || !popupHtml) return;

      new maplibregl.Popup({ offset: 18 })
        .setLngLat(coordinates)
        .setHTML(popupHtml)
        .addTo(map);
    }

    function onIncidentEnter() {
      map.getCanvas().style.cursor = "pointer";
    }

    function onIncidentLeave() {
      map.getCanvas().style.cursor = "";
    }

    map.on("click", PENDING_LAYER_ID, onIncidentClick);
    map.on("click", ACTIVE_LAYER_ID, onIncidentClick);
    map.on("mouseenter", PENDING_LAYER_ID, onIncidentEnter);
    map.on("mouseenter", ACTIVE_LAYER_ID, onIncidentEnter);
    map.on("mouseleave", PENDING_LAYER_ID, onIncidentLeave);
    map.on("mouseleave", ACTIVE_LAYER_ID, onIncidentLeave);

    scheduleRefresh();
  });
  map.on("moveend", () => {
    scheduleRefresh();
  });
});

