import { useState, useRef } from 'react';
import api from '../api';

const card = { background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: '20px', padding: '28px' };
const btn = { padding: '12px 24px', borderRadius: '10px', border: 'none', fontSize: '14px', fontWeight: '600', cursor: 'pointer' };

export default function CameraConfig() {
    const [sources, setSources] = useState(['', '', '', '']);
    const [files, setFiles] = useState([null, null, null, null]);
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(false);
    const fileRefs = [useRef(), useRef(), useRef(), useRef()];

    const updateSource = (i, val) => {
        const updated = [...sources];
        updated[i] = val;
        setSources(updated);
    };

    const updateFile = (i, file) => {
        const updated = [...files];
        updated[i] = file;
        setFiles(updated);
    };

    const handleSubmit = async () => {
        setLoading(true);
        setStatus('');
        const formData = new FormData();
        sources.forEach((s, i) => formData.append(`cam_${i + 1}`, s));
        files.forEach((f, i) => {
            if (f) formData.append(`video_${i + 1}`, f);
        });

        try {
            const res = await api.post('/setup_streams', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            if (res.data.success) {
                setStatus('Streams started successfully! Go to Dashboard to view feeds.');
            }
        } catch (e) {
            setStatus('Failed to start streams: ' + (e.response?.data?.detail || e.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <header>
                <h2 style={{ fontSize: '26px', fontWeight: 'bold', margin: '0 0 4px 0' }}>Camera Configuration</h2>
                <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>Configure video sources for each lane. You can use uploaded videos, RTSP streams, or webcam indices.</p>
            </header>

            {status && (
                <div style={{
                    background: status.includes('success') ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                    border: `1px solid ${status.includes('success') ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
                    borderRadius: '10px', padding: '12px', fontSize: '14px', textAlign: 'center',
                    color: status.includes('success') ? '#10b981' : '#ef4444'
                }}>{status}</div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                {[0, 1, 2, 3].map(i => (
                    <div key={i} style={card}>
                        <h3 style={{ fontSize: '16px', fontWeight: '600', margin: '0 0 16px 0', color: '#e2e8f0' }}>
                            <span style={{ color: '#3b82f6' }}>Lane {i + 1}</span>
                        </h3>

                        <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>Camera URL / Webcam Index</label>
                        <input
                            type="text"
                            value={sources[i]}
                            onChange={e => updateSource(i, e.target.value)}
                            placeholder="rtsp://... or 0 for webcam"
                            style={{ width: '100%', padding: '10px 14px', background: '#0f172a', border: '1px solid #334155', borderRadius: '10px', color: '#f1f5f9', fontSize: '14px', outline: 'none', boxSizing: 'border-box', marginBottom: '12px' }}
                        />

                        <label style={{ display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>Or Upload Video File</label>
                        <input
                            type="file"
                            ref={fileRefs[i]}
                            accept=".mp4,.avi,.mov,.mkv,.webm"
                            onChange={e => updateFile(i, e.target.files[0])}
                            style={{ display: 'none' }}
                        />
                        <button
                            onClick={() => fileRefs[i].current?.click()}
                            style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '2px dashed #334155', background: 'transparent', color: '#94a3b8', cursor: 'pointer', fontSize: '14px' }}
                        >
                            {files[i] ? `📁 ${files[i].name}` : 'Click to select video file'}
                        </button>
                    </div>
                ))}
            </div>

            <button
                onClick={handleSubmit}
                disabled={loading}
                style={{ ...btn, background: 'linear-gradient(90deg, #3b82f6, #6366f1)', color: 'white', alignSelf: 'flex-start', opacity: loading ? 0.6 : 1 }}
            >
                {loading ? 'Starting Streams...' : '🚀 Start All Streams'}
            </button>
        </div>
    );
}
