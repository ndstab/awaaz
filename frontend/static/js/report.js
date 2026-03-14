document.addEventListener("DOMContentLoaded", () => {
  const mapContainer = document.getElementById("map");
  const latInput = document.getElementById("lat");
  const lngInput = document.getElementById("lng");
  const hint = document.getElementById("location-hint");
  const form = document.getElementById("report-form");
  const messageEl = document.getElementById("report-message");

  if (!mapContainer || !latInput || !lngInput || !form) {
    return;
  }

  // eslint-disable-next-line no-undef
  const map = new maplibregl.Map({
    container: "map",
    style: "https://demotiles.maplibre.org/style.json",
    center: [77.5946, 12.9716],
    zoom: 11,
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");

  let marker = null;

  map.on("click", (e) => {
    const { lng, lat } = e.lngLat;

    if (marker) {
      marker.setLngLat([lng, lat]);
    } else {
      marker = new maplibregl.Marker().setLngLat([lng, lat]).addTo(map);
    }

    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);

    if (hint) {
      hint.textContent = `Location set at ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!messageEl) return;

    const token = typeof requireAuth === "function" ? requireAuth() : null;
    if (!token) return;

    const type = document.getElementById("type").value;
    const severity = document.getElementById("severity").value;
    const description = document.getElementById("description").value;
    const city = document.getElementById("city").value.trim();
    const state = document.getElementById("state").value.trim();
    const addressText = document.getElementById("address_text").value.trim();
    const lat = latInput.value;
    const lng = lngInput.value;

    if (!lat || !lng) {
      messageEl.textContent = "Please click on the map to set a location.";
      return;
    }

    messageEl.textContent = "Submitting incident…";

    try {
      const response = await fetch("/api/v1/incidents/", {
        method: "POST",
        headers: typeof authHeaders === "function" ? authHeaders() : { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({
          type,
          severity,
          description,
          lat: parseFloat(lat),
          lng: parseFloat(lng),
          city,
          state,
          address_text: addressText,
        }),
      });

      if (!response.ok) {
        if (typeof handleAuthError === "function" && handleAuthError(response.status)) return;
        const errorText = await response.text();
        messageEl.textContent = `Error (${response.status}): ${errorText}`;
        return;
      }

      const data = await response.json();
      messageEl.textContent = "Incident submitted.";

      console.log("Created incident", data);
    } catch (error) {
      messageEl.textContent = "Network error submitting incident.";
      // eslint-disable-next-line no-console
      console.error(error);
    }
  });
});

