import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';
const card = { background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: '16px', padding: '24px' };
const btn = { padding: '10px 20px', borderRadius: '10px', border: 'none', fontSize: '13px', fontWeight: '600', cursor: 'pointer' };
const statusColors = { 'Dispatched': '#f59e0b', 'En Route': '#3b82f6', 'Arrived': '#8b5cf6', 'Patient Loaded': '#10b981', 'Complete': '#64748b', 'Declined': '#ef4444' };
const statusSteps = ['Dispatched', 'En Route', 'Arrived', 'Patient Loaded', 'Complete'];

export default function AmbulancePortal() {
    const [dispatches, setDispatches] = useState([]);

    const load = () => axios.get(`${API_BASE}/dispatch/active`).then(r => setDispatches(r.data.dispatches || [])).catch(() => { });

    useEffect(() => { load(); const interval = setInterval(load, 5000); return () => clearInterval(interval); }, []);

    const accept = async (id) => { await axios.post(`${API_BASE}/dispatch/${id}/accept`); load(); };
    const decline = async (id) => { await axios.post(`${API_BASE}/dispatch/${id}/decline`); load(); };
    const updateStatus = async (id, status) => { await axios.post(`${API_BASE}/dispatch/${id}/status`, { status }); load(); };

    return (
        <div style={{ minHeight: '100vh', background: '#0f172a', color: '#f8fafc', fontFamily: "'Inter', 'Segoe UI', sans-serif", padding: '24px' }}>
            <div style={{ maxWidth: '900px', margin: '0 auto' }}>
                <header style={{ textAlign: 'center', marginBottom: '32px' }}>
                    <h1 style={{ fontSize: '28px', fontWeight: 'bold', margin: '0 0 8px 0' }}>
                        <span style={{ color: '#ef4444' }}>🚑</span> Ambulance Driver Portal
                    </h1>
                    <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>Receive and manage dispatch alerts in real-time.</p>
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '12px', alignItems: 'center' }}>
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', animation: 'pulse 2s infinite' }} />
                        <span style={{ color: '#64748b', fontSize: '13px' }}>Auto-refreshing every 5 seconds</span>
                    </div>
                    <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}`}</style>
                </header>

                {dispatches.length === 0 ? (
                    <div style={{ ...card, textAlign: 'center', padding: '64px 24px' }}>
                        <div style={{ fontSize: '48px', marginBottom: '12px' }}>📡</div>
                        <p style={{ fontSize: '16px', color: '#94a3b8' }}>No active dispatches</p>
                        <p style={{ fontSize: '13px', color: '#64748b' }}>Waiting for incoming alerts...</p>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {dispatches.map(d => (
                            <div key={d.id} style={{ ...card, borderLeft: `4px solid ${statusColors[d.status]}` }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                                    <div>
                                        <h3 style={{ fontSize: '18px', margin: '0 0 4px 0' }}>Dispatch #{d.id}</h3>
                                        <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>Report #{d.report_id} • {d.timestamp}</p>
                                    </div>
                                    <span style={{ fontSize: '12px', padding: '4px 12px', borderRadius: '999px', background: `${statusColors[d.status]}20`, color: statusColors[d.status], fontWeight: '700' }}>{d.status}</span>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                                    <div style={{ background: '#0f172a', borderRadius: '10px', padding: '12px' }}>
                                        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>Location</div>
                                        <div style={{ fontSize: '14px' }}>{d.location || 'Not specified'}</div>
                                    </div>
                                    <div style={{ background: '#0f172a', borderRadius: '10px', padding: '12px' }}>
                                        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>Hospital</div>
                                        <div style={{ fontSize: '14px' }}>{d.hospital_name}</div>
                                    </div>
                                    <div style={{ background: '#0f172a', borderRadius: '10px', padding: '12px' }}>
                                        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>Distance</div>
                                        <div style={{ fontSize: '14px' }}>{d.distance_km ? `${d.distance_km} km` : 'N/A'}</div>
                                    </div>
                                    <div style={{ background: '#0f172a', borderRadius: '10px', padding: '12px' }}>
                                        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>Description</div>
                                        <div style={{ fontSize: '14px' }}>{d.description || 'No details'}</div>
                                    </div>
                                </div>

                                {/* Progress steps */}
                                <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
                                    {statusSteps.map((step, sIdx) => {
                                        const currentIdx = statusSteps.indexOf(d.status);
                                        const isActive = sIdx <= currentIdx;
                                        return (
                                            <div key={step} style={{ flex: 1, height: '4px', borderRadius: '2px', background: isActive ? statusColors[d.status] : '#334155' }} />
                                        );
                                    })}
                                </div>

                                {/* Action Buttons */}
                                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                    {d.status === 'Dispatched' && (
                                        <>
                                            <button onClick={() => accept(d.id)} style={{ ...btn, background: '#10b981', color: 'white' }}>✓ Accept</button>
                                            <button onClick={() => decline(d.id)} style={{ ...btn, background: '#ef4444', color: 'white' }}>✗ Decline</button>
                                        </>
                                    )}
                                    {d.status === 'En Route' && <button onClick={() => updateStatus(d.id, 'Arrived')} style={{ ...btn, background: '#8b5cf6', color: 'white' }}>📍 Mark Arrived</button>}
                                    {d.status === 'Arrived' && <button onClick={() => updateStatus(d.id, 'Patient Loaded')} style={{ ...btn, background: '#10b981', color: 'white' }}>🏥 Patient Loaded</button>}
                                    {d.status === 'Patient Loaded' && <button onClick={() => updateStatus(d.id, 'Complete')} style={{ ...btn, background: '#3b82f6', color: 'white' }}>✓ Complete</button>}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
