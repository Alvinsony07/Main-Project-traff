import { useState, useEffect, useRef } from 'react';
import api from '../api';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const card = { background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: '20px', padding: '24px' };

export default function CityOverview() {
    const mapRef = useRef(null);
    const mapInstance = useRef(null);
    const [data, setData] = useState(null);

    useEffect(() => {
        api.get('/city_map_data').then(r => setData(r.data)).catch(() => { });
        const interval = setInterval(() => api.get('/city_map_data').then(r => setData(r.data)).catch(() => { }), 10000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (!mapRef.current || mapInstance.current) return;
        mapInstance.current = L.map(mapRef.current).setView([10.0261, 76.3125], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(mapInstance.current);
    }, []);

    useEffect(() => {
        if (!mapInstance.current || !data) return;
        // Clear old markers
        mapInstance.current.eachLayer(layer => { if (layer instanceof L.Marker || layer instanceof L.CircleMarker) mapInstance.current.removeLayer(layer); });

        // Incident markers (red)
        (data.reports || []).forEach(r => {
            if (r.latitude && r.longitude) {
                L.circleMarker([r.latitude, r.longitude], { radius: 8, color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.7 })
                    .bindPopup(`<b>Incident #${r.id}</b><br>${r.location}<br>Status: ${r.status}`)
                    .addTo(mapInstance.current);
            }
        });

        // Dispatch markers (blue)
        (data.dispatches || []).forEach(d => {
            if (d.accident_lat && d.accident_lng) {
                L.circleMarker([d.accident_lat, d.accident_lng], { radius: 10, color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.6 })
                    .bindPopup(`<b>Dispatch #${d.id}</b><br>Hospital: ${d.hospital_name}<br>Status: ${d.status}`)
                    .addTo(mapInstance.current);
            }
            if (d.hospital_lat && d.hospital_lng) {
                L.circleMarker([d.hospital_lat, d.hospital_lng], { radius: 6, color: '#10b981', fillColor: '#10b981', fillOpacity: 0.7 })
                    .bindPopup(`<b>${d.hospital_name}</b>`)
                    .addTo(mapInstance.current);
            }
        });
    }, [data]);

    const summary = data?.summary || {};

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <header>
                <h2 style={{ fontSize: '26px', fontWeight: 'bold', margin: '0 0 4px 0' }}>City Overview</h2>
                <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>Interactive map with traffic, incidents, and ambulance dispatches.</p>
            </header>

            {/* Summary */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                {[
                    { label: 'Total Vehicles', value: summary.total_vehicles || 0, color: '#3b82f6' },
                    { label: 'Active Incidents', value: summary.active_incidents || 0, color: '#ef4444' },
                    { label: 'Active Dispatches', value: summary.active_dispatches || 0, color: '#f59e0b' },
                ].map((s, i) => (
                    <div key={i} style={{ ...card, textAlign: 'center' }}>
                        <div style={{ fontSize: '28px', fontWeight: 'bold', color: s.color }}>{s.value}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>{s.label}</div>
                    </div>
                ))}
            </div>

            {/* Map */}
            <div style={{ ...card, padding: 0, overflow: 'hidden', height: '500px' }}>
                <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
            </div>
        </div>
    );
}
