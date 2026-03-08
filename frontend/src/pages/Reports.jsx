import { useState, useEffect } from 'react';
import api, { API_BASE } from '../api';

const card = { background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: '20px', padding: '24px' };
const input = { padding: '10px 14px', background: '#0f172a', border: '1px solid #334155', borderRadius: '10px', color: '#f1f5f9', fontSize: '14px', outline: 'none' };
const btn = { padding: '10px 20px', borderRadius: '10px', border: 'none', fontSize: '13px', fontWeight: '600', cursor: 'pointer' };
const dColors = { Low: '#10b981', Medium: '#f59e0b', High: '#ef4444' };

export default function Reports() {
    const [records, setRecords] = useState([]);
    const [meta, setMeta] = useState({});
    const [page, setPage] = useState(1);
    const [filters, setFilters] = useState({ lane: '', density: '', date: '' });

    const load = (p = page) => {
        const params = new URLSearchParams({ page: p, per_page: 20 });
        if (filters.lane) params.set('lane', filters.lane);
        if (filters.density) params.set('density', filters.density);
        if (filters.date) params.set('date', filters.date);
        api.get(`/reports_data?${params}`).then(r => { setRecords(r.data.records); setMeta(r.data); }).catch(() => { });
    };

    useEffect(() => { load(1); setPage(1); }, [filters]);

    const changePage = (p) => { setPage(p); load(p); };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '26px', fontWeight: 'bold', margin: '0 0 4px 0' }}>Traffic Reports</h2>
                    <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>View, filter, and export historical traffic data.</p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <a href={`${API_BASE}/export_stats`} target="_blank" style={{ ...btn, background: '#10b981', color: 'white', textDecoration: 'none' }}>Export CSV</a>
                    <a href={`${API_BASE}/generate_pdf`} target="_blank" style={{ ...btn, background: '#3b82f6', color: 'white', textDecoration: 'none' }}>Generate PDF</a>
                </div>
            </header>

            {/* Filters */}
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                <select value={filters.lane} onChange={e => setFilters({ ...filters, lane: e.target.value })} style={{ ...input, minWidth: '120px' }}>
                    <option value="">All Lanes</option>
                    <option value="1">Lane 1</option><option value="2">Lane 2</option><option value="3">Lane 3</option><option value="4">Lane 4</option>
                </select>
                <select value={filters.density} onChange={e => setFilters({ ...filters, density: e.target.value })} style={{ ...input, minWidth: '120px' }}>
                    <option value="">All Density</option>
                    <option value="Low">Low</option><option value="Medium">Medium</option><option value="High">High</option>
                </select>
                <input type="date" value={filters.date} onChange={e => setFilters({ ...filters, date: e.target.value })} style={input} />
                <button onClick={() => setFilters({ lane: '', density: '', date: '' })} style={{ ...btn, background: '#334155', color: '#94a3b8' }}>Clear</button>
                <span style={{ fontSize: '13px', color: '#64748b', marginLeft: 'auto' }}>{meta.total || 0} records found</span>
            </div>

            {/* Table */}
            <div style={{ ...card, padding: 0, overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                    <thead>
                        <tr style={{ background: '#1e293b' }}>
                            {['ID', 'Lane', 'Vehicles', 'Density', 'Timestamp'].map(h => (
                                <th key={h} style={{ padding: '14px 16px', textAlign: 'left', color: '#94a3b8', fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {records.length === 0 ? (
                            <tr><td colSpan={5} style={{ padding: '48px', textAlign: 'center', color: '#64748b' }}>No data available. Start video streams from Camera Config to begin collecting data.</td></tr>
                        ) : records.map(r => (
                            <tr key={r.id} style={{ borderBottom: '1px solid rgba(51,65,85,0.3)' }}>
                                <td style={{ padding: '12px 16px', color: '#94a3b8' }}>#{r.id}</td>
                                <td style={{ padding: '12px 16px' }}>Lane {r.lane_id}</td>
                                <td style={{ padding: '12px 16px', fontWeight: '600' }}>{r.vehicle_count}</td>
                                <td style={{ padding: '12px 16px' }}><span style={{ fontSize: '12px', padding: '2px 10px', borderRadius: '999px', background: `${dColors[r.density]}20`, color: dColors[r.density], fontWeight: '600' }}>{r.density}</span></td>
                                <td style={{ padding: '12px 16px', color: '#94a3b8', fontSize: '13px' }}>{r.timestamp}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            {meta.pages > 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', gap: '4px' }}>
                    <button disabled={!meta.has_prev} onClick={() => changePage(page - 1)} style={{ ...btn, background: '#334155', color: '#94a3b8', opacity: meta.has_prev ? 1 : 0.4 }}>← Prev</button>
                    <span style={{ padding: '10px 16px', fontSize: '13px', color: '#94a3b8' }}>Page {meta.current_page} of {meta.pages}</span>
                    <button disabled={!meta.has_next} onClick={() => changePage(page + 1)} style={{ ...btn, background: '#334155', color: '#94a3b8', opacity: meta.has_next ? 1 : 0.4 }}>Next →</button>
                </div>
            )}
        </div>
    );
}
