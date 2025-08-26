<template>
    <div class="compare-view">
        <h1>Compare View</h1>
        <p>This is the compare view where you can compare different extractions -- only use extractions.</p>
        
        <NodeChooser
            v-if="showNodeChooser"
            :selected_node="nodeChooserSource === 'node_1' ? node_1 : node_2"
            @select="(node) => {
                nodeChooserSource === 'node_1' ? node_1 = node : node_2 = node
                showNodeChooser = false;
                }"
            @close="showNodeChooser = false">
        </NodeChooser>
        
        <!-- Add your comparison logic and components here 
         
            1. select one node
            2. select another node

            View intersection results
        -->
        <label for="node_1">Choose a node</label>
        <button @click="chooseNode('node_1')">Choose node 1</button>
        <p>Selected node: {{ node_1.textual_identifier ? node_1.textual_identifier : node_1.text }} ({{ node_1.id }})</p>

        <label for="node_2">Choose another node</label>
        <button @click="chooseNode('node_2')">Choose node 2</button>
        <p>Selected node: {{ node_2.textual_identifier ? node_2.textual_identifier : node_2.text }} ({{ node_2.id }})</p>

        <button v-if="node_1.id && node_2.id" @click="compareNodes">Compare Nodes</button>
        
        <div v-if="comparisonResult">
            <h2>Comparison Result</h2>
            <table>
                <thead>
                    <tr>
                        <th>Phrase</th>
                        <th>{{ node_1.textual_identifier ? node_1.textual_identifier : node_1.text }} Frequency</th>
                        <th>{{ node_2.textual_identifier ? node_2.textual_identifier : node_2.text }} Frequency</th>
                        <th>Total Frequency</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="comparison in comparisonResult">
                        <td>{{ comparison.phrase }}</td>
                        <td>{{ comparison.extraction1_freq }}</td>
                        <td>{{ comparison.extraction2_freq }}</td>
                        <td>{{ comparison.total_frequency }}</td>
                    </tr>
                </tbody>
            </table>
            <p v-if="comparisonResult.length === 0">No common phrases found.</p>
        </div>
    </div>
</template>
<script lang="ts" setup>
import NodeChooser from '@/components/NodeChooser.vue';
import { ref } from 'vue';
import api from '@/api/api';

const showNodeChooser = ref(false); // This will control the visibility of the node chooser
const nodeChooserSource = ref<string | null>(null); // source | target
const chosenEntity = ref<any>(null); // Store the chosen entity for linking

const comparisonResult = ref<any>(null);

const node_1 = ref({
    id: "",
    text: "",
    type: "",
    textual_identifier: ""
});

const node_2 = ref({
    id: "",
    text: "",
    type: "",
    textual_identifier: ""
});

function chooseNode(source: string) {
    nodeChooserSource.value = source; // Set the source for the node chooser
    showNodeChooser.value = true; // Show the node chooser
}

function compareNodes() {
    if (node_1.value.id === "" || node_2.value.id === "") {
        console.warn('Please select both nodes before comparing.');
        return;
    }
    comparisonResult.value = null; // Reset previous comparison result

    api.get("/compare-extractions", {
        params: {
            extraction_id_1: node_1.value.id,
            extraction_id_2: node_2.value.id
        }
    }).then(
        (response) => {
            comparisonResult.value = response.data;
            console.log("Comparison Result:", comparisonResult.value);
        }
    ).catch((error) => {
        console.error("API Error:", error);
    });
}

</script>
<style scoped>
table {
    width: 100%;
    border-collapse: collapse;
}
th, td {
    border: 1px solid #ddd;
    padding: 8px;
}
th {
    text-align: left;
    background-color: darkslategrey;
    font-weight:bold;
}
td {
    text-align: left;
}

.compare-view {
    padding: 20px;
}

</style>