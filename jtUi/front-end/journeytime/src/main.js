import Vue from 'vue';
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';
import App from './App.vue';
// import * as VueGoogleMaps from 'vue2-google-maps'
import * as VueGoogleMaps from 'vue2-google-maps'
// import Router
import VueRouter from 'vue-router'
import myrouter from './router'

Vue.use(ElementUI);

// use router
Vue.use(VueRouter);
Vue.use(VueGoogleMaps, {
    load: {
        key: 'AIzaSyCHrX0Xl5WfOznFH1esYeEUEGFNr0VnL1w',
        libraries: 'places'
    }
})

Vue.config.productionTip = false

new Vue({
    render: h => h(App),
    // Registered routing:注册路由
    router: myrouter
}).$mount('#app')