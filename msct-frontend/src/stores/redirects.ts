import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useRouter } from 'vue-router'

export const useRedirectStore = defineStore('redirector', () => {
    const router = useRouter()
    function redirectToView(id: string, type: string) {
        switch (type) {
            case 'Extraction':
                router.push({ name: 'extractionDetail', params: { id } })
                break
            case 'HLC':
                router.push({ name: 'High Level Concept Detail', params: { id } })
                break
            case 'MLC':
                router.push({ name: 'Medium Level Concept Detail', params: { id } })
                break
            case 'Entity':
                router.push({ name: 'Entity Detail', params: { id } })
                break
            default:
                console.error('Unknown type for redirect:', type)
        }
    }

  return { redirectToView }
})
