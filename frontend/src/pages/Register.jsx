import { useState } from 'react';
import api from '../api';

const s = {
    wrapper: { display: 'flex', justifycontent: 'center', alignItems: 'center', minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a, #1e293b)', fontFamily: "'Inter', 'Segoe UI', sans-serif", padding: '24px' },
    card: { background: '#1e293b', border: '1px solid #334155', borderRadius: '20px', padding: '40px', width: '100%', maxWidth: '450px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)', margin: '0 auto' },
    title: { fontSize: '28px', fontWeight: 'bold', color: '#f8fafc', margin: '0 0 6px 0', textAlign: 'center' },
    subtitle: { fontSize: '14px', color: '#64748b', textAlign: 'center', marginBottom: '32px' },
    label: { display: 'block', fontSize: '13px', fontWeight: '500', color: '#94a3b8', marginBottom: '6px' },
    input: { width: '100%', padding: '12px 16px', background: '#0f172a', border: '1px solid #334155', borderRadius: '10px', color: '#f1f5f9', fontSize: '15px', outline: 'none', boxSizing: 'border-box', marginBottom: '20px' },
    btn: { width: '100%', padding: '14px', background: 'linear-gradient(90deg, #10b981, #059669)', border: 'none', borderRadius: '12px', color: 'white', fontSize: '16px', fontWeight: '600', cursor: 'pointer', transition: 'all 0.3s' },
    error: { background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '10px', padding: '10px 14px', color: '#ef4444', fontSize: '14px', marginBottom: '16px', textAlign: 'center' },
    success: { background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '10px', padding: '10px 14px', color: '#10b981', fontSize: '14px', marginBottom: '16px', textAlign: 'center' },
    link: { display: 'block', textAlign: 'center', marginTop: '20px', fontSize: '14px', color: '#60a5fa', cursor: 'pointer', textDecoration: 'none' },
};

export default function Register({ onNavigateToLogin }) {
    const [formData, setFormData] = useState({
        username: '', full_name: '', phone_number: '', organization: '', password: '', confirm_password: ''
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            const res = await api.post('/auth/register', formData);
            if (res.data.success) {
                setSuccess('Registration successful! You can now sign in.');
                setFormData({ username: '', full_name: '', phone_number: '', organization: '', password: '', confirm_password: '' });
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={s.wrapper}>
            <div style={s.card}>
                <h1 style={s.title}>Traffic Vision AI</h1>
                <p style={s.subtitle}>Create a new account</p>

                {error && <div style={s.error}>{error}</div>}
                {success && <div style={s.success}>{success}</div>}

                <form onSubmit={handleSubmit}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        <div>
                            <label style={s.label}>Username *</label>
                            <input style={s.input} type="text" value={formData.username} onChange={e => setFormData({ ...formData, username: e.target.value })} required minLength={3} />
                        </div>
                        <div>
                            <label style={s.label}>Full Name *</label>
                            <input style={s.input} type="text" value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })} required />
                        </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        <div>
                            <label style={s.label}>Phone Number</label>
                            <input style={s.input} type="text" value={formData.phone_number} onChange={e => setFormData({ ...formData, phone_number: e.target.value })} />
                        </div>
                        <div>
                            <label style={s.label}>Organization</label>
                            <input style={s.input} type="text" value={formData.organization} onChange={e => setFormData({ ...formData, organization: e.target.value })} />
                        </div>
                    </div>

                    <label style={s.label}>Password * (min 6 chars)</label>
                    <input style={s.input} type="password" value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} required minLength={6} />

                    <label style={s.label}>Confirm Password *</label>
                    <input style={s.input} type="password" value={formData.confirm_password} onChange={e => setFormData({ ...formData, confirm_password: e.target.value })} required minLength={6} />

                    <button style={{ ...s.btn, opacity: loading ? 0.6 : 1 }} type="submit" disabled={loading}>
                        {loading ? 'Creating...' : 'Register'}
                    </button>
                </form>

                <button onClick={onNavigateToLogin} style={{ background: 'none', border: 'none', ...s.link }}>
                    ← Back to Sign In
                </button>
            </div>
        </div>
    );
}
