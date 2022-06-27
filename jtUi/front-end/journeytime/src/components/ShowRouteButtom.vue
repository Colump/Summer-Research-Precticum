<template>
<div>
    <el-button @click="drawer = true" type="primary" style="margin-left: 16px;">
        Show roadmap
    </el-button>
    <el-drawer
      title="我是标题"
      :visible.sync="drawer"
      :with-header="false">
      <AsideShowRoute></AsideShowRoute>
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
      };
    }

}
</script>

<style>

</style>