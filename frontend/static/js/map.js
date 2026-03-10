document.addEventListener("DOMContentLoaded", () => {
  const mapContainer = document.getElementById("map");
  if (!mapContainer) return;

  // eslint-disable-next-line no-undef
  const map = new maplibregl.Map({
    container: "map",
    style: "https://demotiles.maplibre.org/style.json",
    center: [77.5946, 12.9716], // Bengaluru
    zoom: 11,
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");

  const markersById = new Map();
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
    const bbox = bboxParamFromBounds(map.getBounds());
    const url = `/api/v1/incidents/?bbox=${encodeURIComponent(bbox)}`;

    const response = await fetch(url);
    if (!response.ok) return;
    const incidents = await response.json();
    if (requestId !== lastRequestId) return;

    const seen = new Set();
    for (const incident of incidents) {
      seen.add(incident.id);

      const coords = coordsFromLocation(incident.location);
      if (!coords) continue;
      const [lng, lat] = coords;

      let marker = markersById.get(incident.id);
      if (!marker) {
        const popup = new maplibregl.Popup({ offset: 18 }).setHTML(
          incidentPopupHtml(incident),
        );
        marker = new maplibregl.Marker().setLngLat([lng, lat]).setPopup(popup).addTo(map);
        markersById.set(incident.id, marker);
      } else {
        marker.setLngLat([lng, lat]);
      }
    }

    for (const [id, marker] of markersById.entries()) {
      if (!seen.has(id)) {
        marker.remove();
        markersById.delete(id);
      }
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
    scheduleRefresh();
  });
  map.on("moveend", () => {
    scheduleRefresh();
  });
});

