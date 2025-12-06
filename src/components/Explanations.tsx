

interface ExplanationsProps {
    mode: 'NFA' | 'DFA';
}

export function Explanations({ mode }: ExplanationsProps) {
    return (
        <div className="bg-navy-800 rounded-lg border border-navy-700 p-6 text-gray-300">
            <h3 className="text-lg font-semibold text-white mb-4">
                {mode === 'NFA' ? "Thompson's Construction Steps" : "Subset Construction Steps"}
            </h3>

            {mode === 'NFA' ? (
                <div className="space-y-4 text-sm">
                    <div className="flex gap-3">
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-navy-700 flex items-center justify-center text-accent-400 font-bold">1</div>
                        <p><strong>Parse Regex:</strong> The regular expression is parsed into an Abstract Syntax Tree (AST) respecting operator precedence (parentheses, Kleene star, concatenation, union).</p>
                    </div>
                    <div className="flex gap-3">
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-navy-700 flex items-center justify-center text-accent-400 font-bold">2</div>
                        <p><strong>Base Cases:</strong> Symbols (a, b) and Epsilon (ε) are converted into simple 2-state NFAs.</p>
                    </div>
                    <div className="flex gap-3">
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-navy-700 flex items-center justify-center text-accent-400 font-bold">3</div>
                        <p><strong>Recursive Construction:</strong> Smaller NFAs are combined using ε-transitions for operations like Union (|), Concatenation, and Kleene Star (*).</p>
                    </div>
                </div>
            ) : (
                <div className="space-y-4 text-sm">
                    <div className="flex gap-3">
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-navy-700 flex items-center justify-center text-secondary-500 font-bold">1</div>
                        <p><strong>Epsilon Closure:</strong> Find the set of all states reachable from the NFA start state using only ε-transitions. This forms the DFA start state.</p>
                    </div>
                    <div className="flex gap-3">
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-navy-700 flex items-center justify-center text-secondary-500 font-bold">2</div>
                        <p><strong>Calculate Transitions:</strong> For each new DFA state (set of NFA states) and each input symbol, calculate the set of reachable NFA states.</p>
                    </div>
                    <div className="flex gap-3">
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-navy-700 flex items-center justify-center text-secondary-500 font-bold">3</div>
                        <p><strong>Repeat:</strong> Repeat step 2 for every newly discovered DFA state until no new states are found.</p>
                    </div>
                </div>
            )}
        </div>
    );
}
