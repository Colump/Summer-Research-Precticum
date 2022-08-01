const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
    transpileDependencies: true,
    lintOnSave: false,

    devServer: {
        host: 'localhost',
        port: '8080',
        open: true,
        proxy: { //配置跨域
            '/api': {
                target: 'https://api.journeyti.me',
                ws: true,
                changeOrigin: true, //允许跨域
                pathRewrite: {
                    '^/api': '' //请求的时候使用这个api就可以
                }
            }
        }
    }
})