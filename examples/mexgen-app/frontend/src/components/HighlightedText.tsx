import { useState } from "react";
import type { UnitAttribution } from "@/types";
import { scoreToColor } from "@/utils/colors";

interface Props {
	attributions: UnitAttribution[];
}

function UnitSpan({ attr }: { attr: UnitAttribution }) {
	const [expanded, setExpanded] = useState(false);
	const hasChildren = attr.children && attr.children.length > 0;
	const isAttributed = attr.unit_type !== "n";

	const bg = isAttributed ? scoreToColor(attr.score) : "transparent";
	const scoreLabel = isAttributed ? attr.score.toFixed(2) : null;

	// Type badge
	const typeBadge: Record<string, string> = {
		s: "sentence",
		ph: "phrase",
		w: "word",
		n: "",
	};

	if (expanded && hasChildren) {
		return (
			<span className="inline">
				<span
					className="relative cursor-pointer border-b border-dashed border-blue-400/50"
					onClick={() => setExpanded(false)}
					title="Click to collapse"
				>
					{attr.children!.map((child, i) => (
						<UnitSpan key={i} attr={child} />
					))}
				</span>
			</span>
		);
	}

	return (
		<span
			className={`
        relative inline rounded-sm px-px transition-colors duration-200
        ${hasChildren ? "cursor-pointer hover:ring-1 hover:ring-blue-400/40" : ""}
        ${isAttributed ? "" : "opacity-50"}
      `}
			style={{ backgroundColor: bg }}
			onClick={hasChildren ? () => setExpanded(true) : undefined}
			title={
				scoreLabel
					? `${typeBadge[attr.unit_type] ?? attr.unit_type} | score: ${scoreLabel}${hasChildren ? " | click to expand" : ""}`
					: undefined
			}
		>
			{attr.text}
		</span>
	);
}

export default function HighlightedText({ attributions }: Props) {
	if (!attributions.length) return null;

	return (
		<div className="leading-7 text-[15px] text-zinc-200 font-sans whitespace-pre-wrap">
			{attributions.map((attr, i) => (
				<UnitSpan key={i} attr={attr} />
			))}
		</div>
	);
}
