<script>
    /**
     * Show a paginated list of GWAS studies from a defined query
     */
    import VuePaginator from 'vuejs-paginator/src/VPaginator.vue'

    import GwasDescription from './gwas_description.vue';

    const STATUS = { 'onload': 0, 'pending': 1, 'finished': 2, 'failed': 3 };

    export default {
        name: "profile_studies",
        props: ['data_url'],
        beforeCreate() {
            this.STATUS = STATUS;
        },
        data() {
            return {
                search_status: STATUS.onload,

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
                this.search_status = STATUS.finished;
            }
        },
        components: { GwasDescription, VuePaginator },
    }
</script>


<template>
  <div>
    <div v-if="search_status === STATUS.finished">
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
    </div>
    <div v-else-if="search_status === STATUS.pending">
      <div class="d-flex justify-content-center">
        <div class="spinner-border text-secondary" role="status">
          <span class="sr-only">Loading...</span>
        </div>
      </div>
    </div>
    <div v-else-if="search_status === STATUS.error">
      An error occurred. Please try again later.
    </div>

    <vue-paginator :resource_url="data_url"
                   @update="updateResource"
                   @request_start="search_status = STATUS.pending"
                   @request_error="search_status = STATUS.error"
                   :options="page_options"
    ></vue-paginator>
  </div>
</template>

<style scoped></style>
