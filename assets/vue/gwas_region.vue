<script>
    // Custom interactivity attached to the "GWAS Region/LocusZoom plot" page

    import BatchSpec from 'localzoom/src/components/BatchSpec.vue';
    import BatchScroller from 'localzoom/src/components/BatchScroller.vue';
    import GwasToolbar from 'localzoom/src/components/GwasToolbar.vue';
    import PlotPanes from 'localzoom/src/components/PlotPanes.vue';
    import RegionPicker from 'localzoom/src/components/RegionPicker.vue';
    import { DATA_TYPES } from 'localzoom/src/util/constants';
    import { activateUserLD } from 'localzoom/src/util/lz-helpers';
    import {setup_feature_metrics} from 'localzoom/src/util/metrics';

    const MAX_REGION_SIZE = 1000000;

    export default {
        name: 'gwas_region',
        props: [
            'genome_build', 'chr', 'start', 'end',
            'lz_layout',
            'lz_sources',
            'init_tracks',
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
                known_tracks: [...this.init_tracks],

                // Controls for "batch view" mode
                batch_mode_active: false,
                batch_mode_regions: [],
            };
        },
        methods: {
            activateMetrics() {
                // After plot is created, initiate metrics capture
                // TODO: This is a mite finicky; consider further refactoring in the future?
                this.$refs.plotWidget.$refs.assoc_plot.callPlot(setup_feature_metrics);
            },
            updateRegion({ chr, start, end }) {
                // Receive new region config from toolbar
                if (!chr || !start || !end) {
                    return;
                }
                this.c_chr = chr;
                this.c_start = start;
                this.c_end = end;
            },
            fetchTopHits() {
                // Used for batch mode "get top hits" button
                // Fetch pre-computed top loci, in sorted order, and return list of [ {chr, start, end} ] entries
                return fetch(this.top_hits_url)
                    .then(resp => {
                        if (resp.ok) {
                            return resp.json();
                        }
                        throw new Error('Could not retrieve results');
                    }).then(json => {
                        // Convert the list of peaks (top hits) into manageable nearby regions (target +/- 250k)
                        return json.unbinned_variants.filter(variant => !!variant.peak)
                            .sort((a, b) => b.neg_log_pvalue - a.neg_log_pvalue)
                            .map(variant => ({
                                chr: variant.chrom,
                                start: +variant.pos - 250000,
                                end: +variant.pos + 250000
                            }));
                    });
            },

            receiveTrackOptions(data_type, filename, display_name, source_configs, panel_configs, extra_plot_state) {
                if (!this.known_tracks.length) {
                    // If this is the first track added, allow the new track to suggest a region of interest and navigate there if relevant (mostly just GWAS)
                    this.updateRegion(extra_plot_state);

                    this.base_sources = getBasicSources(source_configs);
                    this.base_layout = getBasicLayout(extra_plot_state, panel_configs);

                    // Collect metrics for first plot loaded
                    count_region_view();
                } else {
                    // TODO: We presently ignore extra plot state (like region) when adding new tracks. Revisit for future data types.
                    this.$refs.plotWidget.addStudy(panel_configs, source_configs);
                    if (data_type === DATA_TYPES.PLINK_LD) {
                        this.$refs.plotWidget.$refs.assoc_plot.callPlot((plot) => {
                            activateUserLD(plot, display_name);
                        });
                    }
                }

            },
        },
        components: { BatchSpec, BatchScroller, GwasToolbar, PlotPanes, RegionPicker }
    }
</script>

<template>
  <div>
    <div class="row">
      <div class="col-md-12">
        <gwas-toolbar
          :batch_region_getter="fetchTopHits"
          :genome_build.sync="genome_build"
          :max_studies="6"
          :known_tracks="known_tracks"
          @add-tabix-track="receiveTrackOptions"
          @select-range="updateRegion"/>
      </div>
    </div>

    <div class="row">
      <div class="col-md-12">
        <plot-panes
            ref="plotWidget"
            :dynamic_urls="true"
            :base_layout="lz_layout"
            :base_sources="lz_sources"
            :known_tracks="known_tracks"
            :genome_build="genome_build"
            :chr="c_chr" :start="c_start" :end="c_end"
            @plot-created="activateMetrics"
        />
      </div>
    </div>
  </div>
</template>
