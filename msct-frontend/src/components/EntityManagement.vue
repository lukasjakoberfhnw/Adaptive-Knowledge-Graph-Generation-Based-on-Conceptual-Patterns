<script setup lang="ts">
import { onMounted, ref } from 'vue';
import api from '../api/api.ts'; // Adjust the path as necessary
import NodeChooser from './NodeChooser.vue'; // Import the NodeChooser component

const props = defineProps<{
  selectedTokens: any[];
  mlc_index: number;
  hlc_id: string;
}>()
const newEntityName = ref("");
const newEntityTextualIdentifier = ref("");
const newEntityType = ref(''); // retrieve possible types first from api
const entities = ref<any[]>([]); // This will hold the list of entities
const showNodeChooser = ref(false); // Control visibility of the node chooser modal
const chosenEntity = ref<any>(null); // Store the chosen entity for linking

const entities_fetch_error = ref("");

const $emit = defineEmits(['close', 'create-entity']); // Define the events that this component can emit

onMounted(() => {
    newEntityName.value = props.selectedTokens.map(token => token.text).join(' ');
    newEntityTextualIdentifier.value = props.selectedTokens.map(token => token.text).join(' '); // Default to the concatenated text of selected tokens
  console.log('EntityManagement component mounted with selected tokens:', props.selectedTokens);
  entities.value = []; // Initialize entities with an empty array

    // fetch entities that are linked to the selected tokens by their mlc id in search parameter
  if (props.selectedTokens.length > 0) {
    const mlcIds = props.selectedTokens.map(token => token.id).join(',');
    console.log('Fetching entities for MLC IDs:', mlcIds);
    api.get(`/entities-from-mlcs/${mlcIds}`) // Adjust the API endpoint as necessary --- might be interesting to send the full sentence
      .then(response => {
        entities.value = response.data || [];
        console.log('Fetched entities:', entities.value);
      })
      .catch(error => {
        console.error('Error fetching entities:', error);
        // if code 404, then no entities found
        if (error.response && error.response.status === 404) {
          entities_fetch_error.value = "No entities found for the selected tokens.";
        } else {
          entities_fetch_error.value = "Error fetching entities: " + error.message;
        }
      });
  }
});

function linkToEntity(entity: any) {
  console.log('Linking to entity:', entity);
  api.post('/link-entity', {
    entity_id: entity.id,
    token_ids: props.selectedTokens.map(token => token.id),
    hlc_id: props.hlc_id,
    order: props.mlc_index
  })
    .then(response => {
      console.log('Entity linked successfully:', response.data);
        $emit('create-entity', { id: entity.id, text: entity.text });
        $emit('close'); 
    })
    .catch(error => {
      console.error('Error linking entity:', error);
    });
}

function createEntity(){
    console.log('Creating new entity with name:', newEntityName.value);
    api.post('/entities', {
        id: "", // api will overwrite this... temporary error probably because of cache
        text: newEntityName.value,
        textual_identifier: newEntityTextualIdentifier.value, // Assuming this is the same as the name
        mlc_token_ids: props.selectedTokens.map(token => token.id),
        from_hlc: true,
        hlc_id: props.hlc_id,
        mlc_token_index: props.mlc_index
    })
        .then(response => {
        console.log('New entity created successfully:', response.data);
        $emit('create-entity', {id: response.data.id, text: newEntityName}); // Emit an event to notify the parent component
        $emit('close'); // Close the modal after creation
        })
        .catch(error => {
        console.error('Error creating entity:', error);
        });
}

</script>

<template>
    <div class="overlay" @click="$emit('close')"></div>
    <div class="entity-management-modal">
        <h2>Entity Management</h2>
        <p>Selected Tokens: {{ selectedTokens.length }}</p>
        <p>Index / Order: {{ props.mlc_index }}</p>

        <hr />

        <NodeChooser
            v-if="showNodeChooser"
            :selected_node="undefined"
            @select="(node) => {
                chosenEntity = node;
                showNodeChooser = false;
                }"
            @close="showNodeChooser = false">
        </NodeChooser>

        <h3>Selected Tokens</h3>
        <ul>
            <li v-for="(token, index) in selectedTokens" :key="index">
                {{ token.text }} ({{ token.type }})
            </li>
        </ul>

        <hr />

        <h3>Link to existinig Entity?</h3>
        <!-- possibly search for other entities -->
         <button @click="showNodeChooser = true">Search for Entity to Link</button>
         <div v-if="chosenEntity">
         <p>
            <strong>Chosen Entity:</strong> {{ chosenEntity.text }} ({{ chosenEntity.id }})
        </p>
        <button @click="linkToEntity(chosenEntity)">Link to this Entity</button>
        </div>
        
        <h4>Existing Entities</h4>
        <ul>
            <li v-for="(entity, index) in entities" :key="index">
                <button @click="linkToEntity(entity)">{{ entity.text }} ({{ entity.textual_identifier }})</button>
            </li>
        </ul>
        <p v-if="entities_fetch_error">{{ entities_fetch_error }}</p>

        <hr />

        <h3>Create new Entity</h3>
        <form @submit.prevent="$emit('create-entity')" class="entity-form">
          <div>
            <div style="display:flex; flex-direction: column;">
              <label for="entityType">Entity Text:</label>
              <input type="text" placeholder="Entity Name" v-model="newEntityName" required />
            </div>
            <div style="display:flex; flex-direction: column;">
              <label for="entityTextualIdentifier">Entity Textual Identifier:</label>
              <input type="text" placeholder="Textual Identifier" v-model="newEntityTextualIdentifier" required />
            </div>
          </div>
          <button type="submit" @click="createEntity()">Create</button>
        </form>

        <button @click="$emit('close')">Close</button>
    </div>
</template>

<style scoped>
.entity-management-modal {
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

.entity-form {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.entity-form div {
    display: flex;
    flex-direction: column;
}

.entity-form input {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    min-width: 200px;
}

.overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 999;
}

hr {
    margin: 10px 0;
    margin-top: 20px;
    border: none;
    border-top: 1px solid var(--color-border);
}
</style>
