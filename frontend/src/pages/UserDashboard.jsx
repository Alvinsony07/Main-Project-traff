import { useState, useEffect } from 'react';
import api from '../api';

const card = { background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: '20px', padding: '24px' };
const input = { width: '100%', padding: '12px 16px', background: '#0f172a', border: '1px solid #334155', borderRadius: '10px', color: '#f1f5f9', fontSize: '14px', outline: 'none', boxSizing: 'border-box', marginBottom: '16px' };
const label = { display: 'block', fontSize: '13px', fontWeight: '500', color: '#94a3b8', marginBottom: '8px' };
const btn = { width: '100%', padding: '14px', background: 'linear-gradient(90deg, #ef4444, #dc2626)', border: 'none', borderRadius: '12px', color: 'white', fontSize: '16px', fontWeight: '600', cursor: 'pointer', transition: 'all 0.3s' };

export default function UserDashboard({ user }) {
    const [reports, setReports] = useState([]);
    const [formData, setFormData] = useState({ location: '', description: '', latitude: '', longitude: '' });
    const [status, setStatus] = useState('');

    const loadReports = () => api.get('/reports').then(r => {
        // Filter only current user's reports based on username returned from API
        const userReports = r.data.reports.filter(rep => rep.user === user.username);
        setReports(userReports);
    }).catch(() => { });

    useEffect(() => { loadReports(); }, [user]);

    const getLocationFields = () => {
        if ("geolocation" in navigator) {
            setStatus('Getting coordinates...');
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    setFormData({
                        ...formData,
                        latitude: position.coords.latitude.toFixed(6),
                        longitude: position.coords.longitude.toFixed(6)
                    });
                    setStatus('Coordinates acquired successfully.');
                    setTimeout(() => setStatus(''), 3000);
                },
                (error) => {
                    setStatus('Error getting location: ' + error.message);
                }
            );
        } else {
            setStatus('Geolocation is not supported by your browser.');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus('Submitting report...');
        try {
            const jwtTokenPayload = JSON.parse(atob(localStorage.getItem('token').split('.')[1]));
            const userId = jwtTokenPayload.sub;

            const payload = {
                ...formData,
                user_id: userId
            };

            const res = await api.post('/report_accident', payload);
            if (res.data.success) {
                setStatus('Accident reported successfully. Authorities have been notified.');
                setFormData({ location: '', description: '', latitude: '', longitude: '' });
                loadReports();
                setTimeout(() => setStatus(''), 5000);
            }
        } catch (err) {
            setStatus('Failed to submit report. Please try again.');
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <header>
                <h2 style={{ fontSize: '26px', fontWeight: 'bold', margin: '0 0 4px 0' }}>User Dashboard</h2>
                <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>Report traffic incidents and view your submission history.</p>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(350px, 1fr) 2fr', gap: '24px' }}>

                {/* Report Form */}
                <div style={card}>
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#ef4444', margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '24px' }}>🚨</span> Report an Incident
                    </h3>

                    {status && (
                        <div style={{
                            background: status.includes('success') ? 'rgba(16,185,129,0.1)' : 'rgba(59,130,246,0.1)',
                            border: `1px solid ${status.includes('success') ? 'rgba(16,185,129,0.3)' : 'rgba(59,130,246,0.3)'}`,
                            borderRadius: '10px', padding: '12px', color: status.includes('success') ? '#10b981' : '#60a5fa',
                            fontSize: '14px', marginBottom: '16px', textAlign: 'center'
                        }}>
                            {status}
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <label style={label}>Location (Required)</label>
                        <input
                            style={input} type="text"
                            placeholder="e.g. Main St Intersection" required
                            value={formData.location} onChange={e => setFormData({ ...formData, location: e.target.value })}
                        />

                        <label style={label}>Description</label>
                        <textarea
                            style={{ ...input, resize: 'vertical', minHeight: '80px' }}
                            placeholder="Describe the incident..."
                            value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })}
                        />

                        <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                            <div style={{ flex: 1 }}>
                                <label style={label}>Latitude</label>
                                <input style={{ ...input, marginBottom: 0 }} type="number" step="any" placeholder="Optional" value={formData.latitude} onChange={e => setFormData({ ...formData, latitude: e.target.value })} />
                            </div>
                            <div style={{ flex: 1 }}>
                                <label style={label}>Longitude</label>
                                <input style={{ ...input, marginBottom: 0 }} type="number" step="any" placeholder="Optional" value={formData.longitude} onChange={e => setFormData({ ...formData, longitude: e.target.value })} />
                            </div>
                        </div>

                        <button type="button" onClick={getLocationFields} style={{ width: '100%', padding: '10px', background: '#334155', border: 'none', borderRadius: '10px', color: '#f1f5f9', fontSize: '13px', cursor: 'pointer', marginBottom: '24px', transition: 'all 0.2s' }}>
                            📍 Get Current Location
                        </button>

                        <button type="submit" style={btn}>Submit Emergency Report</button>
                    </form>
                </div>

                {/* User's Reports List */}
                <div style={{ ...card, padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: '24px', borderBottom: '1px solid rgba(51,65,85,0.5)' }}>
                        <h3 style={{ fontSize: '18px', fontWeight: 'bold', margin: '0' }}>Your Recent Reports</h3>
                    </div>

                    {reports.length === 0 ? (
                        <div style={{ padding: '48px', textAlign: 'center', color: '#64748b' }}>
                            You haven't submitted any incident reports yet.
                        </div>
                    ) : (
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                            <thead>
                                <tr style={{ background: '#1e293b' }}>
                                    {['Location', 'GPS', 'Status', 'Time'].map(h => (
                                        <th key={h} style={{ padding: '14px 16px', textAlign: 'left', color: '#94a3b8', fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {reports.map((r, i) => (
                                    <tr key={i} style={{ borderBottom: '1px solid rgba(51,65,85,0.3)', background: i % 2 === 0 ? 'transparent' : 'rgba(15,23,42,0.3)' }}>
                                        <td style={{ padding: '14px 16px' }}>
                                            <div style={{ fontWeight: '500', color: '#f1f5f9', marginBottom: '4px' }}>{r.location}</div>
                                            <div style={{ fontSize: '12px', color: '#64748b' }}>{r.description || 'No description'}</div>
                                        </td>
                                        <td style={{ padding: '14px 16px', color: '#94a3b8', fontSize: '12px' }}>
                                            {r.latitude && r.longitude ? `${r.latitude}, ${r.longitude}` : 'N/A'}
                                        </td>
                                        <td style={{ padding: '14px 16px' }}>
                                            <span style={{
                                                fontSize: '12px', padding: '4px 10px', borderRadius: '999px', fontWeight: '600',
                                                background: r.status === 'Reported' ? 'rgba(245,158,11,0.2)' : (r.status === 'Verified' ? 'rgba(59,130,246,0.2)' : 'rgba(16,185,129,0.2)'),
                                                color: r.status === 'Reported' ? '#f59e0b' : (r.status === 'Verified' ? '#60a5fa' : '#10b981')
                                            }}>
                                                {r.status}
                                            </span>
                                        </td>
                                        <td style={{ padding: '14px 16px', color: '#94a3b8', fontSize: '13px' }}>{r.timestamp}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

            </div>
        </div>
    );
}
