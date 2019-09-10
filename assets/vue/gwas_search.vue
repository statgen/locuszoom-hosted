<script>
    /**
     * Implement the homepage search interface in Vue.js
     */

    import {
        BFormCheckbox,
        BFormInput,
        BFormGroup,
        BInputGroup,
        BInputGroupAppend,
        BJumbotron
    } from 'bootstrap-vue/esm/';

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
                filter_published: false,
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
            BFormCheckbox,
            BFormInput,
            BFormGroup,
            BInputGroup,
            BInputGroupAppend,
            BJumbotron,
            GenericGwasList,
        }
    }
</script>


<template>
  <div>
    <div class="row">
      <div class="col-md-12">
        <b-jumbotron :fluid="true" lead="Create and share interactive GWAS Plots" class="search-field">
          <b-input-group>
            <b-form-input type="text" placeholder="Search by analysis name or PMID" v-model="search_text"/>
            <b-input-group-append>
              <button class="btn btn-info" @click="doSearch">Search</button>
            </b-input-group-append>
          </b-input-group>
          <b-form-group>
            Filter(s):
            <b-form-checkbox id="filter-published" inline
                              v-model="filter_published">Published
            </b-form-checkbox>
            <b-form-checkbox v-if="is_authenticated"
                              id="filter-mine" inline
                              v-model="filter_mine">Mine
            </b-form-checkbox>
          </b-form-group>

        </b-jumbotron>
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
