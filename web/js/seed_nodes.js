import { app } from "../../../scripts/app.js";

app.registerExtension({
	name: "SeedAPI.DynamicInputs",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "Seedream4Unified") {
			console.log("Registering Seedream4Unified dynamic inputs");

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
