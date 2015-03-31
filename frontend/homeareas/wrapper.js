// requires Leaflet, tested with version 0.6.2

function createMap(divId, tileLayer, colors) {
    var opacity = 0.5;    

    // create map and add provided tiles
    var map = L.map(divId);
    tileLayer.addTo(map);

    // create legend
    var legend = L.control({position: 'bottomright'});
    legend.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend');

        var ul = L.DomUtil.create('ul');

        div.appendChild(ul);

        map.legendList = ul; // save in map object for future use in addMultiPolygonCoordinates

        return div;
    };
    map.addControl(legend);

    // common processing for geoJson objects
    map.addGeoJson = function (geoJson) {
        var layer = L.geoJson([geoJson], {

	        style: function (feature) {
		        return feature.properties && feature.properties.style;
	        },

	        onEachFeature: function onEachFeature(feature, layer) {
	            if (feature.properties && feature.properties.popupContent) {
		            layer.bindPopup(feature.properties.popupContent);
	            }
            }
        }).addTo(map);

        map.fitBounds(layer.getBounds());
    }

    // common processing for systems with home area coordinates
    map.addSystemMultiPolygon = function (coordinates, systemName) {
        var color = systemName in colors ? colors[systemName] : "#eee";
        var title = systemName + ' home area';

        var geoJsonMultiPolygon = {
            "type": "Feature",
            "properties": {
                "popupContent": title,
                "style": {
                    weight: 1,
                    color: "#999",
                    opacity: 1,
                    fillColor: color,
                    fillOpacity: opacity
                }
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": coordinates
            }
        };

        map.addGeoJson(geoJsonMultiPolygon);

        if (map.legendList) {
            var li = document.createElement('li');
            li.setAttribute('data-name-system', systemName);
            li.setAttribute('data-name-caption', title);
            li.setAttribute('data-color', color);

            var span = document.createElement('span');
            span.style.background = color;
            span.style.opacity = opacity;
            li.appendChild(span);

            li.appendChild(document.createTextNode(title));

            map.legendList.appendChild(li);
        }
    };

    return map;
};

