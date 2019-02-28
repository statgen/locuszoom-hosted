/**
 * Upload your own GWAS page: custom validations (and eventually nicer upload interface)
 * TODO: Incorporate some elements of LocalZoom (eg modals)
 */


// 1. Custom validations for upload form

import pako from 'pako';

const PREVIEW_BYTES = 5000;  // enough for 50-100 lines

const MISSING_VALUES = ['', '.', 'NA', 'N/A', 'n/a', 'nan', '-nan', 'NaN', '-NaN', 'null', 'NULL'];

class BaseReader {
    constructor(blob) {
        this.source = blob;
        this._is_text = false;

        this._data_promise = null;
    }
    _getFields(line) {
        // Assumes file tab delimited (for now)
        return line.trim().split(/\t/);
    }
    getRows() {
        // Limited subset up to a defined PREVIEW_BYTES
        this._data_promise = this._getPreviewText(this.source)
            .then(rows => rows.map(this._getFields));
        return this._data_promise;
    }

    /**
     * Return the last item that qualifies as a header row.
     * @returns {null|*}
     */
    getColumnLabels() {
        return (this._data_promise || this.getRows())
            .then(rows => {
                for (let i = 0; i < rows.length; i++) {
                    const fields = rows[i];
                    const is_header = fields[0].startsWith('#') ||
                        (fields.every(isNaN) && !fields.some(v => MISSING_VALUES.includes(v)));
                    if (!is_header) {
                        return rows[i - 1] || [];
                    }
                }
                return [];
            });
    }
    /**
     * Wrapper for dalliance reader compatibility
     * @param callback
     * @param nLines
     * @returns String[] Raw unprocessed lines of data
     */
    fetchHeaders(callback, { nLines = 30 }) {
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
                    text = String.fromCharCode.apply(null, new Uint8Array(buffer));
                    resolve(text.split(/[\r\n]+/g));
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

const fileField = document.getElementById('id_raw_gwas_file');

fileField.addEventListener('change', function (e) {
    const file = event.target.files[0];
    const name = file.name;
    const reader = makeReader(name, file);
    reader.getColumnLabels()
        .then(console.log);
});
