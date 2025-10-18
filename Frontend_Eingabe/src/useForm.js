import { ref, watch } from 'vue'
import containerweights from '@/data/Containergewichte.json'

export const selectedCountry = ref('')
export const selectedRegion = ref('')
export { containerweights }

export const articles = ref([
  {
    name: '',
    amount: 1,
    weight: 0,
    shape: '',
    length: null,
    width: null,
    height: null,
    diameter: null,
    usesPallet: false,
    palletLength: null,
    palletWidth: null,
    palletHeight: null
  }
])

export const addArticle = () => {
  articles.value.push({
    name: '',
    amount: 1,
    weight: 0,
    shape: '',
    length: null,
    width: null,
    height: null,
    diameter: null,
    usesPallet: false,
    palletLength: null,
    palletWidth: null,
    palletHeight: null
  })
}

export const removeArticle = (index) => {
  articles.value.splice(index, 1)
}

watch(selectedCountry, (newCountry) => {
  const regionen = containerweights[newCountry]
  if (regionen && regionen.length === 1) {
    selectedRegion.value = regionen[0].Region
  } else {
    selectedRegion.value = ''
  }
})
