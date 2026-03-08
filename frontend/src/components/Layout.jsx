import { Link, Outlet, useLocation } from 'react-router-dom';
import { LayoutDashboard, BarChart3, Settings as SettingsIcon, FileText } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Layout() {
    const location = useLocation();

    const links = [
        { name: 'Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'Analytics', path: '/analytics', icon: BarChart3 },
        { name: 'Reports', path: '/reports', icon: FileText },
        { name: 'Settings', path: '/settings', icon: SettingsIcon },
    ];

    return (
        <div className="flex h-screen bg-slate-950 text-slate-50 font-sans overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
                <div className="p-6">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
                        Traffic Vision AI
                    </h1>
                </div>
                <nav className="flex-1 px-4 space-y-2 mt-4">
                    {links.map((link) => {
                        const isActive = location.pathname === link.path;
                        const Icon = link.icon;
                        return (
                            <Link key={link.name} to={link.path} className="relative block">
                                {isActive && (
                                    <motion.div
                                        layoutId="active-nav-bg"
                                        className="absolute inset-0 bg-blue-600/20 rounded-xl"
                                        initial={false}
                                        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                                    />
                                )}
                                <div
                                    className={`relative flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${isActive ? 'text-blue-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                                        }`}
                                >
                                    <Icon className="w-5 h-5" />
                                    <span className="font-medium">{link.name}</span>
                                </div>
                            </Link>
                        );
                    })}
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950">
                <div className="p-8 max-w-7xl mx-auto h-full">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
