export default function Settings() {
    return (
        <div>
            <h2 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '8px' }}>System Settings</h2>
            <p style={{ color: '#94a3b8', fontSize: '15px', marginBottom: '24px' }}>Configure AI models, camera inputs, and system preferences.</p>
            <div style={{ background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: '24px', padding: '32px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    <div>
                        <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#cbd5e1', marginBottom: '8px' }}>Min Green Time (s)</label>
                        <input type="number" defaultValue={10} style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '12px', padding: '12px 16px', color: '#f1f5f9', fontSize: '15px', outline: 'none' }} />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#cbd5e1', marginBottom: '8px' }}>Max Green Time (s)</label>
                        <input type="number" defaultValue={120} style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '12px', padding: '12px 16px', color: '#f1f5f9', fontSize: '15px', outline: 'none' }} />
                    </div>
                </div>
                <button style={{ marginTop: '24px', background: '#3b82f6', color: 'white', border: 'none', padding: '12px 24px', borderRadius: '12px', fontSize: '15px', fontWeight: '500', cursor: 'pointer' }}>
                    Save Changes
                </button>
            </div>
        </div>
    );
}
