const path = require("path");
const webpack = require("webpack");
const fs = require("fs");
const os = require("os");

module.exports = {
    entry: {
        pyright_worker: "./src/worker/pyright-worker.ts",
    },
    output: {
        path: path.resolve(__dirname, "dist"),
        filename: "[name].js",
        clean: true,
    },
    target: "webworker",
    resolve: {
        extensions: [".ts", ".tsx", ".js", ".json"],
        alias: {
            fs: require.resolve("@zenfs/core"),
            // Stub out Node-only Pyright deps that aren't needed in browser
            "@yarnpkg/fslib": path.resolve(__dirname, "src/worker/polyfills/yarnpkg-fslib-stub.js"),
            "@yarnpkg/libzip": path.resolve(__dirname, "src/worker/polyfills/yarnpkg-libzip-stub.js"),
            tmp: path.resolve(__dirname, "src/worker/polyfills/tmp-stub.js"),
        },
        fallback: {
            assert: require.resolve("assert"),
            crypto: require.resolve("crypto-browserify"),
            stream: require.resolve("stream-browserify"),
            url: require.resolve("url"),
            zlib: require.resolve("browserify-zlib"),
            vm: require.resolve("vm-browserify"),
            os: require.resolve("os-browserify/browser"),
            util: require.resolve("util/"),
            v8: false,
            readline: false,
            worker_threads: false,
            child_process: false,
            process: false,
            path: require.resolve("path-browserify"),
        },
    },
    plugins: [
        new webpack.ProvidePlugin({
            process: "process/browser",
            Buffer: ["buffer", "Buffer"],
        }),
        new webpack.DefinePlugin({
            __fs_constants: JSON.stringify(fs.constants),
            __os_constants: JSON.stringify(os.constants),
        }),
    ],
    module: {
        rules: [
            {
                test: /\.(ts|tsx)$/i,
                loader: "ts-loader",
                options: {
                    transpileOnly: true,
                    ignoreDiagnostics: [2307],
                },
            },
            {
                test: /\.(zip|egg)$/,
                use: ["arraybuffer-loader"],
            },
        ],
    },
    performance: {
        maxAssetSize: 10 * 1024 * 1024, // 10 MB (Pyright is large)
        maxEntrypointSize: 10 * 1024 * 1024,
    },
};
