import dagre from 'dagre';

try {
    console.log('Dagre imported:', dagre);
    const g = new dagre.graphlib.Graph();
    g.setGraph({});
    g.setDefaultEdgeLabel(() => ({}));

    g.setNode('a', { width: 50, height: 50 });
    g.setNode('b', { width: 50, height: 50 });
    g.setEdge('a', 'b');

    dagre.layout(g);

    console.log('Node a:', g.node('a'));
    console.log('Node b:', g.node('b'));
    console.log('Dagre layout successful');
} catch (error) {
    console.error('Dagre error:', error);
}
