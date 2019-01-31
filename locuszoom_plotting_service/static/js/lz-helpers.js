"use strict";

/**
 * Extensions to core LocusZoom to support plotting service
 */

LocusZoom.KnownDataSources.extend("AssociationLZ", "AssociationApi", {
    getURL: function(state, chain,fields) {
        return `${this.url}${this.params.analysis}/data/?chrom=${state.chr}&start=${state.start}&end=${state.end}`;
    }
});
