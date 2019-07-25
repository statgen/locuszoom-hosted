<script>
    /**
     * Represent a single GWAS item as a tile. Accepts an API representation of the data as a single prop
     */

    import bsCard from 'bootstrap-vue/es/components/card/card';

    export default {
        name: "gwas_description",
        props: ['study_data'],
        computed: {
            pmid_link() {
                const pmid = this.study_data.pmid;
                return pmid ? `https://www.ncbi.nlm.nih.gov/pubmed/${pmid}/` : null;
            },
        },
        components: { bsCard },
        filters: {
            date(value) {
                return value? new Date(value).toLocaleDateString() : '';
            }
        }
    }
</script>


<template>
<bs-card border-variant="light">
  <a :href="study_data.url" class="study-title">{{ study_data.label }}</a><br>
  <em class="text-muted">Uploaded by: {{ study_data.owner_name }}</em><br>
  <em class="text-muted">Created: {{ study_data.created | date }}</em><br>
  <span v-if="pmid_link">
    <a :href="pmid_link">{{ study_data.pmid }}</a><br>
  </span>
  <span v-if="study_data.is_public" class="badge badge-primary">Public</span>
  <span v-if="study_data.ingest_status === 0" class="badge badge-warning">Pending</span>
  <span v-if="study_data.ingest_status === 1" class="badge badge-danger">Error</span>
</bs-card>
</template>


<style scoped>
  .study-title {
    font-size: x-large;
  }
</style>
