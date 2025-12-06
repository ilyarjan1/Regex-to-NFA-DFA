import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';

export function StateNode({ data, selected, style }: NodeProps & { style?: React.CSSProperties }) {
    const isAccepting = data.isAccepting as boolean;
    const label = data.label as string;

    // Parse dimensions from style or default to 50
    const width = style?.width ? Number(style.width) : 50;
    const height = style?.height ? Number(style.height) : 50;

    // Format label for display
    const formatLabel = (text: string) => {
        if (text.startsWith('{') && text.endsWith('}')) {
            // It's a set label, try to break it up
            const inner = text.slice(1, -1);
            const parts = inner.split(',');
            if (parts.length > 4) {
                // Split into chunks of 3
                const chunks = [];
                for (let i = 0; i < parts.length; i += 3) {
                    chunks.push(parts.slice(i, i + 3).join(','));
                }
                return (
                    <div className="flex flex-col items-center leading-tight">
                        <span>{'{'}</span>
                        {chunks.map((chunk, i) => (
                            <span key={i}>{chunk}{i < chunks.length - 1 ? ',' : ''}</span>
                        ))}
                        <span>{'}'}</span>
                    </div>
                );
            }
        }
        return text;
    };

    // Dynamic font size based on width
    const fontSize = width > 80 ? 'text-xs' : 'text-sm';

    return (
        <div
            className={`relative flex items-center justify-center rounded-full transition-all duration-300
        ${selected
                    ? 'bg-accent-600 border-accent-400 shadow-[0_0_20px_rgba(45,212,191,0.6)]'
                    : 'bg-navy-900 border-slate-400 shadow-[0_0_10px_rgba(148,163,184,0.2)]'
                }
        ${isAccepting ? 'border-4 border-double border-white' : 'border-2'}
      `}
            style={{
                width: `${width}px`,
                height: `${height}px`,
                color: selected ? '#ffffff' : '#f8fafc',
            }}
        >
            {/* Main Left/Right Handles for sequential flow */}
            <Handle
                type="target"
                position={Position.Left}
                id="left"
                className="!w-1 !h-1 !bg-transparent !border-none"
            />
            <Handle
                type="source"
                position={Position.Right}
                id="right"
                className="!w-1 !h-1 !bg-transparent !border-none"
            />

            {/* Top Handles for Forward Skips (Arcs Over) */}
            <Handle
                type="source"
                position={Position.Top}
                id="top-source"
                className="!w-1 !h-1 !bg-transparent !border-none !-top-1"
            />
            <Handle
                type="target"
                position={Position.Top}
                id="top-target"
                className="!w-1 !h-1 !bg-transparent !border-none !-top-1"
            />

            {/* Bottom Handles for Backward Loops (Arcs Under) */}
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom-source"
                className="!w-1 !h-1 !bg-transparent !border-none !-bottom-1"
            />
            <Handle
                type="target"
                position={Position.Bottom}
                id="bottom-target"
                className="!w-1 !h-1 !bg-transparent !border-none !-bottom-1"
            />

            <span className={`${fontSize} font-bold select-none text-center px-1`}>
                {formatLabel(label)}
            </span>
        </div>
    );
}
