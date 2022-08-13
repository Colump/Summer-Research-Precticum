<template>
  <div>
      <el-button @click="drawer = true" type="primary" style="margin-left: 16px;">
          Show roadmap
      </el-button>
      <el-drawer
        title="我是标题"
        :visible.sync="drawer"
        :with-header="false">
        <AsideShowRoute :displayInfo = "displayInfo" :routeIndex="routeIndex"></AsideShowRoute>
      </el-drawer>

  </div>
</template>

<script>
import AsideShowRoute from './AsideShowRoute.vue';
export default {
    name:'ShowRouteButtom',
    components:{
        AsideShowRoute
    },
    data() {
      return {
        drawer: false,
        displayInfo:{

        },
        routeIndex:0
      };
    },
    created() {
      this.$bus.$on('stopBystopInfo',(data)=>{
        console.log("信息传递组件方法启动 ShowRouteButton.created() stopBystopInfo even detected on bus.")
        this.displayInfo = data
      })
      this.$bus.$on('GoogleMaps_IndexOfRouteToDisplay',(data)=>{
        console.log('ShowRouteButton.created() GoogleMaps_IndexOfRouteToDisplay detected on bus:', data)
        this.routeIndex = data
      })
    },
    watch:{
      routeIndex(){
        /* 22/08/13 TK; Replaced following - how did this ever work? */
        //this.$bus.$emit('Index', this.form.flag);
        console.log(
          'ShowRouteButton.routeIndex() Generating AsideShowRoute_IndexOfRouteToDisplay event on bus:',
          this.routeIndex)
        this.$bus.$emit('AsideShowRoute_IndexOfRouteToDisplay', this.routeIndex);
      }
    }

}
</script>

<style>
.el-button{
  font-family: element-icons;

}
</style>