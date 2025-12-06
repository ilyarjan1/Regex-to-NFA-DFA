import { useState } from 'react';

import { Layout } from './components/Layout';
import { InputPanel } from './components/InputPanel';
import { VisualizationPanel } from './components/VisualizationPanel';
import { Documentation } from './components/Documentation';

import { RegexParser } from './lib/automata/regexParser';
import { thompson, resetStateCounter } from './lib/automata/nfa';
import type { NFA } from './lib/automata/nfa';

import { subsetConstruction, testString } from './lib/automata/dfa';
import type { DFA } from './lib/automata/dfa';


function App() {
  const [activePage, setActivePage] = useState('converter');
  const [regex, setRegex] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [nfa, setNfa] = useState<NFA | null>(null);
  const [dfa, setDfa] = useState<DFA | null>(null);
  const [mode, setMode] = useState<'NFA' | 'DFA'>('NFA');

  // String testing state
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState<boolean | null>(null);

  const handleParse = () => {
    try {
      setError(null);
      resetStateCounter();
      const parser = new RegexParser(regex);
      const ast = parser.parse();
      const nfaResult = thompson(ast);
      setNfa(nfaResult);

      const dfaResult = subsetConstruction(nfaResult);
      setDfa(dfaResult);

      setMode('NFA');
      setTestResult(null);
    } catch (err: any) {
      setError(err.message);
      setNfa(null);
      setDfa(null);
    }
  };

  const handleTestString = () => {
    if (dfa) {
      const result = testString(dfa, testInput);
      setTestResult(result);
    }
  };

  return (
    <Layout activePage={activePage} onNavigate={setActivePage}>
      {activePage === 'docs' ? (
        <Documentation />
      ) : activePage === 'home' ? (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <h1 className="text-4xl font-bold text-white mb-4">Welcome to Automata</h1>
          <p className="text-gray-400 max-w-lg mb-8">
            An interactive tool to visualize and understand the conversion of Regular Expressions to NFA and DFA.
          </p>
          <button
            onClick={() => setActivePage('converter')}
            className="bg-accent-600 hover:bg-accent-500 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
          >
            Start Converting
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full">
          {/* Left Column: Input */}
          <div className="lg:col-span-4 h-full">
            <InputPanel
              regex={regex}
              setRegex={setRegex}
              onParse={handleParse}
              error={error}
            />
          </div>

          {/* Right Column: Visualization */}
          <div className="lg:col-span-8 h-full bg-navy-800 rounded-lg border border-navy-700 p-6 flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold text-white">Result</h2>

              {nfa && (
                <div className="flex gap-2 bg-navy-900 p-1 rounded-lg border border-navy-700">
                  <button
                    onClick={() => setMode('NFA')}
                    className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${mode === 'NFA'
                        ? 'bg-accent-600 text-white shadow-sm'
                        : 'text-gray-400 hover:text-white'
                      }`}
                  >
                    NFA
                  </button>
                  <button
                    onClick={() => setMode('DFA')}
                    className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${mode === 'DFA'
                        ? 'bg-accent-600 text-white shadow-sm'
                        : 'text-gray-400 hover:text-white'
                      }`}
                  >
                    DFA
                  </button>
                </div>
              )}
            </div>

            <div className="flex-1 relative bg-navy-900 rounded-lg border border-navy-700 overflow-hidden min-h-[400px]">
              <VisualizationPanel
                nfa={nfa}
                dfa={dfa}
                mode={mode}
                activeStates={[]}
              />
            </div>

            {nfa && (
              <div className="mt-4 flex items-center gap-4">
                <input
                  type="text"
                  placeholder="Test string..."
                  className="bg-navy-900 border border-navy-700 rounded-md px-4 py-2 text-white text-sm outline-none focus:border-accent-500"
                  value={testInput}
                  onChange={(e) => {
                    setTestInput(e.target.value);
                    setTestResult(null);
                  }}
                  onKeyDown={(e) => e.key === 'Enter' && handleTestString()}
                />
                <button
                  onClick={handleTestString}
                  className="text-accent-500 hover:text-accent-400 text-sm font-medium"
                >
                  Test String
                </button>
                {testResult !== null && (
                  <span className={`px-2 py-1 rounded text-xs font-bold ${testResult ? 'bg-green-900/50 text-green-400 border border-green-800' : 'bg-red-900/50 text-red-400 border border-red-800'}`}>
                    {testResult ? 'ACCEPTED' : 'REJECTED'}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}

export default App;
