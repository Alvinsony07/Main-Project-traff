import { useState, useEffect } from 'react';

function StatCard({ title, value, color, delay }) {
    const [visible, setVisible] = useState(false);
    useEffect(() => {
        const t = setTimeout(() => setVisible(true), delay);
        return () => clearTimeout(t);
    }, [delay]);

    return (
        <div style={{
            background: 'rgba(30, 41, 59, 0.6)', backdropFilter: 'blur(12px)',
            border: '1px solid rgba(51, 65, 85, 0.5)', padding: '24px', borderRadius: '16px',
            position: 'relative', overflow: 'hidden',
            opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(20px)',
            transition: 'opacity 0.5s, transform 0.5s',
        }}>
            <div style={{ position: 'absolute', right: '-24px', top: '-24px', width: '96px', height: '96px', background: `${color}15`, borderRadius: '50%', filter: 'blur(24px)' }} />
            <h3 style={{ color: '#94a3b8', fontWeight: '500', fontSize: '14px', marginBottom: '12px' }}>{title}</h3>
            <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#f1f5f9' }}>{value}</div>
        </div>
    );
}

function VideoFeed({ laneId }) {
    return (
        <div style={{
            position: 'relative', borderRadius: '16px', overflow: 'hidden',
            border: '1px solid rgba(51, 65, 85, 0.5)', background: '#0f172a',
            aspectRatio: '16/9', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
        }}>
            <img
                src={`http://localhost:8000/api/video_feed/${laneId}`}
                alt={`Lane ${laneId} Feed`}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                crossOrigin="anonymous"
            />
            <div style={{
                position: 'absolute', top: '12px', left: '12px',
                background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)',
                padding: '4px 12px', borderRadius: '999px', fontSize: '13px',
                fontWeight: '500', border: '1px solid rgba(255,255,255,0.1)',
                display: 'flex', alignItems: 'center', gap: '8px',
            }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444', animation: 'pulse 2s infinite' }} />
                Lane {laneId}
            </div>
        </div>
    );
}

export default function Dashboard() {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <style>{`@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.4 } }`}</style>

            {/* Header */}
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '28px', fontWeight: 'bold', letterSpacing: '-0.5px', marginBottom: '4px' }}>Live Dashboard</h2>
                    <p style={{ color: '#94a3b8', fontSize: '15px' }}>Real-time traffic monitoring and incident detection</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ position: 'relative', display: 'inline-flex', width: '12px', height: '12px' }}>
                        <span style={{ position: 'absolute', inset: 0, borderRadius: '50%', background: '#34d399', opacity: 0.75, animation: 'pulse 2s infinite' }}></span>
                        <span style={{ position: 'relative', display: 'inline-flex', width: '12px', height: '12px', borderRadius: '50%', background: '#10b981' }}></span>
                    </span>
                    <span style={{ color: '#34d399', fontWeight: '500', fontSize: '13px', letterSpacing: '0.5px' }}>SYSTEM ACTIVE</span>
                </div>
            </header>

            {/* Stats Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
                <StatCard title="Active Cameras" value="4" color="#3b82f6" delay={100} />
                <StatCard title="Total Vehicles" value="0" color="#10b981" delay={200} />
                <StatCard title="Active Incidents" value="0" color="#f97316" delay={300} />
                <StatCard title="Ambulance Active" value="0" color="#ef4444" delay={400} />
            </div>

            {/* Video Feeds */}
            <div style={{
                background: 'rgba(30, 41, 59, 0.3)', backdropFilter: 'blur(8px)',
                border: '1px solid rgba(51, 65, 85, 0.5)', borderRadius: '24px', padding: '24px',
            }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    <VideoFeed laneId={1} />
                    <VideoFeed laneId={2} />
                    <VideoFeed laneId={3} />
                    <VideoFeed laneId={4} />
                </div>
            </div>
        </div>
    );
}
