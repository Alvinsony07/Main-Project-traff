import { useState, useEffect } from 'react';
import api from '../api';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend);

const card = { background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: '20px', padding: '24px' };
const chartOpts = { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } }, x: { grid: { display: false }, ticks: { color: '#64748b' } } } };

export default function Analytics() {
    const [data, setData] = useState(null);
    const [predictions, setPredictions] = useState(null);

    useEffect(() => {
        api.get('/stats').then(r => setData(r.data)).catch(() => { });
        api.get('/predictions').then(r => setPredictions(r.data)).catch(() => { });
    }, []);

    const trendChart = data ? {
        labels: data.trend.map(t => t.time),
        datasets: [{ label: 'Traffic Volume', data: data.trend.map(t => t.count), borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', fill: true, tension: 0.4 }]
    } : null;

    const distChart = data ? {
        labels: Object.keys(data.distribution),
        datasets: [{ data: Object.values(data.distribution), backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'], borderColor: '#0f172a', borderWidth: 2 }]
    } : null;

    const peakChart = data ? {
        labels: Object.keys(data.peak_hours).map(h => `${h}:00`),
        datasets: [{ label: 'Vehicles', data: Object.values(data.peak_hours), backgroundColor: 'rgba(99,102,241,0.6)', borderRadius: 4 }]
    } : null;

    const laneChart = data ? {
        labels: Object.keys(data.lane_performance).map(l => `Lane ${l}`),
        datasets: [{ label: 'Avg Vehicles', data: Object.values(data.lane_performance), backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'], borderRadius: 6 }]
    } : null;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <header>
                <h2 style={{ fontSize: '26px', fontWeight: 'bold', margin: '0 0 4px 0' }}>Analytics & Visualization</h2>
                <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>Deep dive into traffic patterns, vehicle distribution, and AI predictions.</p>
            </header>

            {/* Row 1 */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
                <div style={card}>
                    <h3 style={{ fontSize: '15px', fontWeight: '600', margin: '0 0 16px 0' }}>Traffic Volume Trend</h3>
                    <div style={{ height: '250px' }}>{trendChart ? <Line data={trendChart} options={chartOpts} /> : <p style={{ color: '#64748b' }}>Loading...</p>}</div>
                </div>
                <div style={card}>
                    <h3 style={{ fontSize: '15px', fontWeight: '600', margin: '0 0 16px 0' }}>Vehicle Distribution</h3>
                    <div style={{ height: '250px', display: 'flex', justifyContent: 'center' }}>{distChart ? <Doughnut data={distChart} options={{ ...chartOpts, scales: undefined }} /> : <p style={{ color: '#64748b' }}>Loading...</p>}</div>
                </div>
            </div>

            {/* Row 2 */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div style={card}>
                    <h3 style={{ fontSize: '15px', fontWeight: '600', margin: '0 0 16px 0' }}>Peak Traffic Hours</h3>
                    <div style={{ height: '220px' }}>{peakChart ? <Bar data={peakChart} options={chartOpts} /> : <p style={{ color: '#64748b' }}>Loading...</p>}</div>
                </div>
                <div style={card}>
                    <h3 style={{ fontSize: '15px', fontWeight: '600', margin: '0 0 16px 0' }}>Lane Load Performance</h3>
                    <div style={{ height: '220px' }}>{laneChart ? <Bar data={laneChart} options={chartOpts} /> : <p style={{ color: '#64748b' }}>Loading...</p>}</div>
                </div>
            </div>

            {/* AI Predictions */}
            <div style={card}>
                <h3 style={{ fontSize: '15px', fontWeight: '600', margin: '0 0 16px 0' }}>🤖 AI Congestion Prediction (Next 6 Hours)</h3>
                {predictions ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '12px' }}>
                        {predictions.predictions.map((p, i) => (
                            <div key={i} style={{ background: '#0f172a', borderRadius: '14px', padding: '16px', textAlign: 'center', border: `1px solid ${p.color}30` }}>
                                <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>{p.label}</div>
                                <div style={{ fontSize: '24px', fontWeight: 'bold', color: p.color }}>{p.avg_vehicles}</div>
                                <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '6px' }}>avg vehicles</div>
                                <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '999px', background: `${p.color}20`, color: p.color, fontWeight: '600' }}>{p.level}</span>
                                <div style={{ fontSize: '10px', color: '#475569', marginTop: '6px' }}>Confidence: {p.confidence}%</div>
                            </div>
                        ))}
                    </div>
                ) : <p style={{ color: '#64748b' }}>Loading predictions...</p>}
            </div>
        </div>
    );
}
