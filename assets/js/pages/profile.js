/**
 * Render the "list of studies" UI on the main landing page of the site.
 */

import Vue from 'vue';
import VueResource from 'vue-resource';

Vue.use(VueResource);

import App from '../../vue/profile_studies.vue';

function makeWidget() {
    return new Vue({ render: h => h(App)})
        .$mount('#app');
}

window.widget = makeWidget();
