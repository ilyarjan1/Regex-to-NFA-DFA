import { Info } from 'lucide-react';


interface ExplanationPanelProps {
    title: string;
    description: string;
}

export function ExplanationPanel({ title, description }: ExplanationPanelProps) {
    return (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-3">
                <Info className="text-blue-600 mt-1" size={20} />
                <div>
                    <h3 className="font-medium text-blue-900">{title}</h3>
                    <p className="text-blue-800 text-sm mt-1">{description}</p>
                </div>
            </div>
        </div>
    );
}
