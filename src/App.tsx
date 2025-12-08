import { useState } from 'react';

import { Layout } from './components/Layout';
import { InputPanel } from './components/InputPanel';
import { VisualizationPanel } from './components/VisualizationPanel';
import { Documentation } from './components/Documentation';
import { TransitionTable } from './components/TransitionTable';
import { Explanations } from './components/Explanations';

import { RegexParser } from './lib/automata/regexParser';
import { thompson, resetStateCounter } from './lib/automata/nfa';
import type { NFA } from './lib/automata/nfa';

import { subsetConstruction, testString } from './lib/automata/dfa';
import type { DFA } from './lib/automata/dfa';


function App() {
  const [activePage, setActivePage] = useState('home');
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
        <div className="flex flex-col items-center justify-center h-full text-center px-4">
          <h1 className="text-3xl md:text-5xl font-bold text-white mb-6 tracking-tight">
            Master <span className="text-accent-400">Automata Theory</span>
          </h1>
          <p className="text-gray-400 max-w-2xl mb-10 text-base md:text-lg leading-relaxed">
            Visualize the magic of converting Regular Expressions into Nondeterministic and Deterministic Finite Automata. Interactive, educational, and easy to understand.
          </p>
          <button
            onClick={() => setActivePage('converter')}
            className="bg-accent-600 hover:bg-accent-500 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all shadow-lg shadow-accent-900/20 hover:scale-105"
          >
            Start Learning
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full overflow-y-auto pr-2 pb-20 md:pb-0">
          {/* Left Column: Input & Explanations */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            <InputPanel
              regex={regex}
              setRegex={setRegex}
              onParse={handleParse}
              error={error}
            />

            {nfa && <Explanations mode={mode} />}
          </div>

          {/* Right Column: Visualization & Table */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            <div className="bg-navy-800 rounded-lg border border-navy-700 p-4 md:p-6 flex flex-col shadow-xl">
              <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4 md:gap-0">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span className="w-2 h-8 bg-accent-500 rounded-full"></span>
                  Visualization Result
                </h2>

                {nfa && (
                  <div className="flex gap-2 bg-navy-900 p-1 rounded-lg border border-navy-700">
                    <button
                      onClick={() => setMode('NFA')}
                      className={`px-4 py-1.5 rounded-md text-sm font-bold transition-all ${mode === 'NFA'
                        ? 'bg-accent-600 text-white shadow-lg shadow-accent-900/50'
                        : 'text-gray-400 hover:text-white hover:bg-navy-800'
                        }`}
                    >
                      NFA
                    </button>
                    <button
                      onClick={() => setMode('DFA')}
                      className={`px-4 py-1.5 rounded-md text-sm font-bold transition-all ${mode === 'DFA'
                        ? 'bg-secondary-500 text-white shadow-lg shadow-secondary-900/50'
                        : 'text-gray-400 hover:text-white hover:bg-navy-800'
                        }`}
                    >
                      DFA
                    </button>
                  </div>
                )}
              </div>

              <div className="flex-1 relative bg-navy-950 rounded-lg border border-navy-700 overflow-hidden min-h-[300px] md:min-h-[400px]">
                <VisualizationPanel
                  nfa={nfa}
                  dfa={dfa}
                  mode={mode}
                  activeStates={[]}
                />
              </div>

              {nfa && (
                <div className="mt-6 flex flex-col md:flex-row items-center gap-4 bg-navy-900/50 p-4 rounded-lg border border-navy-700">
                  <input
                    type="text"
                    placeholder="Test string..."
                    className="w-full md:w-auto bg-navy-950 border border-navy-700 rounded-md px-4 py-2 text-white text-sm outline-none focus:border-accent-500 flex-1"
                    value={testInput}
                    onChange={(e) => {
                      setTestInput(e.target.value);
                      setTestResult(null);
                    }}
                    onKeyDown={(e) => e.key === 'Enter' && handleTestString()}
                  />
                  <button
                    onClick={handleTestString}
                    className="bg-navy-800 hover:bg-navy-700 text-accent-400 border border-navy-600 px-4 py-2 rounded-md text-sm font-bold transition-colors"
                  >
                    Test String
                  </button>
                  {testResult !== null && (
                    <span className={`px-3 py-2 rounded-md text-xs font-bold uppercase tracking-wider ${testResult ? 'bg-green-900/30 text-green-400 border border-green-800' : 'bg-red-900/30 text-red-400 border border-red-800'}`}>
                      {testResult ? 'Accepted' : 'Rejected'}
                    </span>
                  )}
                </div>
              )}
            </div>

            {nfa && (
              <TransitionTable nfa={nfa} dfa={dfa} mode={mode} />
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}

export default App;
