const webpack = require('webpack');

module.exports = {
  webpack: {
    configure: {
      resolve: {
        fallback: {
          "buffer": require.resolve("buffer/"),
          "timers": require.resolve("timers-browserify"),
          "stream": require.resolve("stream-browserify"),
          "util": require.resolve("util/"),
          "assert": require.resolve("assert/"),
          "crypto": require.resolve("crypto-browserify"),
          "fs": false,
          "path": require.resolve("path-browserify"),
          "os": require.resolve("os-browserify/browser"),
          "http": require.resolve("stream-http"),
          "https": require.resolve("https-browserify"),
          "url": require.resolve("url/"),
          "querystring": require.resolve("querystring-es3"),
          "zlib": require.resolve("browserify-zlib"),
        }
      },
      plugins: [
        new webpack.ProvidePlugin({
          Buffer: ['buffer', 'Buffer'],
          process: 'process/browser.js',
        }),
      ]
    }
  }
}; 