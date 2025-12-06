import { Handle, Position } from '@xyflow/react';
import type { NodeProps } from '@xyflow/react';

export function StateNode({ data, selected }: NodeProps) {
    const isAccepting = data.isAccepting as boolean;
    const label = data.label as string;

    return (
        <div
            className={`relative flex items-center justify-center w-[50px] h-[50px] rounded-full transition-all duration-300
        ${selected
                    ? 'bg-accent-600 border-accent-400 shadow-[0_0_20px_rgba(45,212,191,0.6)]'
                    : 'bg-navy-900 border-slate-400 shadow-[0_0_10px_rgba(148,163,184,0.2)]'
                }
        ${isAccepting ? 'border-4 border-double border-white' : 'border-2'}
      `}
            style={{
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

            <span className="text-sm font-bold select-none">{label}</span>

            {/* Double ring visual for accepting state (handled by border-double above, but can enhance) */}
        </div>
    );
}
