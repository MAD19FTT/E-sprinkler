// for Mapbox API
const apiKey ='pk.eyJ1Ijoic2FtMzExIiwiYSI6ImNrdDRuaTA3eTAwYXoyd3BraW1xa2duYWMifQ.hn48VQPLLrZrQdueXVMkWQ';

// for the center view of the map
const mymap = L.map('map').setView([5.042320, 115.058788], 13);

L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
    maxZoom: 18,
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1,
    accessToken: apiKey
}).addTo(mymap);

L.styleLayer('https://api.mapbox.com/styles/v1/mapbox/streets-v11', {
  // This map option disables world wrapping.
  continuousWorld: false,
  // This option disables loading tiles outside of the world bounds. By default, it is false.
  noWrap: true,
  renderWorldCopies: false,
  accessToken: apiKey
}).addTo(mymap);

// adding marker
const marker= L.marker([5.042086, 115.059314]).addTo(mymap);

// add popup message 
let template = `

<h1>My Place</h1>

`
marker.bindPopup(template)

// add circle
const circle = L.circle([5.042086, 115.059314], {
    radius:500
}).addTo(mymap).bindPopup('Moisture: 60%')