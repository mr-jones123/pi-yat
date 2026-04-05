import { scoreToColor } from "@/utils/colors";

const STEPS = 11; // -1.0 to 1.0

export default function ColorLegend() {
	const scores = Array.from(
		{ length: STEPS },
		(_, i) => -1 + (2 * i) / (STEPS - 1),
	);

	return (
		<div className="flex items-center gap-3 text-xs text-zinc-500">
			<span>Low importance</span>
			<div className="flex h-4 overflow-hidden rounded">
				{scores.map((s, i) => (
					<div
						key={i}
						className="w-5 h-full"
						style={{ backgroundColor: scoreToColor(s, 0.85) }}
					/>
				))}
			</div>
			<span>High importance</span>
			<span className="ml-2 text-zinc-600">
				Click highlighted sentences to drill down
			</span>
		</div>
	);
}
