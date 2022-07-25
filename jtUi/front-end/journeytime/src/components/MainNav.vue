<template>
    <el-row :gutter="20">
      <el-col :span="20">
        <div class="grid-content bg-purple">
          <el-menu :default-active="activeIndex" mode='horizontal' :collapse-transition.='false' class="el-menu-demo"  @select="handleSelect">
            <el-menu-item index="1" >Map</el-menu-item>
            <el-menu-item index="2" >Register</el-menu-item>
            <el-menu-item index="5" >Log In</el-menu-item>
            <el-menu-item index="3" >About Us</el-menu-item>
            <el-menu-item index="4" >API</el-menu-item>
          </el-menu>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="grid-content bg-purple">
           <el-button circle @click="SignUp">
              <el-avatar> {{userName}} </el-avatar>
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
        activeIndex2: '1',
        userName:'user'
      };
    },
    mounted(){
      this.$bus.$on('ToOtherPage',(data)=>{
        this.activeIndex=data+''
        // console.log(data)
      })
      this.$bus.$on('UserName',(data)=>{
        if(data==''){
          this.userName = 'user'
        }
        this.userName = data.substr(0, 4)
        // console.log(data)
      })
      
      
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
        }else if(key=='5'){
          this.$router.push({
            name:'LogIn',
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
      
    },
    watch:{
      activeIndex(){

        this.$bus.$on('ToOtherPage',(data)=>{
        this.activeIndex=data+''
        console.log(data)
      })
      }

    },

}
</script>

<style spcope>
.el-button.is-circle {
    border-radius: 50%;
    padding: 4px;
}
.el-menu {
  font-family: element-icons!important;
  background-color: rgb(0, 140, 255);

}
</style>