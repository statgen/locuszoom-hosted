<script>
    /**
     * Show a paginated list of GWAS studies from a defined query
     */
    import VuePaginator from 'vuejs-paginator/src/VPaginator.vue'

    import GwasDescription from './gwas_description.vue';

    export default {
        name: "profile_studies",
        props: ['data_url'],
        data() {
            return {
                items: [], // fetched by paginator widget
                page_options: {
                    remote_current_page: "meta.pagination.page",
                    remote_prev_page_url: "links.prev",
                    remote_next_page_url: "links.next",
                    remote_last_page: "meta.pagination.pages",
                }
            };
        },
        methods: {
            updateResource(data) {
                this.items = data.map(item => item.attributes);
            }
        },
        components: { GwasDescription, VuePaginator },
    }
</script>


<template>
  <div>
    <div v-if="items.length">
      <div class="row" v-for="item in items">
        <div class="col-md-12">
          <gwas-description :study_data="item"></gwas-description>
        </div>
      </div>
    </div>
    <div v-else>
      No results found. <a href="/gwas/upload/">Upload your data.</a>
    </div>
    <vue-paginator :resource_url="data_url"
                   @update="updateResource"
                   :options="page_options"
    ></vue-paginator>
  </div>
</template>

<style scoped></style>
