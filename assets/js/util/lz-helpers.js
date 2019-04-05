/**
 * Define LZ layout for data sources from hosted service API
 */

import LocusZoom from 'locuszoom';

import { sourceName} from 'locuszoom-tabix/src/util/lz-helpers';

LocusZoom.KnownDataSources.extend('AssociationLZ', 'AssociationApi', {
    getURL: function(state, chain,fields) {
        return `${this.url}?chrom=${state.chr}&start=${state.start}&end=${state.end}`;
    }
});


/**
 * Define sources used to add a study to the plot. Having this as a separate method is useful when dynamically
 * adding new panels.
 * @param label A dataset label
 * @param url
 * @returns {Array} Array with configuration options for each datasource required
 */
function createStudyAssocSources(label, url) {
    const name = sourceName(label);
    return [
        [`assoc_${name}`, ['AssociationApi', { url, params: { id_field: 'variant' } }]],
        [
            `credset_${name}`, [
                'CredibleSetLZ',
                { params: { fields: { log_pvalue: `assoc_${name}:log_pvalue` }, threshold: 0.95 } },
            ],
        ],
    ];
}

export { createStudyAssocSources };
