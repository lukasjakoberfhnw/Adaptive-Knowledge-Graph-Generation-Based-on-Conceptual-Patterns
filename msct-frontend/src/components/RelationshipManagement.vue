<script setup lang="ts">
import { onMounted, ref } from 'vue';
import api from '../api/api.ts'; // Adjust the path as necessary
import NodeChooser from './NodeChooser.vue'; // Import the NodeChooser component

const props = defineProps<{
    selectedTokens: any[];
}>()

const source = ref({
    id: "",
    text: "",
    type: ""
});

const target = ref({
    id: "",
    text: "",
    type: ""
});


const showNodeChooser = ref(false); // This will control the visibility of the node chooser
const nodeChooserSource = ref<string | null>(null); // source | target

const addProperty = ref(false); // This will control the visibility of the property input field
const newRelationshipName = ref("");
const possibleRelationships = ref<any[]>([]); // This will hold the list of entities
const existingRelationships = ref<any[]>([]); // This will hold the list of existing relationships between the selected entities

const $emit = defineEmits(['close', 'create-relationship']); // Define the events that this component can emit

// can get tricky if we would want to connect more than two tokens.. for now, assume only two

onMounted(() => {
    if(props.selectedTokens.length > 1) {
        source.value = props.selectedTokens[0]; // Use the first selected token as source
        target.value = props.selectedTokens[1] || { id: "", text: "", type: "" }; // Use the second selected token as target, if available
    } else if (props.selectedTokens.length === 1) {
        source.value = props.selectedTokens[0]; // Use the only selected token as source
    } else {
        console.warn('No tokens selected for relationship management');
    }

    // fetch possible relationships from the API
    api.get('/relationship-types')
        .then(response => {
            possibleRelationships.value = response.data.relationship_types || [];
            console.log('Possible relationships fetched:', possibleRelationships.value);
        })
        .catch(error => {
            console.error('Error fetching possible relationships:', error);
        });
});

function createRelationship() {
    console.log('Creating new relationship with name:', newRelationshipName.value); 
    let target_id = null;
    if(target.value.id !== "") {
        target_id = target.value.id;
    }

    if(addProperty.value) {
        console.log('Adding property:', newRelationshipName.value, 'with value:', target.value.text);
        target_id = null;
    } else if (target_id === null) {
        console.error('Target ID is required for creating a relationship');
        return;
    }

    api.post('/relationships', {
        source_id: source.value.id,
        source_type: source.value.type,
        target_id: target_id,
        target_type: target.value.type,
        relationship_type: newRelationshipName.value,
        target_text: target.value.text,
        // maybe add - hlc for derived from
    })
    .then(response => {
        console.log('Relationship created successfully:', response.data);
        $emit('create-relationship', response.data);
        $emit('close'); 
    })
    .catch(error => {
        console.error('Error creating relationship:', error);
    });
}

function switchSourceAndTarget() {
    // if((source.value.type !== "Entity") || (target.value.type !== "Entity")) {
    //     console.warn('Both source and target must be entities to switch them.');
    //     return;
    // }
    if(addProperty.value) {
        console.warn('Cannot switch source and target when adding a property.');
        return;
    }

    const temp = source.value;
    source.value = target.value;
    target.value = temp;
    console.log('Switched source and target:', source.value, target.value);
}

function chooseNode(source: string) {
    nodeChooserSource.value = source; // Set the source for the node chooser
    showNodeChooser.value = true; // Show the node chooser
}


</script>

<template>
    <div class="overlay" @click="$emit('close')"></div>
    <div class="relationship-management-modal">
        <h2>Relationship Management</h2>
        <p>Selected Tokens: {{ selectedTokens.length }}</p>

        <h3>Selected Tokens</h3>
        <ul>
            <li v-for="(token, index) in selectedTokens" :key="index">
                {{ token.text }} ({{ token.type }})
            </li>
        </ul>

        <!--
        possibly let user search for other relationships that already exist... to make sure the user does not create a new one - 

        <h3>Existing relationships (possibly add count/strength?)</h3>

        <p style="color:red">Allow user to search for relationships here</p>
        <ul>
            <li v-for="(rel, index) in existingRelationships" :key="index">
                <span>{{ rel.text }}</span>
            </li>
        </ul> -->

        <NodeChooser
            v-if="showNodeChooser"
            :selected_node="nodeChooserSource === 'target' ? target : source"
            @select="(node) => {
                nodeChooserSource === 'target' ? target = node : source = node
                showNodeChooser = false;
                }"
            @close="showNodeChooser = false">
        </NodeChooser>

        <h3>Create new Relationship</h3>
        <form @submit.prevent="$emit('create-relationship')">
            <button v-if="target.id != ''" @click="switchSourceAndTarget()">Switch Source and Target</button>
            <button @click="addProperty = !addProperty">Toggle Add Relationship/Property</button>
            <div class="relationship-inputs">
                <div class="relationship-source">
                    <label for="source">Source: (node chooser)</label>
                    <input class="pointy" @click="chooseNode('source')" type="text" id="source" v-model="source.id" readonly />
                </div>
                <div v-if="!addProperty" class="relationship-inputs">
                    <div class="relationship-name">
                        <label for="name">Relationship Name:</label>
                        <input
                            list="relationship-types"
                            type="text"
                            id="relation"
                            v-model="newRelationshipName"
                            required
                        />
                        <datalist id="relationship-types">
                            <option v-for="relation in possibleRelationships" :key="relation" :value="relation">{{ relation }}</option>
                        </datalist>
                    </div>
                    <div class="relationship-target">
                        <label for="target">Target (node chooser - id):</label>
                        <input class="pointy" @click="chooseNode('target')" type="text" id="target" v-model="target.id" readonly />
                    </div>
                </div>
                <div v-else class="relationship-inputs">
                    <div class="relationship-name">
                        <label for="property">Property:</label>
                        <input type="text" id="property" v-model="newRelationshipName" required />
                    </div>
                    <div class="relationship-target">
                        <label for="value">Value:</label>
                        <input type="text" id="value" v-model="target.text" />
                    </div>
                </div>
            </div>
            <button type="submit" @click="createRelationship()">Create</button>
        </form>
        <button @click="$emit('close')">Close</button>
    </div>
</template>

<style scoped>
.relationship-management-modal {
    position: fixed;
    z-index: 1000;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background-color: black;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    border: 1px solid var(--color-border);
}

.overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.8);
    z-index: 999;
}

.relationship-source,
.relationship-target,
.relationship-name {
    margin-bottom: 10px;
    display: flex;
    flex-direction: column;
}

.relationship-inputs {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
}

.pointy {
    cursor: pointer;
}
</style>
