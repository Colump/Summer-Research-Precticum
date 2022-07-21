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

// module.exports = {
//     // pabulicPath:process.env.NODE_ENV === 'production' ? '' : '',
//     devServer: {
//         host: '0.0.0.0',
//         port: '8080',
//         https:false,
//         open: true,
//         //以上的ip和端口是我们本机的;下面为需要跨域的
//         proxy: { //配置跨域
//             '/api': {
//                 target: 'https://api.journeyti.me',
//                 ws: true,
//                 changeOrigin: true, //允许跨域
//                 pathRewrite: {
//                     '^/api': '' //请求的时候使用这个api就可以
//                 }
//             }
//         }
//     }
// }