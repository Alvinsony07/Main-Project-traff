import { useState, useEffect } from 'react';
import api, { API_BASE } from '../api';

const cardStyle = { background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: '16px', padding: '24px', backdropFilter: 'blur(12px)' };
const badgeColors = { GREEN: '#10b981', YELLOW: '#f59e0b', RED: '#ef4444' };

export default function Dashboard() {
    const [status, setStatus] = useState(null);
    const [overrideMsg, setOverrideMsg] = useState('');

    useEffect(() => {
        const load = () => api.get('/status').then(r => setStatus(r.data)).catch(() => { });
        load();
        const interval = setInterval(load, 2000);
        return () => clearInterval(interval);
    }, []);

    const handleOverride = async (laneIdx) => {
        try {
            await api.post('/override', { lane_id: laneIdx });
            setOverrideMsg(`Lane ${laneIdx + 1} forced to GREEN`);
            setTimeout(() => setOverrideMsg(''), 3000);
        } catch (e) { setOverrideMsg('Override failed'); }
    };

    const signalStatus = status?.signal_status || {};
    const laneData = status?.lane_data || {};

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Header */}
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '26px', fontWeight: 'bold', margin: '0 0 4px 0' }}>Live Dashboard</h2>
                    <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>Real-time traffic monitoring and incident detection</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
                    <span style={{ color: '#34d399', fontSize: '12px', fontWeight: '600', letterSpacing: '0.5px' }}>SYSTEM ACTIVE</span>
                </div>
            </header>

            {/* Signal Status Bar */}
            <div style={{ ...cardStyle, display: 'flex', gap: '16px', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '16px', flex: 1 }}>
                    {(signalStatus.states || ['RED', 'RED', 'RED', 'RED']).map((state, i) => (
                        <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '12px', borderRadius: '12px', background: 'rgba(15,23,42,0.5)' }}>
                            <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: badgeColors[state] || '#ef4444', boxShadow: `0 0 16px ${badgeColors[state] || '#ef4444'}40` }} />
                            <span style={{ fontSize: '12px', color: '#94a3b8' }}>Lane {i + 1}</span>
                            <span style={{ fontSize: '11px', fontWeight: '700', color: badgeColors[state] || '#ef4444' }}>{state}</span>
                            <button onClick={() => handleOverride(i)} style={{ fontSize: '10px', padding: '4px 10px', borderRadius: '6px', border: '1px solid #475569', background: 'transparent', color: '#94a3b8', cursor: 'pointer' }}>
                                Override
                            </button>
                        </div>
                    ))}
                </div>
                <div style={{ textAlign: 'center', padding: '0 24px' }}>
                    <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#f59e0b' }}>{signalStatus.remaining_time || 0}s</div>
                    <div style={{ fontSize: '11px', color: '#64748b' }}>Remaining</div>
                    {signalStatus.ambulance_mode && <div style={{ color: '#ef4444', fontSize: '12px', fontWeight: '700', marginTop: '4px' }}>🚨 AMBULANCE MODE</div>}
                </div>
            </div>
            {overrideMsg && <div style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '10px', padding: '10px', color: '#60a5fa', fontSize: '13px', textAlign: 'center' }}>{overrideMsg}</div>}

            {/* Stats Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                {[0, 1, 2, 3].map(i => {
                    const ld = laneData[i] || { count: 0, density: 'Low', details: {} };
                    const dColors = { Low: '#10b981', Medium: '#f59e0b', High: '#ef4444' };
                    return (
                        <div key={i} style={cardStyle}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                <span style={{ fontSize: '13px', color: '#94a3b8' }}>Lane {i + 1}</span>
                                <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '999px', background: `${dColors[ld.density] || '#10b981'}20`, color: dColors[ld.density] || '#10b981', fontWeight: '600' }}>{ld.density}</span>
                            </div>
                            <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{ld.count}</div>
                            <div style={{ fontSize: '11px', color: '#64748b' }}>vehicles detected</div>
                            {Object.keys(ld.details || {}).length > 0 && (
                                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '8px' }}>
                                    {Object.entries(ld.details).map(([type, count]) => count > 0 && (
                                        <span key={type} style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: '#0f172a', color: '#94a3b8' }}>{type}: {count}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Video Feeds */}
            <div style={{ ...cardStyle, borderRadius: '20px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', margin: '0 0 16px 0' }}>Live Camera Feeds</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    {[0, 1, 2, 3].map(i => (
                        <div key={i} style={{ position: 'relative', borderRadius: '14px', overflow: 'hidden', border: '1px solid rgba(51,65,85,0.5)', background: '#0f172a', aspectRatio: '16/9' }}>
                            <img src={`${API_BASE}/video_feed/${i}`} alt={`Lane ${i + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} crossOrigin="anonymous" />
                            <div style={{ position: 'absolute', top: '10px', left: '10px', background: 'rgba(0,0,0,0.7)', padding: '4px 12px', borderRadius: '999px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ef4444', animation: 'pulse 2s infinite' }} />
                                Lane {i + 1}
                            </div>
                        </div>
                    ))}
                </div>
                <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }`}</style>
            </div>
        </div>
    );
}
