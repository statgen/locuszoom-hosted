/**
 * Render the "search" UI on the main landing page of the site.
 */

import Vue from 'vue';

import App from '../../vue/gwas_search.vue';

function makeWidget() {
    return new Vue({ render: h => h(App)})
        .$mount('#app');
}

window.widget = makeWidget();
