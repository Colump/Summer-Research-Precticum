// 这个文件是我们注册路由器的地方，注册的路由器会传给vue对象
// This file is where we register the router, which is passed to the VUE object
import VueRouter from 'vue-router'



// 引入MyGoogleMap组件和AboutUs组件
// import MyGoogleMap and AboutUs component
import AboutUs from '../components/AboutUs'
import MyGoogleMap from '../components/MyGoogleMap'
import Register from '../components/Register'
import MyAPI from '../components/MyAPI'
// 创建一个路由器，其中要些很多的配置对象
// create a router
const myrouter = new VueRouter({
    routes: [{
            path: '/Map',
            name: 'MyMap',
            component: MyGoogleMap
        },
        {
            path: '/AboutUs',
            name: 'AboutUs',
            component: AboutUs
        },
        {
            path: '/Register',
            name: 'Register',
            component: Register
        },
        {
            path: '/MyAPI',
            name: 'MyAPI',
            component: MyAPI
        },
        {
            path: '',
            redirect: '/Map'
        }

    ]
})

export default myrouter