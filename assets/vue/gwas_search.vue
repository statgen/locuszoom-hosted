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

    import GwasDescription from './gwas_description.vue';

    export default {
        name: "gwas_search",
        data() {
            return {
                search_status: 0, // 0 none, 1 pending, 2 finished, 3 failed
                search_results: [],

                // Search options
                search_text: '',
                filter_published: true,
                filter_mine: false,
            }
        },
        methods: {
            doSearch() {
                this.search_status = 1;

                const url = new URL("/api/v1/gwas/", window.location.origin);
                if (this.filter_published) {
                    url.searchParams.append('filter[pmid.isnull]', 'false');
                }
                if (this.filter_mine) {
                    url.searchParams.append('filter[me]', 'true');
                }
                if (this.search_text) {
                    url.searchParams.append('filter[search]', this.search_text);
                }

                fetch(url)
                    .then(resp => {
                        if (resp.ok) {
                            return resp.json()
                        } else {
                            throw new Error('Could not perform the requested search');
                        }
                    }).then(json => {
                        this.search_results = json.data.map(item => item.attributes);
                        this.search_status = 2;
                    }).catch(err => this.search_status = 3);
            }
        },
        mounted() {
            // When component first loads, render a default search
            this.doSearch();
        },
        components: {
            bsFormCheckbox,
            bsFormInput,
            bsFormGroup,
            bsInputGroup,
            bsInputGroupAppend,
            bsJumbotron,
            GwasDescription
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
            <bs-form-checkbox id="filter-mine" inline
                              v-model="filter_mine">Mine
            </bs-form-checkbox>  <!-- TODO: Only if user is logged in? -->
          </bs-form-group>

        </bs-jumbotron>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <div class="col-md-12">
          <div v-if="search_status === 1"> <!-- pending -->
            <div class="d-flex justify-content-center">
              <div class="spinner-border text-secondary" role="status">
                <span class="sr-only">Loading...</span>
              </div>
            </div>
          </div>
          <div v-else-if="search_status === 2"> <!-- finished -->
            <div class="row" v-for="item in search_results">
              <div class="col-md-12">
                <gwas-description :study_data="item"></gwas-description>
              </div>
            </div>
            <div v-if="search_results && !search_results.length">
              No results for the specified query.
            </div>
          </div>
          <div v-else-if="search_status === 3"> <!-- failed -->
            An error occurred. Please try your search again later.
          </div>

          <div class="row" v-for=""></div>
        </div>
      </div>
    </div>
  </div>
</template>


<style scoped>
  .search-field {
    background-color: #f0ffff;
  }
</style>
