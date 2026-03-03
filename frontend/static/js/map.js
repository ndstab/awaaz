// Basic MapLibre initialization placeholder
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
});

