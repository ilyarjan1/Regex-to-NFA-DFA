
import type { NFA } from '../lib/automata/nfa';
import type { DFA } from '../lib/automata/dfa';

interface TransitionTableProps {
    nfa: NFA | null;
    dfa: DFA | null;
    mode: 'NFA' | 'DFA';
}

export function TransitionTable({ nfa, dfa, mode }: TransitionTableProps) {
    if (!nfa && !dfa) return null;

    // Get all unique symbols from transitions
    const getSymbols = (): string[] => {
        const symbols = new Set<string>();
        if (mode === 'NFA' && nfa) {
            nfa.states.forEach(s => {
                s.transitions.forEach(t => {
                    if (t.symbol !== null) symbols.add(t.symbol);
                });
            });
            // NFA always has epsilon, but we might want to show it explicitly or not.
            // Usually transition tables show input symbols. Epsilon is a special case.
            // Let's include epsilon column if there are epsilon transitions.
            const hasEpsilon = nfa.states.some(s => s.transitions.some(t => t.symbol === null));
            if (hasEpsilon) symbols.add('ε');
        } else if (mode === 'DFA' && dfa) {
            dfa.states.forEach(s => {
                Object.keys(s.transitions).forEach(sym => symbols.add(sym));
            });
        }
        return Array.from(symbols).sort();
    };

    const symbols = getSymbols();

    return (
        <div className="bg-navy-800 rounded-lg border border-navy-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-navy-700 bg-navy-900/50">
                <h3 className="text-lg font-semibold text-white">Transition Table</h3>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left text-gray-300">
                    <thead className="text-xs text-gray-400 uppercase bg-navy-900">
                        <tr>
                            <th scope="col" className="px-6 py-3 border-b border-navy-700">State</th>
                            <th scope="col" className="px-6 py-3 border-b border-navy-700">Type</th>
                            {symbols.map(symbol => (
                                <th key={symbol} scope="col" className="px-6 py-3 border-b border-navy-700">{symbol}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {mode === 'NFA' && nfa?.states.map((state) => (
                            <tr key={state.id} className="bg-navy-800 border-b border-navy-700 hover:bg-navy-700/50 transition-colors">
                                <td className="px-6 py-4 font-medium text-white whitespace-nowrap">
                                    {state.label || state.id}
                                </td>
                                <td className="px-6 py-4">
                                    {state.isAccepting ? <span className="text-accent-400 font-bold">Accept</span> :
                                        state.id === nfa.start.id ? <span className="text-secondary-500 font-bold">Start</span> : '-'}
                                </td>
                                {symbols.map(symbol => {
                                    const targets = state.transitions
                                        .filter(t => (t.symbol === null ? 'ε' : t.symbol) === symbol)
                                        .map(t => t.to.label || t.to.id);

                                    return (
                                        <td key={symbol} className="px-6 py-4">
                                            {targets.length > 0 ? `{${targets.join(', ')}}` : '-'}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}

                        {mode === 'DFA' && dfa?.states.map((state) => (
                            <tr key={state.id} className="bg-navy-800 border-b border-navy-700 hover:bg-navy-700/50 transition-colors">
                                <td className="px-6 py-4 font-medium text-white whitespace-nowrap">
                                    {state.label || state.id}
                                </td>
                                <td className="px-6 py-4">
                                    {state.isAccepting ? <span className="text-accent-400 font-bold">Accept</span> :
                                        state.id === dfa.start.id ? <span className="text-secondary-500 font-bold">Start</span> : '-'}
                                </td>
                                {symbols.map(symbol => {
                                    const target = state.transitions[symbol];
                                    return (
                                        <td key={symbol} className="px-6 py-4">
                                            {target ? (target.label || target.id) : '-'}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
