<template>
    <el-row :gutter="20">
      <el-col :span="20">
        <div class="grid-content bg-purple">
          <el-menu :default-active="activeIndex" mode='horizontal' :collapse-transition.='false' class="el-menu-demo"  @select="handleSelect">
            <el-menu-item index="1" >Map</el-menu-item>
            <el-menu-item index="2" >Register</el-menu-item>
            <el-menu-item index="3" >AboutUs</el-menu-item>
            <el-menu-item index="4" >API provide</el-menu-item>
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
        console.log(key);
        if(key==3){
            this.$router.push({
            name:'AboutUs',
          })
        }else if(key=='1'){
          this.$router.push({
            name:'MyMap',
          })
        }else if(key=='2'){
          this.$router.push({
            name:'Register',
          })
        }else if(key=='4'){
          this.$router.push({
            name:'MyAPI',
          })
        }else{
          this.$router.push({
            name:'MyMap',
          })
        }
      },
      SignUp(){
        console.log("runing success")
      },
      // ShowPage(){
      //   // console.log(this.$router)
      //   this.$router.push({
      //     name:'AboutUs',
      //   })
      // }
      
    }

}
</script>

<style spcope>
.el-button.is-circle {
    border-radius: 50%;
    padding: 4px;
}
</style>