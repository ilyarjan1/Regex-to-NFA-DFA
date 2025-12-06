import { useEffect, useMemo } from 'react';
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
import { StateNode } from './StateNode';
import { CustomEdge } from './CustomEdge';

interface VisualizationPanelProps {
    nfa: NFA | null;
    dfa: DFA | null;
    mode: 'NFA' | 'DFA';
    activeStates: string[]; // IDs of currently active states
}

const nodeWidth = 60;
const nodeHeight = 60;

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    // Compact spacing: ranksep reduces horizontal distance, nodesep reduces vertical
    dagreGraph.setGraph({ rankdir: 'LR', ranksep: 60, nodesep: 30 });

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

    const nodeTypes = useMemo(() => ({ state: StateNode }), []);
    const edgeTypes = useMemo(() => ({ custom: CustomEdge }), []);

    useEffect(() => {
        let newNodes: Node[] = [];
        let newEdges: Edge[] = [];

        if (mode === 'NFA' && nfa) {
            // Add Start Node Indicator
            newNodes.push({
                id: 'start-indicator',
                data: { label: 'Start' },
                position: { x: 0, y: 0 },
                type: 'input',
                style: {
                    background: 'transparent',
                    color: '#e2e8f0',
                    border: 'none',
                    width: 60,
                    height: 50,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    textTransform: 'lowercase',
                },
            });

            newNodes = [...newNodes, ...nfa.states.map((s) => ({
                id: s.id,
                type: 'state',
                data: {
                    label: s.label || s.id.replace('s', ''),
                    isAccepting: s.isAccepting
                },
                position: { x: 0, y: 0 },
            }))];

            // Edge from indicator to start state
            newEdges.push({
                id: 'start-edge',
                source: 'start-indicator',
                target: nfa.start.id,
                targetHandle: 'left',
                label: '',
                markerEnd: { type: MarkerType.ArrowClosed, color: '#ffffff' },
                style: { stroke: '#ffffff', strokeWidth: 2 },
                type: 'straight',
            });

            nfa.states.forEach((s) => {
                s.transitions.forEach((t, idx) => {
                    const sourceIdNum = parseInt(s.id.replace('s', ''));
                    const targetIdNum = parseInt(t.to.id.replace('s', ''));
                    const diff = targetIdNum - sourceIdNum;

                    let sourceHandle = 'right';
                    let targetHandle = 'left';
                    let edgeType = 'custom';

                    if (sourceIdNum === targetIdNum) {
                        // Self loop - use top handles for visibility
                        sourceHandle = 'top-source';
                        targetHandle = 'top-target';
                    } else if (diff > 1) {
                        // Forward Skip (Arc Over)
                        sourceHandle = 'top-source';
                        targetHandle = 'top-target';
                    } else if (diff < 0) {
                        // Backward Loop (Arc Under)
                        sourceHandle = 'bottom-source';
                        targetHandle = 'bottom-target';
                    } else {
                        // Direct neighbor (diff === 1)
                        sourceHandle = 'right';
                        targetHandle = 'left';
                        // Use default bezier for short connections to avoid "hump"
                        edgeType = 'default';
                    }

                    newEdges.push({
                        id: `${s.id}-${t.to.id}-${idx}`,
                        source: s.id,
                        target: t.to.id,
                        sourceHandle,
                        targetHandle,
                        label: t.symbol === null ? 'ε' : t.symbol,
                        markerEnd: { type: MarkerType.ArrowClosed, color: '#ffffff' },
                        style: { stroke: '#ffffff', strokeWidth: 2 },
                        labelStyle: { fill: '#ffffff', fontWeight: 800, fontSize: 16, stroke: '#0f172a', strokeWidth: 4, paintOrder: 'stroke' },
                        type: edgeType,
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
                    color: '#e2e8f0',
                    border: 'none',
                    width: 60,
                    height: 50,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    textTransform: 'lowercase',
                },
            });

            newNodes = [...newNodes, ...dfa.states.map((s) => ({
                id: s.id,
                type: 'state',
                data: {
                    label: s.label || s.id,
                    isAccepting: s.isAccepting
                },
                position: { x: 0, y: 0 },
            }))];

            // Edge from indicator to start state
            newEdges.push({
                id: 'start-edge',
                source: 'start-indicator',
                target: dfa.start.id,
                targetHandle: 'left',
                label: '',
                markerEnd: { type: MarkerType.ArrowClosed, color: '#ffffff' },
                style: { stroke: '#ffffff', strokeWidth: 2 },
                type: 'straight',
            });

            dfa.states.forEach((s) => {
                Object.entries(s.transitions).forEach(([symbol, target]) => {
                    const sourceIdNum = parseInt(s.id.replace('d', ''));
                    const targetIdNum = parseInt(target.id.replace('d', ''));
                    const diff = isNaN(sourceIdNum) || isNaN(targetIdNum) ? 1 : targetIdNum - sourceIdNum;

                    let sourceHandle = 'right';
                    let targetHandle = 'left';
                    let edgeType = 'custom';

                    if (s.id === target.id) {
                        sourceHandle = 'top-source';
                        targetHandle = 'top-target';
                    } else if (diff > 1) {
                        sourceHandle = 'top-source';
                        targetHandle = 'top-target';
                    } else if (diff < 0) {
                        sourceHandle = 'bottom-source';
                        targetHandle = 'bottom-target';
                    } else {
                        edgeType = 'default';
                    }

                    newEdges.push({
                        id: `${s.id}-${target.id}-${symbol}`,
                        source: s.id,
                        target: target.id,
                        sourceHandle,
                        targetHandle,
                        label: symbol,
                        markerEnd: { type: MarkerType.ArrowClosed, color: '#ffffff' },
                        style: { stroke: '#ffffff', strokeWidth: 2 },
                        labelStyle: { fill: '#ffffff', fontWeight: 800, fontSize: 16, stroke: '#0f172a', strokeWidth: 4, paintOrder: 'stroke' },
                        type: edgeType,
                    });
                });
            });
        }

        // Highlight active states
        newNodes = newNodes.map(node => {
            if (node.id === 'start-indicator') return node;
            return {
                ...node,
                selected: activeStates.includes(node.id),
            };
        });

        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(newNodes, newEdges);
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
    }, [nfa, dfa, mode, activeStates, setNodes, setEdges]);

    return (
        <div className="flex-1 bg-navy-950 h-full">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
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
