import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type } from "@sinclair/typebox";

export default function (pi: ExtensionAPI) {
	let hfAvailable = false;

	pi.on("session_start", async (_event, _ctx) => {
		const result = await pi.exec("which", ["hf"]);
		hfAvailable = result.code === 0;
	});

	function checkHf() {
		if (!hfAvailable) {
			return {
				content: [
					{
						type: "text" as const,
						text: "hf CLI not installed. Run: curl -LsSf https://hf.co/cli/install.sh | bash",
					},
				],
				isError: true,
			};
		}
		return null;
	}

	// --- Tools ---

	pi.registerTool({
		name: "search_papers",
		label: "Search Papers",
		description:
			"Search for academic papers on arXiv via HuggingFace. Returns paper IDs, titles, and summaries as JSON.",
		promptSnippet: "Search arXiv papers by keyword",
		parameters: Type.Object({
			query: Type.String({
				description: "Search query, e.g. 'vision language models'",
			}),
			limit: Type.Optional(
				Type.Number({
					description: "Max results to return (default 5)",
					default: 5,
				}),
			),
		}),
		async execute(_id, params, signal) {
			const err = checkHf();
			if (err) return err;

			const result = await pi.exec(
				"hf",
				[
					"papers",
					"search",
					params.query,
					"--limit",
					String(params.limit ?? 5),
					"--format",
					"json",
				],
				{ signal },
			);

			if (result.code !== 0) {
				return {
					content: [{ type: "text", text: `Search failed: ${result.stderr}` }],
					isError: true,
				};
			}

			return { content: [{ type: "text", text: result.stdout }] };
		},
	});

	pi.registerTool({
		name: "get_paper_info",
		label: "Paper Info",
		description:
			"Get metadata for a specific arXiv paper: title, authors, abstract, keywords. Lighter than reading the full paper.",
		promptSnippet: "Get paper metadata (title, abstract, authors) by arXiv ID",
		parameters: Type.Object({
			arxiv_id: Type.String({
				description: "arXiv paper ID, e.g. '1706.03762'",
			}),
		}),
		async execute(_id, params, signal) {
			const err = checkHf();
			if (err) return err;

			const result = await pi.exec(
				"hf",
				["papers", "info", params.arxiv_id, "--format", "json"],
				{
					signal,
				},
			);

			if (result.code !== 0) {
				return {
					content: [{ type: "text", text: `Info failed: ${result.stderr}` }],
					isError: true,
				};
			}

			return { content: [{ type: "text", text: result.stdout }] };
		},
	});

	pi.registerTool({
		name: "read_paper",
		label: "Read Paper",
		description:
			"Read the full content of an arXiv paper as markdown. Can be large — prefer get_paper_info first to confirm the paper is relevant.",
		promptSnippet: "Read full arXiv paper content as markdown",
		parameters: Type.Object({
			arxiv_id: Type.String({
				description: "arXiv paper ID, e.g. '1706.03762'",
			}),
		}),
		async execute(_id, params, signal) {
			const err = checkHf();
			if (err) return err;

			const result = await pi.exec("hf", ["papers", "read", params.arxiv_id], {
				signal,
			});

			if (result.code !== 0) {
				return {
					content: [{ type: "text", text: `Read failed: ${result.stderr}` }],
					isError: true,
				};
			}

			return { content: [{ type: "text", text: result.stdout }] };
		},
	});

	// --- Commands ---

	pi.registerCommand("paper2code", {
		description: "Turn a research paper into a code repository",
		handler: async (args, ctx) => {
			if (!hfAvailable) {
				ctx.ui.notify(
					"hf CLI not found. Install: curl -LsSf https://hf.co/cli/install.sh | bash",
					"error",
				);
				return;
			}

			const query =
				args ||
				(await ctx.ui.input("Paper search", "Enter topic or arXiv ID:"));
			if (!query) return;

			const isArxivId = /^\d{4}\.\d{4,5}(v\d+)?$/.test(query.trim());

			if (isArxivId) {
				pi.sendUserMessage(
					`Read arXiv paper ${query.trim()} and build a working code repository from it.\n\n` +
						`Steps:\n` +
						`1. Use get_paper_info to preview the paper\n` +
						`2. Use read_paper to get the full content\n` +
						`3. Identify the core method/algorithm/architecture\n` +
						`4. Generate a clean repository:\n` +
						`   - README.md (paper summary + how to run)\n` +
						`   - Core implementation\n` +
						`   - Example/demo script\n` +
						`   - Dependencies file`,
				);
			} else {
				pi.sendUserMessage(
					`Search for papers about: "${query}"\n\n` +
						`Use search_papers to find relevant results, then present them so I can pick one to implement.`,
				);
			}
		},
	});

	pi.registerCommand("research2code", {
		description: "Turn a research problem into code + LaTeX paper",
		handler: async (args, ctx) => {
			if (!hfAvailable) {
				ctx.ui.notify(
					"hf CLI not found. Install: curl -LsSf https://hf.co/cli/install.sh | bash",
					"error",
				);
				return;
			}

			const problem =
				args ||
				(await ctx.ui.input("Research problem", "Describe the problem:"));
			if (!problem) return;

			pi.sendUserMessage(
				`I have a research problem. Help me turn it into a working code implementation, tests, and a LaTeX paper.\n\n` +
					`Problem: ${problem}\n\n` +
					`PHASE 1 — DISCOVER:\n` +
					`Use search_papers to find 3-5 related works. Use get_paper_info on the most relevant ones. If a paper looks central to the problem, use read_paper to get the full content.\n\n` +
					`PHASE 2 — PLAN (present this to me and STOP, wait for my approval before continuing):\n` +
					`Present a structured research plan:\n` +
					`  a) Problem framing — what exactly we're solving, scoped clearly\n` +
					`  b) Related work summary — what exists, what gaps remain, cite the papers found\n` +
					`  c) Proposed methodology — the approach, architecture, or algorithm\n` +
					`  d) Test strategy — how we validate this works. Consider what "testing" means for this specific problem: benchmarks, statistical tests, evaluation metrics, baselines, not just unit tests\n` +
					`  e) Paper outline — section plan for the LaTeX paper\n\n` +
					`Ask me to confirm or adjust the plan. Do NOT proceed until I approve.\n\n` +
					`PHASE 3 — BUILD (only after I approve the plan):\n` +
					`  a) Code repository:\n` +
					`     - README.md\n` +
					`     - Core implementation\n` +
					`     - Tests matching the test strategy from the plan\n` +
					`     - Example/demo script\n` +
					`     - Dependencies file\n` +
					`  b) LaTeX paper in paper/ directory:\n` +
					`     - paper/main.tex using standard article class\n` +
					`     - Sections: Abstract, Introduction, Related Work (cite papers found), Methodology, Implementation, Evaluation, Conclusion\n` +
					`     - paper/references.bib with real BibTeX entries from the related papers\n` +
					`     - paper/Makefile (pdflatex + bibtex build)\n\n` +
					`Write the paper in proper academic style. Cite all related works found in Phase 1.`,
			);
		},
	});
}
