import { FileText, MessageSquare, Send } from "lucide-react";
import { useState } from "react";
import type { AttributionMethod, ExplainRequest, TaskType } from "@/types";

interface Props {
	onSubmit: (req: ExplainRequest) => void;
	loading: boolean;
}

const SAMPLE_ARTICLE = `A man has been charged with murder after a woman was found dead at a house in Aylesbury, Buckinghamshire. The 37-year-old man was arrested at the scene on Thursday and charged the following day. The woman, who was in her 30s, was pronounced dead by paramedics at the property. Police said the suspect and victim were known to each other. A post-mortem examination is expected to take place over the weekend. The suspect is due to appear at High Wycombe Magistrates' Court on Monday.`;

const SAMPLE_QA_CONTEXT = `The Apollo program, also known as Project Apollo, was the third United States human spaceflight program carried out by the National Aeronautics and Space Administration (NASA), which succeeded in preparing and landing the first humans on the Moon from 1969 to 1972. It was first conceived during Dwight D. Eisenhower's administration as a three-person spacecraft to follow the one-person Project Mercury, which put the first Americans in space. Apollo was later dedicated to President John F. Kennedy's national goal for the 1960s of "landing a man on the Moon and returning him safely to the Earth" in an address to Congress on May 25, 1961.`;

export default function DocumentInput({ onSubmit, loading }: Props) {
	const [task, setTask] = useState<TaskType>("summarization");
	const [method, setMethod] = useState<AttributionMethod>("clime");
	const [scalarizer, setScalarizer] = useState("prob");
	const [document, setDocument] = useState("");
	const [question, setQuestion] = useState("");

	const handleSubmit = () => {
		if (!document.trim()) return;
		onSubmit({
			document,
			task,
			question: task === "question_answering" ? question : null,
			method,
			scalarizer,
		});
	};

	const loadSample = () => {
		if (task === "summarization") {
			setDocument(SAMPLE_ARTICLE);
			setQuestion("");
		} else {
			setDocument(SAMPLE_QA_CONTEXT);
			setQuestion("Who carried out the Apollo program?");
		}
	};

	return (
		<div className="space-y-4">
			{/* Task + Method selectors */}
			<div className="flex flex-wrap items-center gap-3">
				{/* Task */}
				<div className="flex items-center gap-2">
					<label className="text-xs font-medium uppercase tracking-wider text-zinc-500">
						Task
					</label>
					<select
						value={task}
						onChange={(e) => setTask(e.target.value as TaskType)}
						className="rounded-md border border-zinc-700 bg-surface-2 px-3 py-1.5 text-sm text-zinc-200 focus:border-accent focus:outline-none"
					>
						<option value="summarization">Summarization</option>
						<option value="question_answering">Question Answering</option>
					</select>
				</div>

				{/* Method */}
				<div className="flex items-center gap-2">
					<label className="text-xs font-medium uppercase tracking-wider text-zinc-500">
						Method
					</label>
					<select
						value={method}
						onChange={(e) => setMethod(e.target.value as AttributionMethod)}
						className="rounded-md border border-zinc-700 bg-surface-2 px-3 py-1.5 text-sm text-zinc-200 focus:border-accent focus:outline-none"
					>
						<option value="clime">C-LIME</option>
						<option value="lshap">L-SHAP</option>
						<option value="loo">LOO</option>
					</select>
				</div>

				{/* Scalarizer */}
				<div className="flex items-center gap-2">
					<label className="text-xs font-medium uppercase tracking-wider text-zinc-500">
						Scalarizer
					</label>
					<select
						value={scalarizer}
						onChange={(e) => setScalarizer(e.target.value)}
						className="rounded-md border border-zinc-700 bg-surface-2 px-3 py-1.5 text-sm text-zinc-200 focus:border-accent focus:outline-none"
					>
						<option value="prob">Log Prob</option>
						<option value="text">Text Similarity (BERT)</option>
					</select>
				</div>

				{/* Sample button */}
				<button
					type="button"
					onClick={loadSample}
					className="ml-auto flex items-center gap-1.5 rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 transition hover:border-zinc-500 hover:text-zinc-200"
				>
					<FileText size={14} />
					Load sample
				</button>
			</div>

			{/* Document input */}
			<textarea
				value={document}
				onChange={(e) => setDocument(e.target.value)}
				placeholder="Paste your document or article here …"
				rows={8}
				className="w-full resize-y rounded-lg border border-zinc-700 bg-surface-2 px-4 py-3 text-sm leading-relaxed text-zinc-200 placeholder:text-zinc-600 focus:border-accent focus:outline-none"
			/>

			{/* Question input (QA only) */}
			{task === "question_answering" && (
				<div className="flex items-center gap-2">
					<MessageSquare size={16} className="text-zinc-500" />
					<input
						type="text"
						value={question}
						onChange={(e) => setQuestion(e.target.value)}
						placeholder="Enter your question …"
						className="flex-1 rounded-md border border-zinc-700 bg-surface-2 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-accent focus:outline-none"
					/>
				</div>
			)}

			{/* Submit */}
			<button
				onClick={handleSubmit}
				disabled={loading || !document.trim()}
				className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white transition hover:bg-accent-dim disabled:cursor-not-allowed disabled:opacity-40"
			>
				<Send size={16} />
				{loading ? "Processing …" : "Explain"}
			</button>
		</div>
	);
}
