<template>
	<div id="loader" v-if="loading_extraction_creation">
		<h1>Loading...</h1>
	</div>
	<div class="extraction">
		<h1>Extraction</h1>

		<button @click="extraction_creation_state = !extraction_creation_state">
			{{ extraction_creation_state ? "Hide New Extraction Box" : "Create New Extraction" }}
		</button>

		<!-- text input for extraction -->
		<div v-if="extraction_creation_state" class="create-extraction">
			<button @click="extract_from_document = !extract_from_document">{{ extract_from_document ? "Extract from Text" : "Extract from Document" }}</button>
			<div v-if="!extract_from_document" :class="show_text_big ? 'full-screen-textarea' : ''">
				<label for="extraction-text">Text for Extraction:</label><a style="float:right" href="#" @click.prevent="show_text_big ? show_text_big = false : show_text_big = true">{{ show_text_big ? "Minimize" : "Enlarge" }}</a>
				<textarea
					id="extraction-text"
					type="text"
					placeholder="Enter text to extract from"
					rows="8"
					cols="50"
					data-gramm="false"
					data-gramm_editor="false"
					data-enable-grammarly="false"
				></textarea>
			</div>
			<div v-else>
				<!-- upload document for text to be extracted from -->
				<label for="extraction-document">Upload Document for Extraction:</label>
				<input
					id="extraction-document"
					type="file"
					accept=".txt,.pdf,.docx"
					@change="(e) => getTextFromDocument(e)"
				/>
				<p v-if="extraction_creation_document">
					Selected Document: {{ extraction_creation_document.name }}
				</p>
				<p v-else>No document selected.</p>
			</div>
			<label for="source-id">Source ID:</label>
			<select id="source-id" v-model="extraction_creation_object.source_id">
				<option value="" disabled selected>Select a source</option>
				<option
					v-for="source in availableSources"
					:key="source.source_id"
					:value="source.id"
				>
					{{ source.id }} - {{ source.name }}
				</option>
			</select>
			<label for="textual-identifier">Textual Identifier:</label>
			<input
				id="textual-identifier"
				type="text"
				v-model="extraction_creation_object.textual_identifier"
				placeholder="Enter textual identifier"
				autocomplete="off"
			/>

			<button @click="createExtraction">Create Extraction</button>
		</div>
		<!-- list of past 10 extractions -->
		<table>
			<thead>
				<tr>
					<th>ID</th>
					<th>Created At</th>
					<th>Textual Identifier</th>
					<th>Source</th>
				</tr>
			</thead>
			<tbody>
				<tr
					@click="pushToExtractionDetails(extraction.extraction_id)"
					v-for="extraction in extractionList"
					:key="extraction.extraction_id"
				>
					<td>{{ extraction.extraction_id }}</td>
					<td>{{ new Date(extraction.creation_time).toLocaleString() }}</td>
					<td>{{ extraction.textual_identifier }}</td>
					<td>{{ extraction.source_id }}</td>
				</tr>
			</tbody>
		</table>

		<p style="color: lightblue" v-if="loading_existing_extractions">Loading existing extractions...</p>
		<p v-if="!loading_existing_extractions && extractionList.length === 0">No existing extractions found.</p>

		<!-- button for creating a new extraction -->
	</div>
</template>

<script setup lang="ts">
// test api call here
import router from "@/router/index.ts"
import api from "../api/api.ts"
import { ref, onMounted, watch, nextTick } from "vue"

const text = ref("put text here")
const extractionList = ref<Array<any>>([]) // would be nice to have a type here... for now, using any
const extraction_creation_state = ref(false)
const availableSources = ref<Array<any>>([]) // would be nice to have a type here... for now, using any
const extraction_creation_object = ref({
	text: "",
	source_id: "",
	textual_identifier: "",
})
const extraction_creation_document = ref<File | null>(null)
const extract_from_document = ref(false)
const show_text_big = ref(false)
const loading_extraction_creation = ref(false)
const loading_existing_extractions = ref(false)

const insertTextNextTick = ref(false);
let textToInsert = ""

watch(insertTextNextTick, (newValue) => {
	if (newValue) {
		nextTick(() => {
			const textArea = document.getElementById("extraction-text")
			if (textArea) {
				(textArea as HTMLTextAreaElement).value = textToInsert
			} else {
				console.error("Text area not found")
			}
			insertTextNextTick.value = false // Reset the flag after inserting text
		})
	}
})

onMounted(() => {
	loading_existing_extractions.value = true
	api.get("/extractions")
		.then((response) => {
			console.log("API Response:", response.data)
			extractionList.value = response.data || []
		})
		.catch((error) => {
			console.error("API Error:", error)
		}).finally(() => {
			loading_existing_extractions.value = false
		})

	api.get("/sources")
		.then((response) => {
			console.log("Sources API Response:", response.data)
			availableSources.value = response.data || []
		})
		.catch((error) => {
			console.error("Sources API Error:", error)
		})
})

function pushToExtractionDetails(extractionId: string) {
	console.log("Navigating to extraction details for ID:", extractionId)
	router
		.push({
			name: "extractionDetail",
			params: { id: extractionId },
		})
		.catch((err) => {
			console.error("Navigation error:", err)
		})
}

function createExtraction() {
	// get text from textarea using id
	loading_extraction_creation.value = true

	const textArea = document.getElementById("extraction-text")
	extraction_creation_object.value.text = textArea ? (textArea as HTMLTextAreaElement).value : ""

	if (!extraction_creation_object.value.text) {
		alert("Please enter text for extraction.")
		return
	}

	api.post("/extractions", extraction_creation_object.value)
		.then((response) => {
			console.log("Extraction created:", response.data)
			extractionList.value.unshift(response.data) // Add new extraction to the top of the list
			extraction_creation_object.value = { text: "", source_id: "", textual_identifier: "" } // Reset form
			loading_extraction_creation.value = false

		})
		.catch((error) => {
			console.error("Error creating extraction:", error)
			alert("Failed to create extraction. Please try again.")
			loading_extraction_creation.value = false
		})
}

function getTextFromDocument(e: any) {
	const file = e.target.files[0]
	const formData = new FormData()
	extraction_creation_document.value = file // Store the selected file
	formData.append("file", file)

	// Check if a file is selected
	console.log("Selected file:", file)
	console.log("Form data:", formData)

	// This WILL show the file contents:
	for (let [key, value] of formData.entries()) {
	console.log(key, value);
	}

	if (!file) {
		console.log("No file selected.")
		return
	}

	api.post("/text-from-pdf", formData, {
			headers: {
				"Content-Type": "multipart/form-data",
			},
	})
		.then((response) => {
			console.log("Text extracted from document:", response.data)
			extract_from_document.value = false // Switch back to text input mode

			// set text on textarea using javascript instead of vue for performance
			insertTextNextTick.value = true
			textToInsert = response.data.extracted_text || ""

			extraction_creation_document.value = null // Reset the document input
		})
		.catch((error) => {
			console.error("Error extracting text from document:", error)
			alert("Failed to extract text from document. Please try again.")
		})
}
</script>

<style scoped>
#loader {
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background: rgba(0, 0, 0, 0.8);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 1000;
}

td {
	cursor: pointer;
}

.create-extraction {
	margin: 20px 0;
	padding: 10px;
	border: 1px solid #ccc;
	border-radius: 5px;
	display: flex;
	flex-direction: column;
}

.create-extraction label {
	margin-bottom: 5px;
}

.create-extraction textarea,
.create-extraction input,
.create-extraction select {
	width: 100%;
	margin-bottom: 10px;
	padding: 8px;
	border: 1px solid #ccc;
	border-radius: 4px;
	font-family: "Arial", sans-serif;
}

/* will be a single component for the future with additional tools */
.full-screen-textarea {
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background: rgba(0,0,0,0.8);
	z-index: 1000;
	padding: 20px;
	box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
	overflow: auto;
}

.full-screen-textarea textarea {
	width: 100%;
	height: calc(100% - 50px);
	resize: none;
	font-size: 16px;
}
</style>
