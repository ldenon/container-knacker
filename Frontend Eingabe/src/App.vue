<script setup></script>

<template>
  <div>
    <h1>
      Stückliste
    </h1>

  </div>
  <main>
    <label for = "p1">Produkt 1   </label>
    <input id="p1" v-model.number="formData.p1" type="number" />
    <br>
    <br>
    <label for = "p2">Produkt 2   </label>
    <input id="p2" v-model.number="formData.p2" type="number" />
    <br>
    <br>
    <label for = "p3">Produkt 3   </label>
    <input id="p3" v-model.number="formData.p3" type="number" />
    <br>
    <br>
    <label for = "p4">Produkt 4   </label>
    <input id="p4" v-model.number="formData.p4" type="number" />
    <br>
    <br>
    <label for = "p5">Produkt 5   </label>
    <input id="p5" v-model.number="formData.p5" type="number" />
    <br>
    <br>
    <label for = "p6">Produkt 6   </label>
    <input id="p6" v-model.number="formData.p6" type="number" />
  </main>

  <button>Export</button>
</template>

<style scoped>

div{

}
</style>
