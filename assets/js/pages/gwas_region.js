import Vue from 'vue';
import App from '../../vue/gwas_region.vue';

import { paramsFromUrl } from 'locuszoom/dist/ext/lz-dynamic-urls.min';
import { stateUrlMapping } from 'locuszoom-tabix/src/util/lz-helpers';

import { getBasicSources, createStudyLayout, getBasicLayout } from 'locuszoom-tabix/src/util/lz-helpers';
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
            lz_layout: getBasicLayout(state, panels, { responsive_resize: false }),
            study_names: [template_vars.label]
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

window.lz_widget = makePlot(window.template_args);
