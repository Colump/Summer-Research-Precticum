<template>
    <el-row :gutter="20">
      <el-col :span="20">
        <div class="grid-content bg-purple">
          <el-menu :default-active="activeIndex" mode='horizontal' :collapse-transition.='false' class="el-menu-demo"  @select="handleSelect">
            <el-menu-item index="1" >111</el-menu-item>
            <el-menu-item index="2" >222</el-menu-item>
            <el-menu-item index="3" >222</el-menu-item>
            <el-menu-item index="4" >444</el-menu-item>
          </el-menu>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="grid-content bg-purple">
           <el-button circle @click="SignUp">
              <el-avatar> user </el-avatar>
           </el-button>
        </div>
      </el-col>
    </el-row>

    

</template>

<script>
export default {
    name:'MainNav',
    data() {
      return {
        activeIndex: '1',
        activeIndex2: '1'
      };
    },
    methods: {
      handleSelect(key, keyPath) {
        console.log(key, keyPath);
      },
      SignUp(){
        console.log("runing success")
      }
      
    }

}
</script>

<style spcope>
.el-button.is-circle {
    border-radius: 50%;
    padding: 4px;
}
</style>