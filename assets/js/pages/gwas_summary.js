/**
 GWAS summary page (manhattan plots etc)
 */
/* global $ */
import {create_qq_plot, create_gwas_plot} from '../util/pheweb_plots';

import Tabulator from 'tabulator-tables';
import 'tabulator-tables/dist/css/bootstrap/tabulator_bootstrap4.css';
import { toPairs, sortBy } from 'lodash';

function createTopHitsTable(selector, data, region_url) {
    // Filter the manhattan json to a subset of just peaks, largest -log10p first
    data = data.filter(v => !!v.peak)
        .map(item => {
            // Synthetic field; manhattan loader doesn't provide ref/alt information
            const ref_alt = (item.ref && item.alt) ? ` ${item.ref}/${item.alt}` : '';
            item.marker = `${item.chrom}: ${item.pos.toLocaleString()}${ref_alt}`;
            return item;
        });

    return new Tabulator(selector, {
        data: data,
        pagination: 'local',
        paginationSize: 10,
        layout: 'fitColumns',
        placeholder: 'No peaks found in GWAS',
        columns: [
            {
                title: 'Marker', field: 'marker', formatter: 'link',
                sorter(a, b, aRow, bRow, column, dir, sorterParams) {
                    // Sort by chrom, then position
                    const a_data = aRow.getData();
                    const b_data = bRow.getData();
                    return (a_data.chrom).localeCompare(b_data.chrom, undefined, {numeric: true})
                        || a_data.pos - b_data.pos;
                },
                formatterParams: {
                    label: (cell) => cell.getData().marker,
                    url: (cell) => {
                        const data = cell.getRow().getData();
                        const start = Math.max(data.pos - 250000, 0);
                        const end = data.pos + 250000;

                        const base = new URL(region_url, window.location.origin);
                        base.searchParams.set('chrom', data.chrom);
                        base.searchParams.set('start', start);
                        base.searchParams.set('end', end);
                        return base;
                    }
                },
            },
            {
                title: 'rsID',
                field: 'rsid',
            },
            {
                title: 'Nearest gene(s)',
                field: 'nearest_genes',
                sorter: 'string',
                formatter: cell => {
                    const genes = cell.getValue() || [];  // There will be studies that predate this feature, and won't have a value
                    // Convert the list of ensg/symbol objects to a string- eventually we can add links to ext DB
                    return genes.map(gene => gene.symbol).join(', ');
                }
            },
            {title: '-log<sub>10</sub>(p)', field: 'neg_log_pvalue', formatter: cell => (+cell.getValue()).toFixed(3)},
        ],
        initialSort: [
            {column: 'neg_log_pvalue', dir: 'desc'}
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
                createTopHitsTable('#top-hits-table', data.unbinned_variants, window.template_args.region_url);
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
                sortBy(toPairs(data.overall.gc_lambda), function (d) {
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
            }).catch((e) => {
                console.error(e);
                document.getElementById('qq_plot_container').textContent = 'Could not fetch QQ plot data.';
            });
    });
}



