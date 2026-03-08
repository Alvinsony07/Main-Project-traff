import { useState } from 'react';
import api from '../api';

const s = {
    wrapper: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'linear-gradient(135deg, #0f172a, #1e293b)', fontFamily: "'Inter', 'Segoe UI', sans-serif" },
    card: { background: '#1e293b', border: '1px solid #334155', borderRadius: '20px', padding: '40px', width: '400px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)' },
    title: { fontSize: '28px', fontWeight: 'bold', color: '#f8fafc', margin: '0 0 6px 0', textAlign: 'center' },
    subtitle: { fontSize: '14px', color: '#64748b', textAlign: 'center', marginBottom: '32px' },
    label: { display: 'block', fontSize: '13px', fontWeight: '500', color: '#94a3b8', marginBottom: '6px' },
    input: { width: '100%', padding: '12px 16px', background: '#0f172a', border: '1px solid #334155', borderRadius: '10px', color: '#f1f5f9', fontSize: '15px', outline: 'none', boxSizing: 'border-box', marginBottom: '20px' },
    btn: { width: '100%', padding: '14px', background: 'linear-gradient(90deg, #3b82f6, #6366f1)', border: 'none', borderRadius: '12px', color: 'white', fontSize: '16px', fontWeight: '600', cursor: 'pointer', transition: 'all 0.3s' },
    error: { background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '10px', padding: '10px 14px', color: '#ef4444', fontSize: '14px', marginBottom: '16px', textAlign: 'center' },
    amb: { display: 'block', textAlign: 'center', marginTop: '20px', fontSize: '13px', color: '#64748b', cursor: 'pointer', textDecoration: 'underline' },
};

export default function Login({ onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const res = await api.post('/auth/login', { username, password });
            if (res.data.success) {
                onLogin(res.data);
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={s.wrapper}>
            <div style={s.card}>
                <h1 style={s.title}>Traffic Vision AI</h1>
                <p style={s.subtitle}>Sign in to access the control panel</p>
                {error && <div style={s.error}>{error}</div>}
                <form onSubmit={handleSubmit}>
                    <label style={s.label}>Username</label>
                    <input style={s.input} type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="admin" autoFocus />
                    <label style={s.label}>Password</label>
                    <input style={s.input} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
                    <button style={{ ...s.btn, opacity: loading ? 0.6 : 1 }} type="submit" disabled={loading}>
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>
                <a style={s.amb} href="/ambulance" target="_blank">Ambulance Driver Portal →</a>
            </div>
        </div>
    );
}
