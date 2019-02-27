/* eslint-env node */

// TODO: Sort out process for deploying built assets
// Sample dev/prod core webpack config, based on:
//   https://webpack.js.org/guides/production/
//   https://owais.lone.pw/blog/webpack-plus-reactjs-and-django/

const path = require('path');
var BundleTracker = require('webpack-bundle-tracker');
const CleanWebpackPlugin = require('clean-webpack-plugin');


const assetPath = path.resolve(__dirname, 'assets/js');
const outputPath = path.resolve(__dirname, 'assets/webpack_bundles');


module.exports = {
    context: __dirname,

    entry: {
        // List of individual per-page JS files to be included
        gwas_upload: path.resolve(assetPath, 'gwas_upload.js')
    },
    plugins: [
        new CleanWebpackPlugin([outputPath], { watch: true }),
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
                exclude: /(node_modules|bower_components)/,
                use: { loader: 'babel-loader', options: { presets: ['@babel/preset-env'] } }
            }
        ]
    },
    output: {
        path: outputPath,
        filename: '[name]-[hash].js',
    },
};
