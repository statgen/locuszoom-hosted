<script>

    import GwasDescription from './gwas_description.vue';
    export default {
        name: "gwas_search",
        data() {
            return {
                search_status: 0, // 0 none, 1 pending, 2 finished, 3 failed
                search_results: [],

                // Search options
                search_text: '',
                filter_published: false,
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
        components: { GwasDescription }
    }
</script>


<template>
  <div>
    <div class="row">
      <div class="col-md-12">
        <input type="text" placeholder="Search by analysis name or PMID" v-model="search_text"><button @click="doSearch">Search</button><br>
        Filter(s):
        <label><input type="checkbox" id="filter-published" v-model="filter_published">Published</label>
        <label><input type="checkbox" id="filter-mine" v-model="filter_mine">Mine</label>  <!-- TODO: Only if user is logged in? -->
      </div>
    </div>
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
</template>


<style scoped></style>
