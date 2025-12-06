import React, { useState } from 'react';
import { Menu, Search, Home, Calculator, Settings, Github, BookOpen } from 'lucide-react';

interface LayoutProps {
    children: React.ReactNode;
    activePage: string;
    onNavigate: (page: string) => void;
}

export function Layout({ children, activePage, onNavigate }: LayoutProps) {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    return (
        <div className="min-h-screen bg-navy-900 text-gray-100 flex">
            {/* Sidebar */}
            <aside
                className={`${isSidebarOpen ? 'w-64' : 'w-16'
                    } bg-navy-900 border-r border-navy-700 transition-all duration-300 flex flex-col fixed h-full z-20`}
            >
                <div className="p-4 flex items-center justify-center border-b border-navy-700 h-16">
                    <span className={`font-bold text-xl text-white ${!isSidebarOpen && 'hidden'}`}>
                        Automata
                    </span>
                    <span className={`font-bold text-xl text-white ${isSidebarOpen && 'hidden'}`}>
                        A
                    </span>
                </div>

                <div className="p-4">
                    <div className={`bg-navy-800 rounded-md flex items-center px-3 py-2 border border-navy-700 ${!isSidebarOpen && 'justify-center px-0'}`}>
                        <Search size={18} className="text-gray-400" />
                        {isSidebarOpen && (
                            <input
                                type="text"
                                placeholder="Search algorithms..."
                                className="bg-transparent border-none outline-none text-sm ml-2 text-gray-200 w-full placeholder-gray-500"
                            />
                        )}
                    </div>
                </div>

                <nav className="flex-1 overflow-y-auto py-2">
                    <SidebarItem
                        icon={<Home size={20} />}
                        label="Home"
                        isOpen={isSidebarOpen}
                        active={activePage === 'home'}
                        onClick={() => onNavigate('home')}
                    />
                    <SidebarItem
                        icon={<Calculator size={20} />}
                        label="Regex to NFA/DFA"
                        isOpen={isSidebarOpen}
                        active={activePage === 'converter'}
                        onClick={() => onNavigate('converter')}
                    />
                    <SidebarItem
                        icon={<BookOpen size={20} />}
                        label="Documentation"
                        isOpen={isSidebarOpen}
                        active={activePage === 'docs'}
                        onClick={() => onNavigate('docs')}
                    />
                    <SidebarItem
                        icon={<Github size={20} />}
                        label="Source Code"
                        isOpen={isSidebarOpen}
                        onClick={() => window.open('https://github.com/ilyarjan1/Regex-to-NFA-DFA', '_blank')}
                    />
                </nav>

                <div className="p-4 border-t border-navy-700">
                    <SidebarItem icon={<Settings size={20} />} label="Settings" isOpen={isSidebarOpen} />
                </div>
            </aside>

            {/* Main Content */}
            <div className={`flex-1 flex flex-col transition-all duration-300 ${isSidebarOpen ? 'ml-64' : 'ml-16'}`}>
                {/* Header */}
                <header className="h-16 bg-navy-900 border-b border-navy-700 flex items-center justify-between px-6 sticky top-0 z-10">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                            className="text-gray-400 hover:text-white transition-colors"
                        >
                            <Menu size={24} />
                        </button>
                        <h1 className="text-xl font-semibold text-white">Regex To NFA/DFA Converter</h1>
                    </div>

                    <div className="flex items-center gap-4">
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 p-6 overflow-hidden">
                    {children}
                </main>
            </div>
        </div>
    );
}

function SidebarItem({ icon, label, isOpen, active, onClick }: { icon: React.ReactNode, label: string, isOpen: boolean, active?: boolean, onClick?: () => void }) {
    return (
        <div
            onClick={onClick}
            className={`flex items-center px-4 py-3 cursor-pointer transition-colors ${active ? 'text-accent-500 border-r-2 border-accent-500 bg-navy-800/50' : 'text-gray-400 hover:text-white hover:bg-navy-800'}`}
        >
            <div className="min-w-[20px]">{icon}</div>
            {isOpen && <span className="ml-3 text-sm font-medium whitespace-nowrap">{label}</span>}
        </div>
    );
}
