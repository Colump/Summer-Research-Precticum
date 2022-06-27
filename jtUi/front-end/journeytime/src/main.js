import Vue from 'vue';
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';
import App from './App.vue';
// import * as VueGoogleMaps from 'vue2-google-maps'
import * as VueGoogleMaps from 'vue2-google-maps'

Vue.use(ElementUI);


Vue.use(VueGoogleMaps, {
    load: {
        key: 'AIzaSyCHrX0Xl5WfOznFH1esYeEUEGFNr0VnL1w',
        libraries: 'places'
    }
})

Vue.config.productionTip = false

new Vue({
    render: h => h(App),
}).$mount('#app')