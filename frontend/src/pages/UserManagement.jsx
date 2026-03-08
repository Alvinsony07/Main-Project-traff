import { useState, useEffect } from 'react';
import api from '../api';

const card = { background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: '20px', padding: '24px' };
const btn = { padding: '8px 16px', borderRadius: '8px', border: 'none', fontSize: '12px', fontWeight: '600', cursor: 'pointer', transition: 'opacity 0.2s' };

export default function UserManagement() {
    const [users, setUsers] = useState([]);
    const [msg, setMsg] = useState('');

    const loadUsers = () => api.get('/users').then(r => setUsers(r.data.users)).catch(() => { });

    useEffect(() => { loadUsers(); }, []);

    const handleUnlock = async (id) => {
        try {
            await api.post(`/users/${id}/unlock`);
            setMsg('User unlocked successfully');
            loadUsers();
            setTimeout(() => setMsg(''), 3000);
        } catch (e) { setMsg('Failed to unlock user'); }
    };

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this user? This cannot be undone.')) return;
        try {
            await api.delete(`/users/${id}`);
            setMsg('User deleted');
            loadUsers();
            setTimeout(() => setMsg(''), 3000);
        } catch (e) { setMsg('Failed to delete user: ' + (e.response?.data?.detail || e.message)); }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <header>
                <h2 style={{ fontSize: '26px', fontWeight: 'bold', margin: '0 0 4px 0' }}>User Management</h2>
                <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>Manage system access, unlock accounts, and view user details.</p>
            </header>

            {msg && (
                <div style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '10px', padding: '12px', color: '#60a5fa', fontSize: '14px', textAlign: 'center' }}>
                    {msg}
                </div>
            )}

            <div style={{ ...card, padding: 0, overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                    <thead>
                        <tr style={{ background: '#1e293b' }}>
                            {['User', 'Role', 'Status', 'Contact', 'Joined', 'Actions'].map(h => (
                                <th key={h} style={{ padding: '14px 16px', textAlign: 'left', color: '#94a3b8', fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {users.length === 0 ? (
                            <tr><td colSpan={6} style={{ padding: '48px', textAlign: 'center', color: '#64748b' }}>Loading users...</td></tr>
                        ) : users.map((u, i) => (
                            <tr key={u.id} style={{ borderBottom: '1px solid rgba(51,65,85,0.3)', background: i % 2 === 0 ? 'transparent' : 'rgba(15,23,42,0.3)' }}>
                                <td style={{ padding: '14px 16px' }}>
                                    <div style={{ fontWeight: '600', color: '#f1f5f9' }}>{u.username}</div>
                                    <div style={{ fontSize: '12px', color: '#64748b' }}>{u.full_name || 'No full name'}</div>
                                </td>
                                <td style={{ padding: '14px 16px' }}>
                                    <span style={{ fontSize: '11px', padding: '4px 10px', borderRadius: '999px', fontWeight: '600', background: u.role === 'admin' ? 'rgba(239,68,68,0.2)' : 'rgba(59,130,246,0.2)', color: u.role === 'admin' ? '#ef4444' : '#60a5fa', textTransform: 'uppercase' }}>
                                        {u.role}
                                    </span>
                                </td>
                                <td style={{ padding: '14px 16px' }}>
                                    {u.is_locked ? (
                                        <span style={{ fontSize: '12px', color: '#ef4444', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '4px' }}>🔒 Locked</span>
                                    ) : (
                                        <span style={{ fontSize: '12px', color: '#10b981', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '4px' }}>✓ Active</span>
                                    )}
                                </td>
                                <td style={{ padding: '14px 16px', color: '#94a3b8', fontSize: '13px' }}>
                                    <div>{u.phone_number || '-'}</div>
                                    <div style={{ fontSize: '11px', color: '#64748b' }}>{u.organization || '-'}</div>
                                </td>
                                <td style={{ padding: '14px 16px', color: '#64748b', fontSize: '13px' }}>{u.created_at}</td>
                                <td style={{ padding: '14px 16px' }}>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        {u.is_locked && (
                                            <button onClick={() => handleUnlock(u.id)} style={{ ...btn, background: 'rgba(245,158,11,0.2)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.3)' }} onMouseOver={e => e.target.style.opacity = 0.8} onMouseOut={e => e.target.style.opacity = 1}>
                                                Unlock
                                            </button>
                                        )}
                                        {u.role !== 'admin' && (
                                            <button onClick={() => handleDelete(u.id)} style={{ ...btn, background: 'rgba(239,68,68,0.2)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }} onMouseOver={e => e.target.style.opacity = 0.8} onMouseOut={e => e.target.style.opacity = 1}>
                                                Delete
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
