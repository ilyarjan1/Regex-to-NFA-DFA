import type { NFA, State } from './nfa';


export interface DFAState {
    id: string;
    isAccepting: boolean;
    transitions: Record<string, DFAState>; // symbol -> state
    nfaStates: State[]; // The set of NFA states this DFA state represents
    label?: string;
}

export interface DFA {
    start: DFAState;
    states: DFAState[];
}

export function subsetConstruction(nfa: NFA): DFA {
    const alphabet = getAlphabet(nfa);
    const startClosure = epsilonClosure([nfa.start]);

    const startState: DFAState = {
        id: 'd0',
        isAccepting: startClosure.some(s => s.isAccepting),
        transitions: {},
        nfaStates: startClosure,
        label: formatLabel(startClosure)
    };

    const states: DFAState[] = [startState];
    const queue: DFAState[] = [startState];

    // Map to keep track of existing states (key: sorted NFA state IDs)
    const stateMap = new Map<string, DFAState>();
    stateMap.set(getStateKey(startClosure), startState);

    let dfaCounter = 1;

    while (queue.length > 0) {
        const currentDFAState = queue.shift()!;

        for (const symbol of alphabet) {
            // Move(T, a)
            const moveResult = move(currentDFAState.nfaStates, symbol);
            // Epsilon-closure of Move(T, a)
            const closure = epsilonClosure(moveResult);

            if (closure.length === 0) continue; // Dead state (implicit)

            const key = getStateKey(closure);
            let targetState = stateMap.get(key);

            if (!targetState) {
                targetState = {
                    id: `d${dfaCounter++}`,
                    isAccepting: closure.some(s => s.isAccepting),
                    transitions: {},
                    nfaStates: closure,
                    label: formatLabel(closure)
                };
                states.push(targetState);
                queue.push(targetState);
                stateMap.set(key, targetState);
            }

            currentDFAState.transitions[symbol] = targetState;
        }
    }

    return { start: startState, states };
}

function getAlphabet(nfa: NFA): Set<string> {
    const symbols = new Set<string>();
    for (const state of nfa.states) {
        for (const trans of state.transitions) {
            if (trans.symbol !== null) {
                symbols.add(trans.symbol);
            }
        }
    }
    return symbols;
}

export function epsilonClosure(states: State[]): State[] {
    const stack = [...states];
    const closure = new Set<State>(states);

    while (stack.length > 0) {
        const current = stack.pop()!;
        for (const trans of current.transitions) {
            if (trans.symbol === null && !closure.has(trans.to)) {
                closure.add(trans.to);
                stack.push(trans.to);
            }
        }
    }

    return Array.from(closure).sort((a, b) => a.id.localeCompare(b.id));
}

function move(states: State[], symbol: string): State[] {
    const result = new Set<State>();
    for (const state of states) {
        for (const trans of state.transitions) {
            if (trans.symbol === symbol) {
                result.add(trans.to);
            }
        }
    }
    return Array.from(result);
}

function getStateKey(states: State[]): string {
    return states.map(s => s.id).sort().join(',');
}

function formatLabel(states: State[]): string {
    return `{${states.map(s => s.id.replace('s', '')).join(',')}}`;
}

export function testString(dfa: DFA, input: string): boolean {
    let currentState = dfa.start;

    for (const char of input) {
        if (currentState.transitions[char]) {
            currentState = currentState.transitions[char];
        } else {
            return false; // No transition for this symbol
        }
    }

    return currentState.isAccepting;
}
