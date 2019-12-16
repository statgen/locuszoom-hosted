<script>
    // Custom interactivity attached to the "GWAS Region/LocusZoom plot" page
    import BatchSpec from 'locuszoom-tabix/src/components/BatchSpec.vue';
    import BatchScroller from 'locuszoom-tabix/src/components/BatchScroller.vue';
    import PlotPanes from 'locuszoom-tabix/src/components/PlotPanes.vue';
    import RegionPicker from 'locuszoom-tabix/src/components/RegionPicker.vue';

    const MAX_REGION_SIZE = 1000000;

    export default {
        name: 'gwas_region',
        props: [
            'build', 'chr', 'start', 'end',
            'lz_layout',
            'lz_sources',
            'study_names',
            'top_hits_url'
        ],
        data() {
            return {
                // make constant available
                max_region_size: MAX_REGION_SIZE,
                message: '',
                message_class: '',

                // Allow initial state to be passed in, but then mutated as user navigates
                c_chr: this.chr,
                c_start: this.start,
                c_end: this.end,

                // Controls for "batch view" mode
                batch_mode_active: false,
                batch_mode_regions: [],
            };
        },
        methods: {
            activateBatchMode(regions) {
                this.batch_mode_active = true;
                this.batch_mode_regions = regions;
            },
            showMessage(message, style = 'text-danger') {
                this.message = message;
                this.message_class = style;
            },
            updateRegion(region) {
                // Receive new region config from toolbar
                this.c_chr = region.chr;
                this.c_start = region.start;
                this.c_end = region.end;
            },
            fetchTopHits() {
                // Used for batch mode "get top hits" button
                // Fetch pre-computed top loci, in sorted order, and return list of [ [chr, star, end] ] entries
                return fetch(this.top_hits_url)
                    .then(resp => {
                        if (resp.ok) {
                            return resp.json();
                        }
                        throw new Error('Could not retrieve results');
                    }).then(json => {
                        return json.unbinned_variants.filter(variant => !!variant.peak)
                            .sort((a,b) => b.neg_log_pvalue - a.neg_log_pvalue)
                            .map(variant => ({
                                    chr: variant.chrom,
                                    start: +variant.pos - Math.floor(MAX_REGION_SIZE / 2),
                                    end: +variant.pos + Math.floor(MAX_REGION_SIZE / 2)
                            }));
                    });
            }
        },
        components: { BatchSpec, BatchScroller, PlotPanes, RegionPicker }
    }
</script>

<template>
  <div>
    <div class="row" v-if="!batch_mode_active">
      <div class="col-md-4"></div>
      <div class="col-md-8 d-flex justify-content-end">
        <region-picker
            @ready="updateRegion"
            @fail="showMessage"
            class="float-right"
            :build="build"
            :max_range="max_region_size"
            search_url="https://portaldev.sph.umich.edu/api/v1/annotation/omnisearch/"/>
        <batch-spec class="ml-1"
                    :max_range="max_region_size"
                    @ready="activateBatchMode">
          <template #preset-button="{updateRegions}">
            <button class="btn btn-warning"  @click="updateRegions(fetchTopHits())">Get top hits</button>
          </template>
        </batch-spec>
      </div>
    </div>
    <div class="row" v-else>
      <div class="col-md-12">
        <batch-scroller :regions="batch_mode_regions"
                        @navigate="updateRegion"
                        @cancel="batch_mode_active = false"/>
      </div>
    </div>
    <div class="row" v-if="message">
      <div class="col-sm-12"><span :class="[message_class]">{{message}}</span></div>
    </div>
    <div class="row">
      <div class="col-md-12">
        <plot-panes ref="plotWidget"
                    :dynamic_urls="true"
                    :assoc_layout="lz_layout" :assoc_sources="lz_sources"
                    :study_names="study_names" :has_credible_sets="true"
                    :build="build"
                    :chr="c_chr" :start="c_start" :end="c_end" />
      </div>
    </div>
  </div>
</template>

<style scoped></style>
