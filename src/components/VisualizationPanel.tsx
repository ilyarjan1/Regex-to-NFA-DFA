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

    dagreGraph.setGraph({ rankdir: 'LR', ranksep: 80, nodesep: 40 }); // Increased spacing

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
            // Add Start Node Indicator
            newNodes.push({
                id: 'start-indicator',
                data: { label: 'Start' },
                position: { x: 0, y: 0 },
                type: 'input', // Special type if needed, but default works
                style: {
                    background: 'transparent',
                    color: '#94a3b8', // slate-400
                    border: 'none',
                    width: 50,
                    height: 50,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    fontSize: '14px',
                    fontWeight: 'bold',
                },
            });

            newNodes = [...newNodes, ...nfa.states.map((s) => ({
                id: s.id,
                data: { label: s.label || s.id.replace('s', '') },
                position: { x: 0, y: 0 },
                style: {
                    background: '#1e293b', // navy-800
                    color: '#fff',
                    border: s.isAccepting ? '2px double #2dd4bf' : '1px solid #64748b', // accent-400 or slate-500
                    borderWidth: s.isAccepting ? '4px' : '2px',
                    borderColor: s.isAccepting ? '#2dd4bf' : '#64748b',
                    borderRadius: '50%',
                    width: 50,
                    height: 50,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    fontSize: '14px',
                    fontWeight: '600',
                    boxShadow: s.isAccepting ? '0 0 10px rgba(45, 212, 191, 0.3)' : 'none',
                },
            }))];

            // Edge from indicator to start state
            newEdges.push({
                id: 'start-edge',
                source: 'start-indicator',
                target: nfa.start.id,
                label: '',
                markerEnd: { type: MarkerType.ArrowClosed, color: '#94a3b8' },
                style: { stroke: '#94a3b8', strokeWidth: 2 },
                type: 'straight',
            });

            nfa.states.forEach((s) => {
                s.transitions.forEach((t, idx) => {
                    newEdges.push({
                        id: `${s.id}-${t.to.id}-${idx}`,
                        source: s.id,
                        target: t.to.id,
                        label: t.symbol === null ? 'ε' : t.symbol,
                        markerEnd: { type: MarkerType.ArrowClosed, color: '#cbd5e1' },
                        style: { stroke: '#cbd5e1', strokeWidth: 1.5 },
                        labelStyle: { fill: '#f1f5f9', fontWeight: 700, fontSize: 12 }, // slate-100
                        type: 'smoothstep',
                    });
                });
            });
        } else if (mode === 'DFA' && dfa) {
            // Add Start Node Indicator
            newNodes.push({
                id: 'start-indicator',
                data: { label: 'Start' },
                position: { x: 0, y: 0 },
                style: {
                    background: 'transparent',
                    color: '#94a3b8',
                    border: 'none',
                    width: 50,
                    height: 50,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    fontSize: '14px',
                    fontWeight: 'bold',
                },
            });

            newNodes = [...newNodes, ...dfa.states.map((s) => ({
                id: s.id,
                data: { label: s.label || s.id },
                position: { x: 0, y: 0 },
                style: {
                    background: '#1e293b',
                    color: '#fff',
                    border: s.isAccepting ? '4px double #2dd4bf' : '2px solid #64748b',
                    borderColor: s.isAccepting ? '#2dd4bf' : '#64748b',
                    borderRadius: '50%',
                    width: 60,
                    height: 60,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    fontSize: '12px',
                    fontWeight: '600',
                    boxShadow: s.isAccepting ? '0 0 10px rgba(45, 212, 191, 0.3)' : 'none',
                },
            }))];

            // Edge from indicator to start state
            newEdges.push({
                id: 'start-edge',
                source: 'start-indicator',
                target: dfa.start.id,
                label: '',
                markerEnd: { type: MarkerType.ArrowClosed, color: '#94a3b8' },
                style: { stroke: '#94a3b8', strokeWidth: 2 },
                type: 'straight',
            });

            dfa.states.forEach((s) => {
                Object.entries(s.transitions).forEach(([symbol, target]) => {
                    newEdges.push({
                        id: `${s.id}-${target.id}-${symbol}`,
                        source: s.id,
                        target: target.id,
                        label: symbol,
                        markerEnd: { type: MarkerType.ArrowClosed, color: '#cbd5e1' },
                        style: { stroke: '#cbd5e1', strokeWidth: 1.5 },
                        labelStyle: { fill: '#f1f5f9', fontWeight: 700, fontSize: 12 },
                        type: 'smoothstep',
                    });
                });
            });
        }

        // Highlight active states
        newNodes = newNodes.map(node => {
            if (node.id === 'start-indicator') return node;
            return {
                ...node,
                style: {
                    ...node.style,
                    background: activeStates.includes(node.id) ? '#14b8a6' : (node.style?.background || '#1e293b'), // accent-500
                    borderColor: activeStates.includes(node.id) ? '#2dd4bf' : (node.style?.borderColor || '#64748b'),
                    boxShadow: activeStates.includes(node.id) ? '0 0 15px rgba(20, 184, 166, 0.6)' : (node.style?.boxShadow || 'none'),
                }
            };
        });

        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(newNodes, newEdges);
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
    }, [nfa, dfa, mode, activeStates, setNodes, setEdges]);

    return (
        <div className="flex-1 bg-navy-950 h-full"> {/* Darker background for contrast */}
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
                attributionPosition="bottom-right"
                colorMode="dark"
            >
                <Background color="#334155" gap={20} size={1} />
                <Controls className="bg-navy-800 border-navy-700 text-white" />
            </ReactFlow>
        </div>
    );
}
