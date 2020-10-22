/* eslint-env node */

// TODO: Sort out process for deploying built assets
// Sample dev/prod core webpack config, based on:
//   https://webpack.js.org/guides/production/
//   https://owais.lone.pw/blog/webpack-plus-reactjs-and-django/

const path = require('path');
// const FriendlyErrorsWebpackPlugin = require('friendly-errors-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const VueLoaderPlugin = require('vue-loader/lib/plugin');
// const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

const assetPath = path.resolve(__dirname, 'assets/js');

module.exports = {
    context: __dirname,
    entry: {
        // List of individual per-page JS files to be included
        home_search: path.resolve(assetPath, 'pages/home_search.js'),
        profile: path.resolve(assetPath, 'pages/profile.js'),
        gwas_upload: path.resolve(assetPath, 'pages/gwas_upload.js'),
        gwas_summary: path.resolve(assetPath, 'pages/gwas_summary.js'),
        gwas_region: path.resolve(assetPath, 'pages/gwas_region.js'),
    },
    plugins: [
        // new FriendlyErrorsWebpackPlugin(),  // Disabled until compatible with webpack5
        new CleanWebpackPlugin(),
        new VueLoaderPlugin(),
        // new BundleAnalyzerPlugin(), // Uncomment when assessing bundle size
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
                    'style-loader',
                    'css-loader',
                ]
            }
        ]
    },
    optimization: {
        chunkIds: 'named',
        splitChunks: {
            cacheGroups: {
                vendor: {
                    test: /node_modules/,
                    chunks: 'initial',
                    name: 'vendor',
                    priority: 10,
                    enforce: true
                }
            }
        }
    },
    output: {
        path: path.resolve(__dirname, 'locuszoom_plotting_service/static/webpack_bundles'), // Should be in STATICFILES_DIRS,
        publicPath: '/static/', // Should match Django STATIC_URL
        filename: '[name].js', // In prod, Django will apply its own hashing to static asset filenames
        chunkFilename: '[id]-[chunkhash].js' // DO have Webpack hash chunk filename, see below
    },
    devServer: {
        writeToDisk: true, // Write files to disk in dev mode, so Django can serve the assets
    },
};
