import { useEffect } from 'react';
import {
    ReactFlow,
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    MarkerType,
} from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import type { NFA } from '../lib/automata/nfa';
import type { DFA } from '../lib/automata/dfa';

interface VisualizationPanelProps {
    nfa: NFA | null;
    dfa: DFA | null;
    mode: 'NFA' | 'DFA';
    activeStates: string[]; // IDs of currently active states
}

const nodeWidth = 50;
const nodeHeight = 50;

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    dagreGraph.setGraph({ rankdir: 'LR' });

    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
    });

    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    const layoutedNodes = nodes.map((node) => {
        const nodeWithPosition = dagreGraph.node(node.id);
        node.position = {
            x: nodeWithPosition.x - nodeWidth / 2,
            y: nodeWithPosition.y - nodeHeight / 2,
        };
        return node;
    });

    return { nodes: layoutedNodes, edges };
};

export function VisualizationPanel({ nfa, dfa, mode, activeStates }: VisualizationPanelProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

    useEffect(() => {
        let newNodes: Node[] = [];
        let newEdges: Edge[] = [];

        if (mode === 'NFA' && nfa) {
            newNodes = nfa.states.map((s) => ({
                id: s.id,
                data: { label: s.label || s.id.replace('s', '') },
                position: { x: 0, y: 0 },
                style: {
                    background: '#1e293b', // navy-800
                    color: '#fff',
                    border: s.isAccepting ? '2px double #fff' : '1px solid #94a3b8', // slate-400
                    borderWidth: s.isAccepting ? '4px' : '1px',
                    borderRadius: '50%',
                    width: 50,
                    height: 50,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    fontSize: '12px',
                    fontWeight: '500',
                },
            }));

            nfa.states.forEach((s) => {
                s.transitions.forEach((t, idx) => {
                    newEdges.push({
                        id: `${s.id}-${t.to.id}-${idx}`,
                        source: s.id,
                        target: t.to.id,
                        label: t.symbol === null ? 'ε' : t.symbol,
                        markerEnd: { type: MarkerType.ArrowClosed, color: '#94a3b8' },
                        style: { stroke: '#94a3b8' },
                        labelStyle: { fill: '#cbd5e1', fontWeight: 700 }, // slate-300
                        type: 'smoothstep',
                    });
                });
            });
        } else if (mode === 'DFA' && dfa) {
            newNodes = dfa.states.map((s) => ({
                id: s.id,
                data: { label: s.label || s.id },
                position: { x: 0, y: 0 },
                style: {
                    background: '#1e293b',
                    color: '#fff',
                    border: s.isAccepting ? '4px solid #fff' : '1px solid #94a3b8',
                    borderRadius: '50%',
                    width: 60,
                    height: 60,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    fontSize: '10px',
                },
            }));

            dfa.states.forEach((s) => {
                Object.entries(s.transitions).forEach(([symbol, target]) => {
                    newEdges.push({
                        id: `${s.id}-${target.id}-${symbol}`,
                        source: s.id,
                        target: target.id,
                        label: symbol,
                        markerEnd: { type: MarkerType.ArrowClosed, color: '#94a3b8' },
                        style: { stroke: '#94a3b8' },
                        labelStyle: { fill: '#cbd5e1', fontWeight: 700 },
                        type: 'smoothstep',
                    });
                });
            });
        }

        // Highlight active states
        newNodes = newNodes.map(node => ({
            ...node,
            style: {
                ...node.style,
                background: activeStates.includes(node.id) ? '#2563eb' : (node.style?.background || '#1e293b'), // accent-600
                borderColor: activeStates.includes(node.id) ? '#60a5fa' : (node.style?.borderColor || '#94a3b8'),
            }
        }));

        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(newNodes, newEdges);
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
    }, [nfa, dfa, mode, activeStates, setNodes, setEdges]);

    return (
        <div className="flex-1 bg-navy-900 h-full">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
                attributionPosition="bottom-right"
                colorMode="dark"
            >
                <Background color="#334155" gap={16} />
                <Controls className="bg-navy-800 border-navy-700 text-white" />
            </ReactFlow>
        </div>
    );
}
