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
        console.log("信息传递组件方法启动")
        this.displayInfo = data
      })

      this.$bus.$on('GetRouteIndex',(data)=>{
        this.routeIndex = data
      })
    },
    watch:{
      routeIndex(){
        this.$bus.$emit('Index',this.form.flag);
      }
    }

}
</script>

<style>
.el-button{
  font-family: element-icons;

}
</style>