import { useState, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'

// Fix for default marker icon in React-Leaflet
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

function LocationMarker({ position, label }) {
    useMapEvents({
        click(e) {
            // For now, clicks are handled by the parent to toggle start/end
        },
    })

    return position === null ? null : (
        <Marker position={position}>
            <Popup>{label}</Popup>
        </Marker>
    )
}

function App() {
    const [startPos, setStartPos] = useState(null)
    const [endPos, setEndPos] = useState(null)
    const [startAddress, setStartAddress] = useState('')
    const [endAddress, setEndAddress] = useState('')
    const [riskTolerance, setRiskTolerance] = useState(0.5)
    const [routeData, setRouteData] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [selectionMode, setSelectionMode] = useState('start') // 'start' or 'end'

    const handleMapClick = (e) => {
        if (selectionMode === 'start') {
            setStartPos(e.latlng)
            setStartAddress(`Lat: ${e.latlng.lat.toFixed(4)}, Lon: ${e.latlng.lng.toFixed(4)}`)
            setSelectionMode('end')
        } else {
            setEndPos(e.latlng)
            setEndAddress(`Lat: ${e.latlng.lat.toFixed(4)}, Lon: ${e.latlng.lng.toFixed(4)}`)
            setSelectionMode('start')
        }
    }

    const geocodeAddress = async (address) => {
        if (!address) return null;
        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`, {
                headers: {
                    'User-Agent': 'TorontoSafetyRoutes/1.0'
                }
            });
            const data = await response.json();
            if (data && data.length > 0) {
                return {
                    lat: parseFloat(data[0].lat),
                    lng: parseFloat(data[0].lon),
                    display_name: data[0].display_name
                };
            }
            throw new Error('Address not found');
        } catch (err) {
            console.error("Geocoding error:", err);
            setError(`Geocoding failed: ${err.message}`);
            return null;
        }
    }

    const handleAddressSearch = async (type) => {
        setLoading(true);
        setError(null);
        let result;
        if (type === 'start') {
            result = await geocodeAddress(startAddress);
            if (result) {
                setStartPos({ lat: result.lat, lng: result.lng });
                // Optional: Update address text to full name? Maybe annoying if user just typed "CN Tower"
                // setStartAddress(result.display_name); 
            }
        } else {
            result = await geocodeAddress(endAddress);
            if (result) {
                setEndPos({ lat: result.lat, lng: result.lng });
            }
        }
        setLoading(false);
    }

    const handleKeyDown = (e, type) => {
        if (e.key === 'Enter') {
            handleAddressSearch(type);
        }
    }

    const calculateRoute = async () => {
        if (!startPos || !endPos) return;

        setLoading(true)
        setError(null)
        try {
            const response = await fetch('http://localhost:5000/api/route', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    start_lat: startPos.lat,
                    start_lon: startPos.lng,
                    end_lat: endPos.lat,
                    end_lon: endPos.lng,
                    lambda: riskTolerance
                }),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.error || 'Failed to calculate route')
            }

            const data = await response.json()
            setRouteData(data)
        } catch (err) {
            console.error("Fetch error details:", err);
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    // Map content component to handle click events
    function MapEvents() {
        useMapEvents({
            click: handleMapClick,
        })
        return null
    }

    let polylinePositions = []
    if (routeData && routeData.geometry) {
        if (routeData.geometry.type === 'LineString') {
            polylinePositions = routeData.geometry.coordinates.map(coord => [coord[1], coord[0]])
        } else if (routeData.geometry.type === 'MultiLineString') {
            // Flatten MultiLineString
            routeData.geometry.coordinates.forEach(line => {
                line.forEach(coord => polylinePositions.push([coord[1], coord[0]]))
            })
        }
    }

    return (
        <div className="app-container">
            <div className="sidebar">
                <h1>Toronto Safety Routes</h1>

                <div className="control-group">
                    <h2>1. Select Points</h2>
                    <p>Click on map or search address.</p>

                    <div className="input-group">
                        <label>Start Location:</label>
                        <div className="search-row">
                            <input
                                type="text"
                                value={startAddress}
                                onChange={(e) => setStartAddress(e.target.value)}
                                onKeyDown={(e) => handleKeyDown(e, 'start')}
                                placeholder="Enter start address..."
                            />
                            <button onClick={() => handleAddressSearch('start')}>Find</button>
                        </div>
                    </div>

                    <div className="input-group">
                        <label>End Location:</label>
                        <div className="search-row">
                            <input
                                type="text"
                                value={endAddress}
                                onChange={(e) => setEndAddress(e.target.value)}
                                onKeyDown={(e) => handleKeyDown(e, 'end')}
                                placeholder="Enter end address..."
                            />
                            <button onClick={() => handleAddressSearch('end')}>Find</button>
                        </div>
                    </div>

                    <div className="status-indicator">
                        <span className={startPos ? "status-ok" : "status-waiting"}>
                            Start: {startPos ? `${startPos.lat.toFixed(4)}, ${startPos.lng.toFixed(4)}` : 'Not set'}
                        </span>
                        <span className={endPos ? "status-ok" : "status-waiting"}>
                            End: {endPos ? `${endPos.lat.toFixed(4)}, ${endPos.lng.toFixed(4)}` : 'Not set'}
                        </span>
                    </div>

                    <div className="mode-toggle">
                        <button
                            className={selectionMode === 'start' ? 'active' : ''}
                            onClick={() => setSelectionMode('start')}>
                            Set Start on Map
                        </button>
                        <button
                            className={selectionMode === 'end' ? 'active' : ''}
                            onClick={() => setSelectionMode('end')}>
                            Set End on Map
                        </button>
                    </div>
                </div>

                <div className="control-group">
                    <h2>2. Risk Tolerance</h2>
                    <label>Safety Importance: {riskTolerance}</label>
                    <input
                        type="range"
                        min="0"
                        max="10"
                        step="0.1"
                        value={riskTolerance}
                        onChange={(e) => setRiskTolerance(parseFloat(e.target.value))}
                    />
                    <div className="range-labels">
                        <span>Direct</span>
                        <span>Safe</span>
                    </div>
                </div>

                <div className="actions">
                    <button
                        className="calculate-btn"
                        onClick={calculateRoute}
                        disabled={!startPos || !endPos || loading}
                    >
                        {loading ? 'Processing...' : 'Find Route'}
                    </button>
                </div>

                {error && <div className="error-message">{error}</div>}

                {routeData && (
                    <div className="results">
                        <h2>Route Stats</h2>
                        <p><strong>Distance:</strong> {(routeData.distance_m / 1000).toFixed(2)} km</p>
                        <p><strong>Time:</strong> {Math.ceil(routeData.time_min)} min</p>
                        <p><strong>Avg Risk:</strong> {routeData.avg_risk.toFixed(2)}</p>
                    </div>
                )}
            </div>

            <div className="map-wrapper">
                {/* Center on Toronto */}
                <MapContainer center={[43.6532, -79.3832]} zoom={13} style={{ height: "100%", width: "100%" }}>
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <MapEvents />

                    <LocationMarker position={startPos} label="Start" />
                    <LocationMarker position={endPos} label="End" />

                    {polylinePositions.length > 0 &&
                        <Polyline positions={polylinePositions} color="blue" weight={5} />
                    }
                </MapContainer>
            </div>
        </div>
    )
}

export default App
