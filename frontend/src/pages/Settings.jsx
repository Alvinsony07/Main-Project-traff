import { useState, useEffect } from 'react';
import api from '../api';

const card = { background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: '20px', padding: '28px' };
const label = { display: 'block', fontSize: '13px', fontWeight: '500', color: '#94a3b8', marginBottom: '8px' };
const input = { width: '100%', padding: '12px 16px', background: '#0f172a', border: '1px solid #334155', borderRadius: '10px', color: '#f1f5f9', fontSize: '14px', outline: 'none', boxSizing: 'border-box' };
const btn = { padding: '12px 24px', borderRadius: '10px', border: 'none', fontSize: '14px', fontWeight: '600', cursor: 'pointer' };

export default function Settings() {
    const [s, setS] = useState(null);
    const [msg, setMsg] = useState('');
    const [audit, setAudit] = useState([]);
    const [purgeMsg, setPurgeMsg] = useState('');

    useEffect(() => {
        api.get('/settings').then(r => setS(r.data)).catch(() => { });
        api.get('/audit_trail?per_page=10').then(r => setAudit(r.data.entries || [])).catch(() => { });
    }, []);

    const save = async () => {
        try {
            await api.post('/settings', s);
            setMsg('Settings saved successfully!');
            setTimeout(() => setMsg(''), 3000);
        } catch (e) { setMsg('Save failed'); }
    };

    const purge = async () => {
        if (!confirm('Are you sure? This will permanently delete all traffic history data.')) return;
        try {
            const r = await api.post('/purge_data');
            setPurgeMsg(`Purged ${r.data.purged.lane_stats} lane stats and ${r.data.purged.vehicle_logs} vehicle logs.`);
        } catch (e) { setPurgeMsg('Purge failed'); }
    };

    if (!s) return <p style={{ color: '#64748b' }}>Loading settings...</p>;

    const update = (key, val) => setS({ ...s, [key]: val });

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <header>
                <h2 style={{ fontSize: '26px', fontWeight: 'bold', margin: '0 0 4px 0' }}>System Settings</h2>
                <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>Configure AI models, traffic parameters, and system preferences.</p>
            </header>

            {msg && <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '10px', padding: '12px', color: '#10b981', fontSize: '14px', textAlign: 'center' }}>{msg}</div>}

            {/* AI Model Settings */}
            <div style={card}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', margin: '0 0 20px 0', color: '#e2e8f0' }}>🤖 AI Model Configuration</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
                    <div>
                        <label style={label}>YOLO Model</label>
                        <select value={s.yolo_model} onChange={e => update('yolo_model', e.target.value)} style={input}>
                            <option value="yolov8n">YOLOv8n (Nano)</option><option value="yolov8s">YOLOv8s (Small)</option><option value="yolov8m">YOLOv8m (Medium)</option>
                        </select>
                    </div>
                    <div>
                        <label style={label}>Vehicle Confidence (%)</label>
                        <input type="number" value={s.confidence_threshold} onChange={e => update('confidence_threshold', +e.target.value)} style={input} min={10} max={99} />
                    </div>
                    <div>
                        <label style={label}>Ambulance Confidence (%)</label>
                        <input type="number" value={s.ambulance_confidence} onChange={e => update('ambulance_confidence', +e.target.value)} style={input} min={10} max={99} />
                    </div>
                </div>
            </div>

            {/* Traffic Signal Timing */}
            <div style={card}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', margin: '0 0 20px 0', color: '#e2e8f0' }}>🚦 Signal Timing (Green Durations)</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
                    <div>
                        <label style={label}>Low Density Green (s)</label>
                        <input type="number" value={s.low_density_green} onChange={e => update('low_density_green', +e.target.value)} style={input} />
                    </div>
                    <div>
                        <label style={label}>Medium Density Green (s)</label>
                        <input type="number" value={s.medium_density_green} onChange={e => update('medium_density_green', +e.target.value)} style={input} />
                    </div>
                    <div>
                        <label style={label}>High Density Green (s)</label>
                        <input type="number" value={s.high_density_green} onChange={e => update('high_density_green', +e.target.value)} style={input} />
                    </div>
                </div>
            </div>

            {/* Toggles */}
            <div style={card}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', margin: '0 0 20px 0', color: '#e2e8f0' }}>⚙️ System Preferences</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    {[
                        { key: 'voice_alerts', label: 'Voice Alerts' },
                        { key: 'auto_dispatch', label: 'Auto Dispatch' },
                        { key: 'dark_mode', label: 'Dark Mode' },
                    ].map(t => (
                        <div key={t.key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: '#0f172a', borderRadius: '12px' }}>
                            <span style={{ fontSize: '14px', color: '#cbd5e1' }}>{t.label}</span>
                            <button onClick={() => update(t.key, !s[t.key])} style={{ width: '44px', height: '24px', borderRadius: '12px', border: 'none', background: s[t.key] ? '#3b82f6' : '#475569', cursor: 'pointer', position: 'relative', transition: 'background 0.3s' }}>
                                <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: 'white', position: 'absolute', top: '3px', left: s[t.key] ? '23px' : '3px', transition: 'left 0.3s' }} />
                            </button>
                        </div>
                    ))}
                    <div style={{ padding: '12px 16px', background: '#0f172a', borderRadius: '12px' }}>
                        <label style={label}>Data Retention</label>
                        <select value={s.data_retention} onChange={e => update('data_retention', e.target.value)} style={input}>
                            <option value="7_days">7 Days</option><option value="30_days">30 Days</option><option value="90_days">90 Days</option><option value="forever">Forever</option>
                        </select>
                    </div>
                </div>
            </div>

            <button onClick={save} style={{ ...btn, background: 'linear-gradient(90deg, #3b82f6, #6366f1)', color: 'white', alignSelf: 'flex-start' }}>Save All Settings</button>

            {/* Data Management */}
            <div style={{ ...card, borderColor: 'rgba(239,68,68,0.3)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', margin: '0 0 12px 0', color: '#ef4444' }}>⚠️ Danger Zone</h3>
                <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '16px' }}>Permanently delete all historical traffic data. This cannot be undone.</p>
                <button onClick={purge} style={{ ...btn, background: '#ef4444', color: 'white' }}>Purge All Traffic Data</button>
                {purgeMsg && <p style={{ color: '#f59e0b', fontSize: '13px', marginTop: '8px' }}>{purgeMsg}</p>}
            </div>

            {/* Audit Trail */}
            <div style={card}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', margin: '0 0 16px 0', color: '#e2e8f0' }}>📋 Recent Audit Log</h3>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead><tr style={{ borderBottom: '1px solid #334155' }}>
                        {['Action', 'Details', 'User', 'Time'].map(h => <th key={h} style={{ padding: '10px 12px', textAlign: 'left', color: '#64748b', fontWeight: '500' }}>{h}</th>)}
                    </tr></thead>
                    <tbody>
                        {audit.map(a => (
                            <tr key={a.id} style={{ borderBottom: '1px solid rgba(51,65,85,0.3)' }}>
                                <td style={{ padding: '10px 12px' }}><span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: '#334155', color: '#94a3b8' }}>{a.action}</span></td>
                                <td style={{ padding: '10px 12px', color: '#94a3b8' }}>{a.details}</td>
                                <td style={{ padding: '10px 12px', color: '#60a5fa' }}>{a.user}</td>
                                <td style={{ padding: '10px 12px', color: '#64748b', fontSize: '12px' }}>{a.timestamp}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
