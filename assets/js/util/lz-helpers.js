/**
 * Define LZ layout for data sources from hosted service API
 */

import LocusZoom from 'locuszoom';

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
    return [
        [`assoc_${label}`, ['AssociationApi', { url, params: { id_field: 'variant' } }]],
        [
            'credset_assoc', [
                'CredibleSetLZ',
                { params: { fields: { log_pvalue: `assoc_${label}:log_pvalue` }, threshold: 0.95 } },
            ],
        ],
    ];
}

export { createStudyAssocSources };
