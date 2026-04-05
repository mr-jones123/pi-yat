/**
 * Map a normalised attribution score [-1, 1] to a background color.
 *
 * Negative scores → red (context hurts), zero → neutral gray,
 * positive scores → blue (context helps).
 *
 * Uses sqrt scaling on magnitude so small differences near zero are more
 * visible (matching the paper's visualization approach).
 */
export function scoreToColor(score: number, opacity = 0.65): string {
	// Clamp to [-1, 1]
	const s = Math.max(-1, Math.min(1, score));

	// Sqrt scaling on magnitude
	const magnitude = Math.sqrt(Math.abs(s));

	if (s >= 0) {
		// Blue channel: rgb(59, 130, 246) = Tailwind blue-500
		const r = Math.round(59 * magnitude);
		const g = Math.round(130 * magnitude);
		const b = Math.round(246 * magnitude);
		return `rgba(${r}, ${g}, ${b}, ${opacity * magnitude})`;
	} else {
		// Red channel: rgb(239, 68, 68) = Tailwind red-500
		const r = Math.round(239 * magnitude);
		const g = Math.round(68 * magnitude);
		const b = Math.round(68 * magnitude);
		return `rgba(${r}, ${g}, ${b}, ${opacity * magnitude})`;
	}
}

/**
 * Human-readable labels for job status.
 */
export const STATUS_LABELS: Record<string, string> = {
	pending: "Queued",
	generating: "Generating output …",
	explaining_coarse: "Computing sentence attributions …",
	explaining_fine: "Refining to phrase level …",
	complete: "Complete",
	failed: "Failed",
};
