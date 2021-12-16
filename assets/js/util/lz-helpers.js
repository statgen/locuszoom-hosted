/**
 * Define LZ layout for data sources from hosted service API
 */

import LocusZoom from 'locuszoom';
import 'locuszoom/dist/locuszoom.css';

import { sourceName} from 'localzoom/src/util/lz-helpers';
import {AssociationLZ} from 'locuszoom/esm/data/adapters';


class AssociationApi extends AssociationLZ {
    _getURL(request_options) {
        const { chr, start, end } = request_options;
        const base = new URL(this._url, window.location.origin);
        base.searchParams.set('chrom', chr);
        base.searchParams.set('start', start);
        base.searchParams.set('end', end);
        return base;
    }

    annotateData(records) {
        // Our API is a mix of portaldev and zorp field names. Smooth out differences.
        // TODO: Eventually it would be nice to use a consistent field spec. Key blocker is lz layout.
        return records.map(item => {
            item.stderr_beta = item.se;
            return item;
        });
    }
}

LocusZoom.Adapters.add('AssociationApi', AssociationApi);

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
        [`assoc_gwas_${name}`, ['AssociationApi', { url }]],
        [
            `credset_gwas_${name}`, [
                'CredibleSetLZ',
                { threshold: 0.95 },
            ],
        ],
    ];
}

export { createStudyAssocSources };
