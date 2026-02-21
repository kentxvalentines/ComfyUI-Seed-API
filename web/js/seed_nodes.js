import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// Listen for executed event to auto-populate draft_task_id
// This works because SeedancePro15VideoNode has OUTPUT_NODE = True and returns ui data
api.addEventListener("executed", ({ detail }) => {
	const { node: nodeId, output } = detail;

	// Check if this execution has a draft_task_id in ui output
	if (output && output.draft_task_id && output.draft_task_id[0]) {
		const draftTaskId = output.draft_task_id[0];

		// Find the node in the graph
		const node = app.graph.getNodeById(nodeId);
		if (!node || node.type !== "SeedancePro15Video") {
			return;
		}

		console.log("[SeedAPI] Received draft_task_id from node:", draftTaskId);

		// Check if draft_mode widget is enabled
		const draftModeWidget = node.widgets?.find(w => w.name === "draft_mode");
		if (!draftModeWidget || !draftModeWidget.value) {
			return; // Only auto-populate when draft_mode was True
		}

		// Find and update the draft_task_id widget
		const draftTaskIdWidget = node.widgets?.find(w => w.name === "draft_task_id");
		if (draftTaskIdWidget && draftTaskId) {
			console.log(`[SeedAPI] Auto-populating draft_task_id: ${draftTaskId}`);
			draftTaskIdWidget.value = draftTaskId;

			// Mark the graph as changed so it can be saved
			app.graph.setDirtyCanvas(true, true);
		}
	}
});

app.registerExtension({
	name: "SeedAPI.DynamicInputs",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "Seedream4Unified" || nodeData.name === "Seedream45Unified") {
			console.log(`Registering ${nodeData.name} dynamic inputs`);

			const onConnectionsChange = nodeType.prototype.onConnectionsChange;
			nodeType.prototype.onConnectionsChange = function (type, index, connected, link_info) {
				console.log("onConnectionsChange called:", { type, index, connected, link_info });

				const stackTrace = new Error().stack;

				// Don't modify during graph loading or pasting
				if (stackTrace.includes('loadGraphData') || stackTrace.includes('pasteFromClipboard')) {
					console.log("Skipping due to loadGraphData or pasteFromClipboard");
					return;
				}

				if (!link_info) {
					console.log("No link_info, returning");
					return;
				}

				// Only handle input connections (type 1), ignore output connections (type 2)
				if (type === 1) {
					// Remove disconnected inputs
					if (!connected && this.inputs.length > 1) {
						if (!stackTrace.includes('LGraphNode.prototype.connect') &&
							!stackTrace.includes('LGraphNode.connect') &&
							!stackTrace.includes('loadGraphData')) {
							console.log("Removing input at index:", index);
							this.removeInput(index);
						}
					}

					// Renumber only IMAGE type inputs to keep them sequential
					let slot_i = 1;
					for (let i = 0; i < this.inputs.length; i++) {
						if (this.inputs[i].type === "IMAGE") {
							this.inputs[i].name = `image${slot_i}`;
							slot_i++;
						}
					}
					console.log("After renumbering, next slot_i:", slot_i);

					// When connecting, add a new input slot if we don't have 10 IMAGE inputs yet
					if (connected && slot_i <= 10) {
						console.log("Adding new input: image" + slot_i);
						this.addInput(`image${slot_i}`, "IMAGE");
					}
				}

				// Call the original function if it exists
				if (onConnectionsChange) {
					return onConnectionsChange.apply(this, arguments);
				}
			};
		}
	}
});
