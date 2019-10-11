<script>
    /**
     * Represent a single GWAS item as a tile. Accepts an API representation of the data as a single prop
     */

    import { BCard } from 'bootstrap-vue/esm/';

    export default {
        name: "gwas_description",
        props: ['study_data'],
        computed: {
            pmid_link() {
                const pmid = this.study_data.pmid;
                return pmid ? `https://www.ncbi.nlm.nih.gov/pubmed/${pmid}/` : null;
            },
        },
        components: { BCard },
        filters: {
            date(value) {
                return value? new Date(value).toLocaleDateString() : '';
            }
        }
    }
</script>


<template>
<b-card border-variant="light">
  <a :href="study_data.url" class="study-title align-middle text-info">{{ study_data.label }}</a>
  <span v-if="study_data.is_public" class="badge badge-info align-middle">Public</span>
  <span v-else class="badge badge-warning align-middle">Private</span>
  <span v-if="study_data.ingest_status === 0" class="badge badge-warning align-middle">Pending</span>
  <span v-if="study_data.ingest_status === 1" class="badge badge-danger align-middle">Error</span>
  <span v-if="pmid_link">
    <a :href="pmid_link" class="badge badge-dark align-middle" target="_blank">PubMed</a><br>
  </span>
  <br>

  <span v-if="study_data.study_name" class="text-secondary">Study: <em>{{study_data.study_name}}</em><br></span>
  <span class="text-muted">Uploaded: <em class="text-muted">{{ study_data.created | date }}</em> by
    <em>{{ study_data.owner_name }}</em></span><br>
</b-card>
</template>


<style scoped>
  .study-title {
    font-size: x-large;
  }
</style>
