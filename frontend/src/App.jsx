import { useState, useEffect } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import CityOverview from './pages/CityOverview';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import CameraConfig from './pages/CameraConfig';
import AmbulancePortal from './pages/AmbulancePortal';

const navItems = [
    { name: 'Dashboard', id: 'dashboard' },
    { name: 'Analytics', id: 'analytics' },
    { name: 'City Overview', id: 'city_overview' },
    { name: 'Reports', id: 'reports' },
    { name: 'Camera Config', id: 'camera_config', adminOnly: true },
    { name: 'Settings', id: 'settings', adminOnly: true },
];

export default function App() {
    const [activePage, setActivePage] = useState('dashboard');
    const [user, setUser] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('token');
        const username = localStorage.getItem('username');
        const role = localStorage.getItem('role');
        if (token && username) {
            setUser({ username, role, token });
        }
    }, []);

    const handleLogin = (userData) => {
        localStorage.setItem('token', userData.token);
        localStorage.setItem('username', userData.username);
        localStorage.setItem('role', userData.role);
        setUser(userData);
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
        return <Login onLogin={handleLogin} />;
    }

    const renderPage = () => {
        switch (activePage) {
            case 'analytics': return <Analytics />;
            case 'city_overview': return <CityOverview />;
            case 'reports': return <Reports />;
            case 'camera_config': return <CameraConfig />;
            case 'settings': return <Settings />;
            default: return <Dashboard />;
        }
    };

    const filteredNav = navItems.filter(item => !item.adminOnly || user.role === 'admin');

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