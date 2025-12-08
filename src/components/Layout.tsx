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
        <div className="min-h-screen bg-navy-900 text-gray-100 flex flex-col md:flex-row">
            {/* Sidebar (Desktop) */}
            <aside
                className={`hidden md:flex ${isSidebarOpen ? 'w-64' : 'w-16'
                    } bg-navy-900 border-r border-navy-700 transition-all duration-300 flex-col fixed h-full z-20`}
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
                                placeholder="Search..."
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
                        label="Converter"
                        isOpen={isSidebarOpen}
                        active={activePage === 'converter'}
                        onClick={() => onNavigate('converter')}
                    />
                    <SidebarItem
                        icon={<BookOpen size={20} />}
                        label="Docs"
                        isOpen={isSidebarOpen}
                        active={activePage === 'docs'}
                        onClick={() => onNavigate('docs')}
                    />
                    <SidebarItem
                        icon={<Github size={20} />}
                        label="Source"
                        isOpen={isSidebarOpen}
                        onClick={() => window.open('https://github.com/ilyarjan1/Regex-to-NFA-DFA', '_blank')}
                    />
                </nav>

                <div className="p-4 border-t border-navy-700">
                    <SidebarItem icon={<Settings size={20} />} label="Settings" isOpen={isSidebarOpen} />
                </div>
            </aside>

            {/* Mobile Bottom Navigation */}
            <nav className="md:hidden fixed bottom-0 w-full bg-navy-900 border-t border-navy-700 z-50 flex justify-around items-center h-16 px-2">
                <MobileNavItem
                    icon={<Home size={24} />}
                    label="Home"
                    active={activePage === 'home'}
                    onClick={() => onNavigate('home')}
                />
                <MobileNavItem
                    icon={<Calculator size={24} />}
                    label="Converter"
                    active={activePage === 'converter'}
                    onClick={() => onNavigate('converter')}
                />
                <MobileNavItem
                    icon={<BookOpen size={24} />}
                    label="Docs"
                    active={activePage === 'docs'}
                    onClick={() => onNavigate('docs')}
                />
            </nav>

            {/* Main Content */}
            <div className={`flex-1 flex flex-col transition-all duration-300 ml-0 ${isSidebarOpen ? 'md:ml-64' : 'md:ml-16'} mb-16 md:mb-0`}>
                {/* Header */}
                <header className="h-16 bg-navy-900 border-b border-navy-700 flex items-center justify-between px-4 md:px-6 sticky top-0 z-10">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                            className="text-gray-400 hover:text-white transition-colors hidden md:block"
                        >
                            <Menu size={24} />
                        </button>
                        <h1 className="text-lg md:text-xl font-semibold text-white truncate">Regex To NFA/DFA</h1>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 p-4 md:p-6 overflow-x-hidden overflow-y-auto">
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

function MobileNavItem({ icon, label, active, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) {
    return (
        <button
            onClick={onClick}
            className={`flex flex-col items-center justify-center w-full h-full ${active ? 'text-accent-500' : 'text-gray-400'}`}
        >
            {icon}
            <span className="text-[10px] mt-1 font-medium">{label}</span>
        </button>
    );
}
