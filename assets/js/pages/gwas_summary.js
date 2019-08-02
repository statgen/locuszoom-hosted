/**
 GWAS summary page (manhattan plots etc)
 */
/* global $ */
import {create_qq_plot, create_gwas_plot} from '../util/pheweb_plots';

import Tabulator from 'tabulator-tables';
import 'tabulator-tables/dist/css/bootstrap/tabulator_bootstrap4.css';
import _ from 'underscore';

function createTopHitsTable(selector, data) {
    // Filter the manhattan json to a subset of just peaks, sorted by pvalue (smallest first)
    data = data.filter(v => !!v.peak)
        .sort((a, b) => (a.pval - b.val))
        .map(item => {
            // FIXME: Synthetic field; feed a marker into pheweb loader code for better tables in the future
            // TODO: Get pheweb "nearest gene" annotations working (and make build agnostic)
            item.marker = `${item.chrom}: ${item.pos.toLocaleString()}`;
            return item;
        });

    return new Tabulator(selector, {
        data: data,
        pagination: 'local',
        paginationSize: 25,
        layout: 'fitColumns',
        placeholder: 'No peaks found in GWAS',
        columns: [
            {title: 'Marker', field: 'marker'},
            {title: 'p value', field: 'pval', formatter: cell => cell.getValue().toExponential(1)},
        ],
        initialSort: [
            {column: 'pval', dir: 'asc'}
        ]
    });
}


if (window.template_args.ingest_status === 2) {
    // If the file has been processed, show processed results
    window.addEventListener('load', function () {
        // Generate manhattan plot
        fetch(window.template_args.manhattan_url)
            .then(resp => {
                if (!resp.ok) {
                    throw Error('Could not fetch manhattan json');
                }
                return resp.json();
            })
            .then(data => {
                create_gwas_plot(data.variant_bins, data.unbinned_variants);
                return data;
            }).then((data) => {
                createTopHitsTable('#top-hits-table', data.unbinned_variants);
                return data;
            }).catch((err) => {
                console.error(err);
                document.getElementById('manhattan_plot_container').textContent = 'Could not fetch Manhattan plot data.';
            });

        // Generate QQ plot
        fetch(window.template_args.qq_url)
            .then(resp => {
                if (!resp.ok) {
                    throw Error('Could not fetch QQ json');
                }
                return resp.json();
            })
            .then(data => {
                _.sortBy(_.pairs(data.overall.gc_lambda), function (d) {
                    return -d[0];
                }).forEach(function (d, i) {
                    // FIXME: Manually constructed HTML; change
                    var text = 'GC lambda ' + d[0] + ': ' + d[1].toFixed(3);
                    if (i === 0) {
                        text = '<b>' + text + '</b>';
                    }
                    text = '<br>' + text;
                    $('.gc-control').append(text);
                });
                if (data.by_maf) {
                    create_qq_plot(data.by_maf, data.ci);
                } else {
                    create_qq_plot([{ maf_range: [0, 0.5], qq: data.overall.qq, count: data.overall.count }], data.ci);
                }
            }).catch(() => {
                document.getElementById('qq_plot_container').textContent = 'Could not fetch QQ plot data.';
            });
    });
}



