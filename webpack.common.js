/* eslint-env node */

// TODO: Sort out process for deploying built assets
// Sample dev/prod core webpack config, based on:
//   https://webpack.js.org/guides/production/
//   https://owais.lone.pw/blog/webpack-plus-reactjs-and-django/

const path = require('path');
const BundleTracker = require('webpack-bundle-tracker');
const FriendlyErrorsWebpackPlugin = require('friendly-errors-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const VueLoaderPlugin = require('vue-loader/lib/plugin');

const assetPath = path.resolve(__dirname, 'assets/js');
const outputPath = path.resolve(__dirname, 'assets/webpack_bundles');


module.exports = {
    context: __dirname,
    entry: {
        // List of individual per-page JS files to be included
        home_search: path.resolve(assetPath, 'pages/home_search.js'),
        gwas_upload: path.resolve(assetPath, 'pages/gwas_upload.js'),
        gwas_summary: path.resolve(assetPath, 'pages/gwas_summary.js'),
        gwas_region: path.resolve(assetPath, 'pages/gwas_region.js'),
    },
    plugins: [
        new FriendlyErrorsWebpackPlugin(),
        new CleanWebpackPlugin([outputPath], { watch: true }),
        new VueLoaderPlugin(),
        new BundleTracker({ filename: './webpack-stats.json' }),
    ],
    resolve: {
        alias: {
            '@': assetPath
        },
        modules: [
            'node_modules'
        ],
    },
    module: {
        rules: [
            {
                test: /\.m?js$/,
                exclude: file => (/node_modules/.test(file) && !/\.vue\.js/.test(file)),
                use: { loader: 'babel-loader', options: { presets: ['@babel/preset-env'] } }
            },
            {
                test: /\.js$/,
                use: ['source-map-loader'],
                enforce: 'pre',
            },
            {
                test: /\.vue$/,
                loader: 'vue-loader',
            },
            {
                test: /\.css$/,
                use: [
                    'vue-style-loader',
                    'css-loader',
                ]
            }
        ]
    },
    output: {
        path: outputPath,
        filename: '[name]-[hash].js',
    },
};
