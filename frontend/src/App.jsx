import { useState, useEffect } from 'react';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import UserDashboard from './pages/UserDashboard';
import Analytics from './pages/Analytics';
import CityOverview from './pages/CityOverview';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import CameraConfig from './pages/CameraConfig';
import AmbulancePortal from './pages/AmbulancePortal';
import UserManagement from './pages/UserManagement';

const navItems = [
    { name: 'Dashboard', id: 'dashboard', adminOnly: true },
    { name: 'My Dashboard', id: 'user_dashboard', userOnly: true },
    { name: 'Analytics', id: 'analytics' },
    { name: 'City Overview', id: 'city_overview' },
    { name: 'Reports', id: 'reports' },
    { name: 'Camera Config', id: 'camera_config', adminOnly: true },
    { name: 'User Management', id: 'user_mgmt', adminOnly: true },
    { name: 'Settings', id: 'settings', adminOnly: true },
];

export default function App() {
    const [activePage, setActivePage] = useState('dashboard');
    const [user, setUser] = useState(null);
    const [showRegister, setShowRegister] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('token');
        const username = localStorage.getItem('username');
        const role = localStorage.getItem('role');
        if (token && username) {
            setUser({ username, role, token });
            setActivePage(role === 'admin' ? 'dashboard' : 'user_dashboard');
        }
    }, []);

    const handleLogin = (userData) => {
        localStorage.setItem('token', userData.token);
        localStorage.setItem('username', userData.username);
        localStorage.setItem('role', userData.role);
        setUser(userData);
        setActivePage(userData.role === 'admin' ? 'dashboard' : 'user_dashboard');
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        localStorage.removeItem('role');
        setUser(null);
    };

    // Ambulance portal is a standalone page (no auth needed)
    if (window.location.pathname === '/ambulance') {
        return <AmbulancePortal />;
    }

    if (!user) {
        if (showRegister) {
            return <Register onNavigateToLogin={() => setShowRegister(false)} />;
        }
        return (
            <div style={{ position: 'relative' }}>
                <Login onLogin={handleLogin} />
                <div style={{ position: 'absolute', bottom: '40px', width: '100%', textAlign: 'center' }}>
                    <span style={{ color: '#94a3b8', fontSize: '14px' }}>Don't have an account? </span>
                    <button onClick={() => setShowRegister(true)} style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', fontSize: '14px', textDecoration: 'underline' }}>Sign up here</button>
                </div>
            </div>
        );
    }

    const renderPage = () => {
        switch (activePage) {
            case 'user_dashboard': return <UserDashboard user={user} />;
            case 'analytics': return <Analytics />;
            case 'city_overview': return <CityOverview />;
            case 'reports': return <Reports />;
            case 'camera_config': return <CameraConfig />;
            case 'user_mgmt': return <UserManagement />;
            case 'settings': return <Settings />;
            default: return <Dashboard />;
        }
    };

    const filteredNav = navItems.filter(item => {
        if (item.adminOnly && user.role !== 'admin') return false;
        if (item.userOnly && user.role === 'admin') return false;
        return true;
    });

    return (
        <div style={{ display: 'flex', height: '100vh', background: '#0f172a', color: '#f8fafc', fontFamily: "'Inter', 'Segoe UI', sans-serif", overflow: 'hidden' }}>
            {/* Sidebar */}
            <aside style={{ width: '260px', background: '#1e293b', borderRight: '1px solid #334155', display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '24px' }}>
                    <h1 style={{ fontSize: '20px', fontWeight: 'bold', background: 'linear-gradient(90deg, #60a5fa, #818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', margin: 0 }}>
                        Traffic Vision AI
                    </h1>
                </div>
                <nav style={{ flex: 1, padding: '0 12px' }}>
                    {filteredNav.map((item) => {
                        const isActive = activePage === item.id;
                        return (
                            <button
                                key={item.id}
                                onClick={() => setActivePage(item.id)}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: '12px',
                                    width: '100%', padding: '11px 16px', marginBottom: '2px',
                                    borderRadius: '10px', border: 'none', cursor: 'pointer',
                                    fontSize: '14px', fontWeight: '500', textAlign: 'left',
                                    background: isActive ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                                    color: isActive ? '#60a5fa' : '#94a3b8',
                                    transition: 'all 0.2s',
                                }}
                                onMouseEnter={(e) => { if (!isActive) { e.target.style.background = 'rgba(51, 65, 85, 0.5)'; e.target.style.color = '#e2e8f0'; } }}
                                onMouseLeave={(e) => { if (!isActive) { e.target.style.background = 'transparent'; e.target.style.color = '#94a3b8'; } }}
                            >
                                {item.name}
                            </button>
                        );
                    })}
                </nav>

                {/* User info + Logout */}
                <div style={{ padding: '16px', borderTop: '1px solid #334155' }}>
                    <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '8px' }}>
                        Logged in as <span style={{ color: '#e2e8f0', fontWeight: '600' }}>{user.username}</span>
                        <span style={{ fontSize: '11px', color: '#60a5fa', marginLeft: '6px', textTransform: 'uppercase' }}>{user.role}</span>
                    </div>
                    <button onClick={handleLogout} style={{
                        width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #475569',
                        background: 'transparent', color: '#ef4444', fontSize: '13px', cursor: 'pointer',
                        fontWeight: '500', transition: 'all 0.2s',
                    }}>
                        Logout
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main style={{ flex: 1, overflowY: 'auto', padding: '28px', background: 'radial-gradient(ellipse at top, #1e293b 0%, #0f172a 60%)' }}>
                <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
                    {renderPage()}
                </div>
            </main>
        </div>
    );
}
