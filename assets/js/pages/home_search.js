/**
 * Render the "search" UI on the main landing page of the site.
 */

import Vue from 'vue';

import App from '../../vue/gwas_search.vue';
import VueResource from 'vue-resource';

Vue.use(VueResource);

function makeWidget(is_authenticated) {
    const app_params = { is_authenticated };
    return new Vue({ render: h => h(App, {
        props: app_params,
    })}).$mount('#app');
}

window.widget = makeWidget(window.template_args.is_authenticated);
