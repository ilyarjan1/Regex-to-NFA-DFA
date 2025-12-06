import { ChevronLeft, ChevronRight, RotateCcw, FastForward } from 'lucide-react';


interface ControlPanelProps {
    onPrev: () => void;
    onNext: () => void;
    onReset: () => void;
    onJumpToEnd: () => void;
    canPrev: boolean;
    canNext: boolean;
    stepDescription: string;
}

export function ControlPanel({
    onPrev,
    onNext,
    onReset,
    onJumpToEnd,
    canPrev,
    canNext,
    stepDescription
}: ControlPanelProps) {
    return (
        <div className="bg-white p-4 border-t border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
                <button
                    onClick={onReset}
                    className="p-2 text-gray-600 hover:bg-gray-100 rounded-full"
                    title="Reset"
                >
                    <RotateCcw size={20} />
                </button>
            </div>

            <div className="flex-1 mx-8 text-center">
                <p className="text-sm font-medium text-gray-800">{stepDescription}</p>
            </div>

            <div className="flex items-center gap-2">
                <button
                    onClick={onPrev}
                    disabled={!canPrev}
                    className={`p-2 rounded-full ${canPrev ? 'text-gray-600 hover:bg-gray-100' : 'text-gray-300 cursor-not-allowed'
                        }`}
                    title="Previous Step"
                >
                    <ChevronLeft size={24} />
                </button>
                <button
                    onClick={onNext}
                    disabled={!canNext}
                    className={`p-2 rounded-full ${canNext ? 'text-blue-600 hover:bg-blue-50' : 'text-gray-300 cursor-not-allowed'
                        }`}
                    title="Next Step"
                >
                    <ChevronRight size={24} />
                </button>
                <button
                    onClick={onJumpToEnd}
                    disabled={!canNext}
                    className={`p-2 rounded-full ${canNext ? 'text-gray-600 hover:bg-gray-100' : 'text-gray-300 cursor-not-allowed'
                        }`}
                    title="Jump to End"
                >
                    <FastForward size={20} />
                </button>
            </div>
        </div>
    );
}
