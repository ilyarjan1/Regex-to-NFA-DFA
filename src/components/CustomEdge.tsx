import { BaseEdge, getBezierPath } from '@xyflow/react';
import type { EdgeProps } from '@xyflow/react';

export function CustomEdge({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    style = {},
    markerEnd,
    label,
    labelStyle,
}: EdgeProps) {
    // Calculate distance between nodes
    const dx = Math.abs(targetX - sourceX);

    // Determine if this is a "long" jump or a neighbor connection
    // We can infer this from the handles or just the distance.
    // If handles are Top/Top or Bottom/Bottom, we want an arch.

    let edgePath = '';
    let labelX = 0;
    let labelY = 0;

    // Check if we are connecting Top-Top (Forward Arch) or Bottom-Bottom (Backward Loop)
    // We can't easily access handle IDs here directly without passing them as data, 
    // but we can infer from positions (Position.Top, Position.Bottom).

    const isTopArch = sourcePosition === 'top' && targetPosition === 'top';
    const isBottomArch = sourcePosition === 'bottom' && targetPosition === 'bottom';

    if (isTopArch) {
        // Custom Bezier for Top Arch
        // Control points should be higher based on distance
        const heightFactor = Math.max(50, dx * 0.4); // Height proportional to width
        const controlY = Math.min(sourceY, targetY) - heightFactor;

        edgePath = `M ${sourceX} ${sourceY} Q ${(sourceX + targetX) / 2} ${controlY} ${targetX} ${targetY}`;

        // Label position (approximate peak)
        labelX = (sourceX + targetX) / 2;
        labelY = controlY + 10; // Slightly below peak
    } else if (isBottomArch) {
        // Custom Bezier for Bottom Arch
        const heightFactor = Math.max(50, dx * 0.4);
        const controlY = Math.max(sourceY, targetY) + heightFactor;

        edgePath = `M ${sourceX} ${sourceY} Q ${(sourceX + targetX) / 2} ${controlY} ${targetX} ${targetY}`;

        labelX = (sourceX + targetX) / 2;
        labelY = controlY - 10; // Slightly above peak
    } else {
        // Default Bezier for standard connections
        const [path, lx, ly] = getBezierPath({
            sourceX,
            sourceY,
            sourcePosition,
            targetX,
            targetY,
            targetPosition,
        });
        edgePath = path;
        labelX = lx;
        labelY = ly;
    }

    return (
        <>
            <BaseEdge path={edgePath} markerEnd={markerEnd} style={style} />
            {label && (
                <text
                    x={labelX}
                    y={labelY}
                    className="nopan"
                    style={{
                        fontSize: 12,
                        fontWeight: 700,
                        fill: '#f8fafc', // slate-50
                        textAnchor: 'middle',
                        dominantBaseline: 'central',
                        ...labelStyle,
                    }}
                >
                    {label}
                </text>
            )}
        </>
    );
}
