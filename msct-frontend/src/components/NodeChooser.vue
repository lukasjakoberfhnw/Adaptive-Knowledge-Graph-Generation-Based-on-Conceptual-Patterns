<template>
    <div @keyup.esc="$emit('close')" class="node-chooser-overlay">
        <div class="node-chooser">
            <div v-if="props.selected_node.id" style="margin-bottom: 20px;">
                <h3>Selected Node</h3>
                <div style="display:flex; flex-direction:column; border: 1px solid rgba(0,0,0,0.4); padding: 10px;">
                    <p v-if="props.selected_node.id">ID: {{ props.selected_node.id }}</p>
                    <p v-if="props.selected_node.textual_identifier">Textual identifier: {{ props.selected_node.textual_identifier }}</p>
                    <p v-if="props.selected_node.text">Text: {{ props.selected_node.text.length > 40 ? props.selected_node.text.substring(0, 40) : props.selected_node.text }}</p>
                    <p v-if="props.selected_node.type">Type: {{ props.selected_node.type }}</p>
                </div>
            </div>

            <h3>Choose node</h3>
            <p v-if="searchQuery.length < 2">Type at least 3 characters to search for nodes</p>
            <div>
                <div>
                    <label for="searchType">Search Type:</label>
                    <select v-model="searchType" id="searchType">
                        <option value="" selected>All Types</option>
                        <option value=":MLC">MLC</option>
                        <option value=":HLC">HLC</option>
                        <option value=":Entity">Entity</option>
                        <option value=":Extraction">Extraction</option>
                    </select>
                </div>
                <div>
                    <label for="searchQuery">Search Query:</label>
                    <input autofocus @keyup.enter="searchNodes" type="text" ref="searchInput" v-model="searchQuery" placeholder="Search for nodes..." />
                </div>
                <button @click="searchNodes">Search</button>
                <p v-if="loading">Loading...</p>
            </div>

            <p v-if="nodes.length === 0 && searchQuery.length >= 2">No nodes found</p>
            <div class="results">
                <ul>
                    <li class="pointy" v-for="node in nodes" :key="node.id" @click="$emit('select', {...node, type: node.labels[0]})">
                        <a>{{ node.labels[0] }}: {{ node.textual_identifier ? node.textual_identifier : node.text }} ({{ node.id }})</a>
                    </li>
                </ul>
            </div>
            <button @click="$emit('close')">Close</button>
        </div>
    </div>
</template>

<script setup lang="ts">
// this is a component to choose a node from the graph
import { ref, watch, onMounted } from "vue";
import api from "../api/api.ts";

const searchType = ref("")
const searchQuery = ref("");
const nodes = ref<any[]>([]); // This will hold the list of nodes fetched from the API
const loading = ref(false); // This will indicate if the API call is in progress

const props = defineProps({
    selected_node: {
        type: Object,
        default: () => ({})
    }
});

const emit = defineEmits(["select", "close"]);

onMounted(() => {
    const searchInput = document.querySelector("input[type='text']");
    if (searchInput) {
        (searchInput as HTMLInputElement).focus();
    }
});

// watch(searchQuery, (newQuery) => {
//     if (newQuery.length > 2) {
//         api.get("/nodes/search", { params: { query: newQuery } })
//             .then((response) => {
//                 nodes.value = response.data || [];
//             })
//             .catch((error) => {
//                 console.error("API Error:", error);
//             });
//     } else {
//         nodes.value = []; // Clear nodes if search query is too short
//     }
// });

function searchNodes() {
    nodes.value = []; // Clear previous results
    loading.value = true; // Set loading state

    api.get("/nodes/search", { params: { query: searchQuery.value, node_type: searchType.value } })
        .then((response) => {
            nodes.value = response.data || [];
            loading.value = false;
        })
        .catch((error) => {
            console.error("API Error:", error);
            loading.value = false;
        });
}

</script>

<style scoped>

.results {
    max-height: 60vh;
    overflow-y: auto;
}

.node-chooser-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
}

.node-chooser {
    background-color: #00003d;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    max-height: 100vh;
    overflow-y: auto;
}

.pointy {
    cursor: pointer;
}

.pointy:hover {
    background-color: rgba(50, 200, 50, 0.2);
}
</style>