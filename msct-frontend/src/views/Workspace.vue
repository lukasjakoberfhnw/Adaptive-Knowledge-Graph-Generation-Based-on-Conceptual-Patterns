<template>
    <div class="workspace">
        <h1>Workspace</h1>
        <p>Welcome to the workspace!</p>
        <p>This is a placeholder for your workspace content.</p>
        
        <div>
            <h2>Recent Extractions</h2>
            <p>View your recent extractions and their details.</p>
            <ul>
                <li v-for="creation in recentCreations" :key="creation.id">
                    <a @click="redirector.redirectToView(creation.id, creation.labels[0])">{{ creation.labels[0] }}: {{ creation.textual_identifier }}</a>
                </li>
            </ul>
        </div>

        <div>
            <h2>General Overview (MLC)</h2>
            <p>Most important MLCs are displayed here.</p>
            <ul>
                <li v-for="mlc in importantMLCs" :key="mlc.id">
                    <a @click="redirector.redirectToView(mlc.id, 'MLC')">{{ mlc.text }} ({{ mlc.strength }})</a>
                </li>
            </ul>
        </div>
        <div>
            <h2>Exploratory Chains</h2>
            <p>View possible matches, interesting patterns, etc --- 2-gram checker</p>
            <ul>
                <li v-for="sequence in interestingSequences" :key="sequence.id">
                    {{ sequence.phrase }} ({{ sequence.frequency }})
                </li>
            </ul>
        </div>
        <div>
            <h2>Rulesets</h2>
            <p>Manage and apply rulesets to your data.</p>
        </div>
        <div>
            <h2>Tools</h2>
            <p>Access various tools for data manipulation and analysis.</p>
        </div>
    </div>
</template>
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import api from '../api/api.ts'; // Adjust the path as necessary
// import redirector from stores '../stores/redirector.ts'; // Uncomment if you need to use redirector
import { useRedirectStore } from '../stores/redirects.ts';


const redirector = useRedirectStore(); // Initialize the redirector store
const importantMLCs = ref<any[]>([]); // Reactive variable to hold important MLCs
const recentCreations = ref<any[]>([]); // Reactive variable for recent extractions
const interestingSequences = ref<any[]>([]); // Reactive variable for interesting sequences

onMounted(() => {
    console.log('Workspace component mounted');
    // Example: api.get('/workspace-data').then(response => { ... });

    api.get("/workspace/important-mlcs")
        .then(response => {
            importantMLCs.value = response.data; // Update the reactive variable with fetched data
        })
        .catch(error => {
            console.error('Error fetching important MLCs:', error);
        });

    api.get("/workspace/recent-creations")
        .then(response => {
            recentCreations.value = response.data; // Update the reactive variable with fetched data
        })
        .catch(error => {
            console.error('Error fetching recent creations:', error);
        });

    api.get("/workspace/n-grams")
        .then(response => {
            interestingSequences.value = response.data; // Update the reactive variable with fetched data
        })
        .catch(error => {
            console.error('Error fetching interesting sequences:', error);
        });
});

</script>
<style scoped>
</style>