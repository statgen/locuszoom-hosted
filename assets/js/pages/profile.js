/**
 * Render the "list of studies" UI on the main landing page of the site.
 */

import Vue from 'vue';
import VueResource from 'vue-resource';

Vue.use(VueResource);

import App from '../../vue/generic_gwas_list.vue';

function makeWidget() {
    return new Vue({ render: h => h(App, {
        props: {
            'data_url': '/api/v1/gwas/user-all/',
        }})})
        .$mount('#app');
}

window.widget = makeWidget();
