<template>
    <div class="search-view">
        <div class="search-container">
            <h1>Search</h1>
                <select v-model="searchType" id="searchType">
                    <option value="" selected>All Types</option>
                    <option value=":MLC">MLC</option>
                    <option value=":HLC">HLC</option>
                    <option value=":Entity">Entity</option>
                    <option value=":Extraction">Extraction</option>
                </select>
            <input
                v-model="searchQuery"
                type="text"
                placeholder="Search for a term..."
                @keyup.enter="performSearch"
            />
            <button @click="performSearch">Search</button>
        </div>
        <div class="results-container" v-if="results.length">
            <h2>Results:</h2>
            <ul>
                <li v-for="result in results" :key="result.id">
                    <a @click="redirectStore.redirectToView(result.id, result.labels[0])">{{ result.labels[0] }}: {{ result.textual_identifier ? result.textual_identifier : result.text.length > 300 ? result.text.substring(0, 300) + "..." : result.text }}</a>
                </li>
            </ul>
        </div>
        <div class="no-results" v-else-if="searchQuery && !loading && searchCount > 0 && results.length === 0">
            <p>No results found for "{{ searchQuery }}".</p>
        </div>
        <div class="loading" v-if="loading">
            <p>Loading...</p>
        </div>
    </div>
</template>
<script setup lang="ts">
import { ref } from 'vue';
import api from "../api/api.ts"
import { useRedirectStore } from '../stores/redirects.ts';

const searchQuery = ref('');
const searchType = ref('');
const results = ref<any[]>([]);
const loading = ref(false);
const searchCount = ref(0);

const redirectStore = useRedirectStore();

function performSearch() {
    if (!searchQuery.value.trim()) {
        results.value = [];
        return;
    }

    searchCount.value = searchCount.value + 1; // Reset search count
    results.value = []; // Clear previous results

    // search with query and type
    loading.value = true;
    api.get("/nodes/search", {
        params: { query: searchQuery.value, node_type: searchType.value }
    })
        .then(response => {
            console.log("Search Results:", response.data);
            results.value = response.data || [];
        })
        .catch(error => {
            console.error("Search Error:", error);
            results.value = [];
        })
        .finally(() => {
            loading.value = false;
        });
}
</script>
<style scoped>
.search-view {
    padding: 20px;
}
.search-container {
    margin-bottom: 20px;
}
.search-container input, select {
    padding: 10px;
    width: 300px;
    margin-right: 10px;
}
.search-container button {
    padding: 10px 15px;
}
.results-container {
    margin-top: 20px;
}
.results-container ul {
    list-style-type: none;
    padding: 0;
}
.results-container li {
    padding: 5px 0;
}
.no-results {
    margin-top: 20px;
    color: #888;
}
.loading {
    margin-top: 20px;
    color: #888;
}
</style>