

export function Documentation() {
    return (
        <div className="bg-navy-800 rounded-lg border border-navy-700 p-8 text-gray-200 h-full overflow-y-auto">
            <h1 className="text-3xl font-bold text-white mb-6">Documentation</h1>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-accent-500 mb-4">Overview</h2>
                <p className="mb-4">
                    This application is an interactive tool for converting Regular Expressions (Regex) into Nondeterministic Finite Automata (NFA) and then into Deterministic Finite Automata (DFA). It is designed to help students and enthusiasts understand the underlying algorithms of automata theory.
                </p>
            </section>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-accent-500 mb-4">Supported Syntax</h2>
                <ul className="list-disc pl-6 space-y-2">
                    <li><strong>Concatenation</strong>: Implicit (e.g., <code className="bg-navy-900 px-2 py-1 rounded">ab</code>)</li>
                    <li><strong>Union</strong>: <code className="bg-navy-900 px-2 py-1 rounded">|</code> (e.g., <code className="bg-navy-900 px-2 py-1 rounded">a|b</code>)</li>
                    <li><strong>Kleene Star</strong>: <code className="bg-navy-900 px-2 py-1 rounded">*</code> (e.g., <code className="bg-navy-900 px-2 py-1 rounded">a*</code>)</li>
                    <li><strong>One or More</strong>: <code className="bg-navy-900 px-2 py-1 rounded">+</code> (e.g., <code className="bg-navy-900 px-2 py-1 rounded">a+</code>)</li>
                    <li><strong>Zero or One</strong>: <code className="bg-navy-900 px-2 py-1 rounded">?</code> (e.g., <code className="bg-navy-900 px-2 py-1 rounded">a?</code>)</li>
                    <li><strong>Grouping</strong>: <code className="bg-navy-900 px-2 py-1 rounded">()</code> (e.g., <code className="bg-navy-900 px-2 py-1 rounded">(a|b)*</code>)</li>
                    <li><strong>Epsilon</strong>: <code className="bg-navy-900 px-2 py-1 rounded">ε</code> (represented internally, use empty string or logic implies it)</li>
                </ul>
            </section>

            <section className="mb-8">
                <h2 className="text-xl font-semibold text-accent-500 mb-4">Algorithms Used</h2>
                <div className="space-y-4">
                    <div>
                        <h3 className="text-lg font-medium text-white">Thompson's Construction</h3>
                        <p className="text-gray-400">
                            Used to convert the Regular Expression into an NFA. It builds the NFA recursively by creating small NFA fragments for each sub-expression and combining them using ε-transitions.
                        </p>
                    </div>
                    <div>
                        <h3 className="text-lg font-medium text-white">Subset Construction</h3>
                        <p className="text-gray-400">
                            Used to convert the NFA into a DFA. It simulates the NFA in parallel to find all reachable states for each input symbol, creating a new DFA state for each unique set of NFA states.
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
}
