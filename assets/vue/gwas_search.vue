<script>
    /**
     * Implement the homepage search interface in Vue.js
     */

    import bsFormCheckbox from 'bootstrap-vue/es/components/form-checkbox/form-checkbox';
    import bsFormInput from 'bootstrap-vue/es/components/form-input/form-input';
    import bsFormGroup from 'bootstrap-vue/es/components/form-group/form-group';
    import bsInputGroup from 'bootstrap-vue/es/components/input-group/input-group';
    import bsInputGroupAppend from 'bootstrap-vue/es/components/input-group/input-group-append';
    import bsJumbotron from 'bootstrap-vue/es/components/jumbotron/jumbotron';

    import GenericGwasList from './generic_gwas_list.vue';

    export default {
        name: "gwas_search",
        props: {'is_authenticated': {type: Boolean, default: false}},
        data() {
            const base_url = '/api/v1/gwas/';
            return {
                // Search options
                base_url: base_url,
                search_url: base_url, // Updated when calling doSearch()
                search_text: '',
                filter_published: true,
                filter_mine: false,
            };
        },
        methods: {
            doSearch() {
                const url = new URL(this.base_url, window.location.origin);
                if (this.filter_published) {
                    url.searchParams.append('filter[pmid.isnull]', 'false');
                }
                if (this.filter_mine) {
                    url.searchParams.append('filter[me]', 'true');
                }
                if (this.search_text) {
                    url.searchParams.append('filter[search]', this.search_text);
                }
                this.search_url = url.toString();
            }
        },
        components: {
            bsFormCheckbox,
            bsFormInput,
            bsFormGroup,
            bsInputGroup,
            bsInputGroupAppend,
            bsJumbotron,
            GenericGwasList,
        }
    }
</script>


<template>
  <div>
    <div class="row">
      <div class="col-md-12">
        <bs-jumbotron :fluid="true" lead="Create and share interactive GWAS Plots" class="search-field">
          <bs-input-group>
            <bs-form-input type="text" placeholder="Search by analysis name or PMID" v-model="search_text"/>
            <bs-input-group-append>
              <button class="btn btn-info" @click="doSearch">Search</button>
            </bs-input-group-append>
          </bs-input-group>
          <bs-form-group>
            Filter(s):
            <bs-form-checkbox id="filter-published" inline
                              v-model="filter_published">Published
            </bs-form-checkbox>
            <bs-form-checkbox v-if="is_authenticated"
                              id="filter-mine" inline
                              v-model="filter_mine">Mine
            </bs-form-checkbox>
          </bs-form-group>

        </bs-jumbotron>
      </div>
    </div>
    <div class="container">
      <generic-gwas-list :data_url="search_url"></generic-gwas-list>
    </div>
  </div>
</template>


<style scoped>
  .search-field {
    background-color: #f0ffff;
  }
</style>
