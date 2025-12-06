import type { ASTNode } from './regexParser';


export interface Transition {
    symbol: string | null; // null for epsilon
    to: State;
}

export interface State {
    id: string;
    isAccepting: boolean;
    transitions: Transition[];
    label?: string; // For visualization
}

export interface NFA {
    start: State;
    end: State;
    states: State[]; // Keep track of all states for visualization
}

let stateCounter = 0;

export function resetStateCounter() {
    stateCounter = 0;
}

function createState(isAccepting: boolean = false): State {
    return {
        id: `s${stateCounter++}`,
        isAccepting,
        transitions: [],
    };
}

// Wrapper to ensure renumbering happens at the top level
export function thompson(node: ASTNode): NFA {
    const nfa = _thompson(node);
    return renumberNFA(nfa);
}

function _thompson(node: ASTNode): NFA {
    switch (node.type) {
        case 'Literal':
        case 'Epsilon':
            return createBasicNFA(node.value || null);
        case 'Union':
            if (!node.left || !node.right) throw new Error("Union node missing children");
            return createUnionNFA(_thompson(node.left), _thompson(node.right));
        case 'Concat':
            if (!node.left || !node.right) throw new Error("Concat node missing children");
            return createConcatNFA(_thompson(node.left), _thompson(node.right));
        case 'Star':
            if (!node.left) throw new Error("Star node missing child");
            return createStarNFA(_thompson(node.left));
        default:
            throw new Error(`Unknown node type: ${node.type}`);
    }
}

export function renumberNFA(nfa: NFA): NFA {
    const newIdMap = new Map<string, string>();
    let counter = 0;
    const queue: State[] = [nfa.start];
    const visited = new Set<string>();

    visited.add(nfa.start.id);
    newIdMap.set(nfa.start.id, `s${counter++}`);

    // BFS to assign IDs
    let head = 0;
    while (head < queue.length) {
        const current = queue[head++];

        // Sort transitions to ensure deterministic numbering
        const sortedTransitions = [...current.transitions].sort((a, b) => {
            if (a.symbol === b.symbol) return 0;
            if (a.symbol === null) return 1;
            if (b.symbol === null) return -1;
            return (a.symbol || '').localeCompare(b.symbol || '');
        });

        for (const trans of sortedTransitions) {
            if (!visited.has(trans.to.id)) {
                visited.add(trans.to.id);
                newIdMap.set(trans.to.id, `s${counter++}`);
                queue.push(trans.to);
            }
        }
    }

    // Handle unreachable states
    for (const state of nfa.states) {
        if (!visited.has(state.id)) {
            newIdMap.set(state.id, `s${counter++}`);
        }
    }

    // Update IDs
    nfa.states.forEach(state => {
        state.id = newIdMap.get(state.id)!;
        if (state.label && state.label.startsWith('s')) {
            delete state.label;
        }
    });

    return nfa;
}

function createBasicNFA(symbol: string | null): NFA {
    const start = createState();
    const end = createState(true);
    start.transitions.push({ symbol, to: end });
    return { start, end, states: [start, end] };
}

function createUnionNFA(nfa1: NFA, nfa2: NFA): NFA {
    const start = createState();
    const end = createState(true);

    // Epsilon transitions from new start to both starts
    start.transitions.push({ symbol: null, to: nfa1.start });
    start.transitions.push({ symbol: null, to: nfa2.start });

    // Epsilon transitions from both ends to new end
    nfa1.end.isAccepting = false;
    nfa2.end.isAccepting = false;
    nfa1.end.transitions.push({ symbol: null, to: end });
    nfa2.end.transitions.push({ symbol: null, to: end });

    return {
        start,
        end,
        states: [start, end, ...nfa1.states, ...nfa2.states],
    };
}

function createConcatNFA(nfa1: NFA, nfa2: NFA): NFA {
    // Connect nfa1.end to nfa2.start with epsilon
    nfa1.end.isAccepting = false;
    nfa1.end.transitions.push({ symbol: null, to: nfa2.start });

    return {
        start: nfa1.start,
        end: nfa2.end,
        states: [...nfa1.states, ...nfa2.states],
    };
}

function createStarNFA(nfa: NFA): NFA {
    const start = createState();
    const end = createState(true);

    // Epsilon from new start to inner start
    start.transitions.push({ symbol: null, to: nfa.start });

    // Epsilon from new start to new end (zero occurrences)
    start.transitions.push({ symbol: null, to: end });

    // Epsilon from inner end to inner start (loop)
    nfa.end.isAccepting = false;
    nfa.end.transitions.push({ symbol: null, to: nfa.start });

    // Epsilon from inner end to new end
    nfa.end.transitions.push({ symbol: null, to: end });

    return {
        start,
        end,
        states: [start, end, ...nfa.states],
    };
}
