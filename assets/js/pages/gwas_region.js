import Vue from 'vue';
import App from '../../vue/gwas_region.vue';

import { paramsFromUrl } from 'locuszoom/esm/ext/lz-dynamic-urls';

import { stateUrlMapping, getBasicSources, createStudyLayout, getBasicLayout } from 'localzoom/src/util/lz-helpers';
import count_region_view from 'localzoom/src/util/metrics';
import { createStudyAssocSources } from '../util/lz-helpers';

function makePlot(template_vars) {
    let state = paramsFromUrl(stateUrlMapping);
    // Fill in default params for any values not provided by the url
    state.genome_build = template_vars.build;
    state = Object.assign(
        { chr: template_vars.chr, start: template_vars.start, end: template_vars.end },
        state
    );
    const assoc_sources = createStudyAssocSources(template_vars.label, template_vars.assoc_base_url);
    const panels = createStudyLayout(template_vars.label, {
        credible_sets: true,
        gwas_catalog: true
    }, template_vars.build);
    const app_params = Object.assign(
        {
            lz_sources: getBasicSources(assoc_sources),
            lz_layout: getBasicLayout(state, panels, { responsive_resize: true }),
            study_names: [template_vars.label],
            top_hits_url: template_vars.top_hits_url,
        }, template_vars,
        {
            genome_build: template_vars.build,
            chr: state.chr,
            start: +state.start ,
            end: +state.end
        });
    return new Vue({ render: h => h(App, {
        props: app_params,
    })}).$mount('#app');
}

// On page load, generate a plot, and send Google Analytics metrics for first plot rendered
window.lz_widget = makePlot(window.template_args);
count_region_view();
