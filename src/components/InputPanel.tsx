import React from 'react';

interface InputPanelProps {
    regex: string;
    setRegex: (val: string) => void;
    onParse: () => void;
    error: string | null;
}

export function InputPanel({ regex, setRegex, onParse, error }: InputPanelProps) {
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            onParse();
        }
    };

    return (
        <div className="bg-navy-800 rounded-lg p-6 border border-navy-700 h-full flex flex-col">
            <h2 className="text-lg font-semibold text-white mb-6">Question</h2>

            <div className="flex-1">
                <label htmlFor="regex" className="block text-sm font-medium text-gray-300 mb-2">
                    Enter Regex
                </label>
                <p className="text-xs text-gray-500 mb-3">
                    Supported grammars : (s), st, s|t, s*, s+, s?, ε
                </p>

                <div className="relative h-48">
                    <textarea
                        id="regex"
                        className={`w-full h-full bg-navy-900 border ${error ? 'border-red-500' : 'border-navy-700'
                            } rounded-md p-4 text-white placeholder-gray-600 outline-none focus:border-accent-500 resize-none font-mono text-lg`}
                        placeholder="(a+b)*"
                        value={regex}
                        onChange={(e) => setRegex(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                    {error && (
                        <div className="absolute bottom-4 left-4 text-red-400 text-sm">
                            Error: {error}
                        </div>
                    )}
                </div>
            </div>

            <div className="mt-6">
                <button
                    onClick={onParse}
                    className="bg-accent-600 hover:bg-accent-500 text-white px-6 py-2 rounded-md font-medium transition-colors shadow-lg shadow-accent-600/20"
                >
                    Start
                </button>
            </div>
        </div>
    );
}
