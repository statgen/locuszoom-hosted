<script>
    /**
     * Show a list of studies on the profile page
     */
    import VuePaginator from 'vuejs-paginator/src/VPaginator.vue'

    import GwasDescription from './gwas_description.vue';

    export default {
        name: "profile_studies",
        props: ['data_url', 'page_size'],
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
    <div class="row" v-for="item in items">
      <div class="col-md-12">
        <gwas-description :study_data="item"></gwas-description>
      </div>
    </div>
    <vue-paginator resource_url="/api/v1/gwas/?filter[me]=true"
                   @update="updateResource"
                   :options="page_options"
    ></vue-paginator>
  </div>
</template>

<style scoped></style>
