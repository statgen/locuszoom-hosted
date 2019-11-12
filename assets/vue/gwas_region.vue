<script>
    // Custom interactivity attached to the "GWAS Region/LocusZoom plot" page
    import PlotPanes from 'locuszoom-tabix/src/components/PlotPanes.vue';
    import RegionPicker from 'locuszoom-tabix/src/components/RegionPicker.vue';

    export default {
        name: 'gwas_region',
        props: [
            'build', 'chr', 'start', 'end',
            'lz_layout',
            'lz_sources',
            'study_names',
        ],
        data() {
            return {
                message: '',
                message_class: '',

                // Allow initial state to be passed in, but then mutated as user navigates
                c_chr: this.chr,
                c_start: this.start,
                c_end: this.end


            };
        },
        methods: {
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
        },
        components: { PlotPanes, RegionPicker }
    }
</script>

<template>
  <div>
    <div class="row">
      <div class="col-md-8"></div>
      <div class="col-md-4">
        <region-picker
            @ready="updateRegion"
            @fail="showMessage"
            class="float-right"
            :build="build"
            :max_range="500000"
            search_url="https://portaldev.sph.umich.edu/api/v1/annotation/omnisearch/"/>
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
