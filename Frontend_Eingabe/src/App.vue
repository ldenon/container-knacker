<template>
  <div>
    <h1>Eingabemaske Auftrag</h1>

    <!-- Dropdown 1: Länder -->
    <label for="land">Land wählen:</label>
    <select id="land" v-model="selectedCountry">
      <option v-for="(value, key) in containerweights" :key="key" :value="key">
        {{ key }}
      </option>
    </select>

    <!-- Zeige Hafen-Dropdown nur, wenn Land gewählt -->
    <div v-if="selectedCountry" class="form-row">
      <label for="region">Region wählen:</label>
      <select id="region" v-model="selectedRegion">
        <option v-for="region in containerweights[selectedCountry]" :key="region.Region" :value="region">
          {{ region.Region }}
        </option>
      </select>
    </div>

    <h4>Mögliche Container</h4>
    <div class="container-checkboxes">
      <label>
        <input type="checkbox" v-model="c20" id="c20" />
        Container 20"
      </label>
      <label>
        <input type="checkbox" v-model="c40" id="c40" />
        Container 40"
      </label>
      <label>
        <input type="checkbox" v-model="c40hc" id="c40hq" />
        Container 40" High Cube
      </label>
      <label>
        <input type="checkbox" v-model="c40hw" id="c40hw" />
        Container 40" Heavy Weight
      </label>
    </div>
  </div>

  <h4>Artikel eingeben</h4>

  <div v-for="(article, index) in articles" :key="index" class="artikel-container">
    <h5>Artikel {{ index + 1 }}</h5>

    <div class="form-row">
      <label class="product-name">Produktname:
        <input type="text" v-model="article.name" placeholder="z. B. Schrauben" />
      </label>

      <label class="label-anzahl">Anzahl:
        <input type="number" v-model.number="article.amount" min="1" />
      </label>

      <label class="label-gewicht">Gewicht (kg):
        <input type="number" v-model.number="article.weight" step="1" min="0" />
      </label>
    </div>

    <div class="form-row">
      <label>Form:
        <select v-model="article.shape">
          <option disabled value="">Bitte wählen</option>
          <option value="Rechteck">Rechteck</option>
          <option value="Zylinder">Zylinder</option>
        </select>
      </label>

      <!-- Rechteck-Maße nebeneinander -->
      <template v-if="article.shape === 'Rechteck'">
        <label>Höhe (cm):
          <input type="number" v-model.number="article.height" min="0" />
        </label>
        <label>Länge (cm):
          <input type="number" v-model.number="article.length" min="0" />
        </label>
        <label>Breite (cm):
          <input type="number" v-model.number="article.width" min="0" />
        </label>
      </template>

      <!-- Zylinder-Maße nebeneinander -->
      <template v-else-if="article.shape === 'Zylinder'">
        <label>Höhe (cm):
          <input type="number" v-model.number="article.height" min="0" />
        </label>
        <label>Durchmesser (cm):
          <input type="number" v-model.number="article.diameter" min="0" />
        </label>
      </template>
    </div>


    <!-- Palette Checkbox -->
    <div class="form-row">
      <input type="checkbox" v-model="article.usesPallet" :id="'pallet-' + index" />
      <label :for="'pallet-' + index">Palette verwendet?</label>
    </div>

    <!-- Palettenmaße -->
    <div class="form-row" v-if="article.usesPallet">
      <label>Höhe (cm):
        <input type="number" v-model.number="article.palletHeight" min="0" />
      </label>
      <label>Länge (cm):
        <input type="number" v-model.number="article.palletLength" min="0" />
      </label>
      <label>Breite (cm):
        <input type="number" v-model.number="article.palletWidth" min="0" />
      </label>
    </div>

    <!-- Zeile entfernen -->
    <div class="form-row">
      <button @click="removeArticle(index)" v-if="articles.length > 1">− Artikel entfernen</button>
    </div>
  </div>

  <!-- Artikel hinzufügen -->
  <div class="form-row">
    <button @click="addArticle">+ Artikel hinzufügen</button>
  </div>
  <button @click="exportJSON">JSON erzeugen</button>
</template>

<script setup>
import {
  selectedCountry,
  selectedRegion,
  containerweights,
  articles,
  addArticle,
  removeArticle
} from './useForm.js'  // Pfad anpassen

import { exportOrderJSONToFile } from './createJSON.js'
import { ref } from 'vue'
import './gui.css'

const c20 = ref(false)
const c40 = ref(false)
const c40hc = ref(false)
const c40hw = ref(false)

const exportJSON = () => {
  exportOrderJSONToFile({
    selectedCountry,
    selectedRegion,
    articles,
    c20,
    c40,
    c40hc,
    c40hw
  })
}

</script>

<style scoped></style>
