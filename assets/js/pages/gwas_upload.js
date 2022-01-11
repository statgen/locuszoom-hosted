/**
 * Upload your own GWAS page: custom validations (and eventually nicer upload interface)
 */


// 1. Custom validations for upload form
import Vue from 'vue';
import pako from 'pako';

import App from '../../vue/gwas_upload.vue';

import { _isHeader } from 'locuszoom/esm/ext/lz-parsers/gwas/sniffers';
import { makeGWASParser } from 'locuszoom/esm/ext/lz-parsers';

const PREVIEW_BYTES = 5000;  // enough for 50-100 lines
const MAX_UPLOAD_SIZE = 1048576 * 1250; // 1250 MiB # FIXME: Currently upload limit is only implemented in the frontend


class BaseReader {
    constructor(blob) {
        this.source = blob;
        this._is_text = false;

        this._data_promise = null;
    }

    getRows() {
        // Limited subset up to a defined PREVIEW_BYTES
        this._data_promise = this._getPreviewText(this.source);
        return this._data_promise;
    }

    /**
     * Wrapper for dalliance reader compatibility
     * @param callback
     * @param nLines
     * @returns String[] Raw unprocessed lines of data
     */
    fetchHeader(callback, { nLines = 30 }) {
        // Wrapper for dalliance reader compatibility. metaOnly argument not really supported,
        return this.getRows(nLines).then(callback);
    }

    /**
     * Handle fetching and parsing of data
     * @param blob
     * @returns {Promise<any>}
     * @private
     */
    _getPreviewText(blob) {
        const preview = blob.slice(0, PREVIEW_BYTES);
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsArrayBuffer(preview);
            reader.onload = (e) => {
                try {
                    let buffer = e.target.result;
                    let text;
                    if (!this._is_text) {
                        // Decompress data before converting bytes to string
                        buffer = pako.inflate(new Uint8Array(buffer));
                    }
                    // Assumption: external files will usually be something like UTF8 & common english letters.
                    // Since we're grabbing an arbitrary byte length, odds are the last row will be incomplete- drop it
                    text = String.fromCharCode.apply(null, new Uint8Array(buffer));
                    const rows = text.split(/[\r\n]+/g);
                    resolve(rows.slice(0, rows.length - 1));
                } catch (e) {
                    reject(e);
                }
            };
        });
    }
}

class TextReader extends BaseReader {
    constructor(blob) {
        super(blob);
        this._is_text = true;
    }
}

class GzipReader extends BaseReader {
    constructor(blob) {
        super(blob);
        this._is_text = false;
    }
}

function makeReader(filename, blob) {
    // Delegate based solely on file extension. No single extension for text file formats, or way to detect, eg savvy
    const ext = filename.split('.').pop();
    if (['gz', 'bgz'].includes(ext)) {
        return new GzipReader(blob);
    } else {
        return new TextReader(blob);
    }
}

/**
 * Validate that the rows are sorted (all chrom entries together, all rows in order)
 * @param rows Object[] A list of parsed data objects, each representing a row
 * @returns Boolean
 */
function validateSortOrder(rows) {
    const chrom_seen = {};
    let last_chrom = null;
    let last_pos = null;
    for (let i = 0; i < rows.length; i++) {
        // Is this the same as last chrom? If not, is it in chrom_seen?
        // If this is the same as last chrom, is the position > than previous one?
        const row = rows[i];
        const chrom = row.chromosome;
        const pos = row.position;
        if (row.chromosome !== last_chrom) {
            // We don't enforce sorting of chromosome labels (1,2,3), so long as all data for
            //  each chromosome is grouped together in the same block
            if (chrom_seen[chrom]) {
                return false;
            } else {
                chrom_seen[chrom] = true;
            }
            last_pos = null; // New chromosome, restart position counting
        }
        if (last_pos !== null && pos < last_pos) {  // Tabix allows two lines to have the same position (hence < , not <=)
            return false;
        }

        // Prep for next row
        last_chrom = chrom;
        last_pos = pos;
    }
    return true;
}

// Mount interactive functionality
const modal = new Vue({
    data() {
        // This is a slightly ugly hack to render an SFC that responds to data changed from outside the Vue
        // root instance. Bad code happens when you fight the framework....
        return {
            file_reader: null,
            show_modal: false,
        };
    },
    render(h) {
        return h(App, {
            props: { file_reader: this.file_reader, show_modal: this.show_modal },
        });
    }}).$mount('#vue-app');

window.modal = modal;
const fileField = document.getElementById('id_fileset-raw_gwas_file');
modal.$on('has_options', function (parser_options) { // Close with options selected
    document.getElementById('id_fileset-parser_options').value = JSON.stringify(parser_options);
    // Once options are received, mark form as valid
    fileField.setCustomValidity('');

    // Once we know how to parse the file, do some quick validation to decide if the rows are sorted
    const parser = makeGWASParser(parser_options);
    modal.file_reader.getRows().then((rows) => {
        const first_data_index = rows.findIndex(text => !_isHeader(text));

        let is_valid;
        try {
            const sample_data = rows.slice(first_data_index).map(row => parser(row));
            is_valid = validateSortOrder(sample_data);
        } catch (e) {
            // TODO: Improve UI representation of other parsing errors, like AF out of range
            console.error('error encountered', e);
            is_valid = false;
        }
        if (!is_valid) {  // slightly vague message; in rare cases some middle data rows may be unparseable
            fileField.setCustomValidity('Your file must be sorted by chromosome and position prior to upload.');
        }
    });
});

modal.$on('close', function() {
    modal.show_modal = false;  // Legacy of half-in, half-out vue usage
});

fileField.addEventListener('click', function(e) {
    // Force change event to fire even when the user selects the same file
    e.target.value = null;
});

fileField.addEventListener('change', function (event) {
    // Custom validators for uploaded file
    //  Ref: https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/HTML5/Constraint_validation#Limiting_the_size_of_a_file_before_its_upload
    fileField.setCustomValidity('');

    const file = event.target.files[0];
    const name = file.name;
    document.getElementById('id_fileset-parser_options').value = '';

    if (file.size > MAX_UPLOAD_SIZE) {
        fileField.setCustomValidity(`File exceeds the max upload size of ${MAX_UPLOAD_SIZE}`);
        return;
    }

    // Assume invalid until options are affirmatively received
    fileField.setCustomValidity('Must specify how to parse the file');
    // Show the modal and begin the process of selecting parser config options
    modal.file_reader = makeReader(name, file);
    modal.show_modal = true;
});
