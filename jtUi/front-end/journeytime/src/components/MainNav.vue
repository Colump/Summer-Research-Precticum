<template>
    <el-row :gutter="20">
      <!-- 24 Columns in Element Grid system -->
      <el-col :span="20">
        <div class="grid-content bg-purple">
          <el-menu :default-active="activeIndex" mode='horizontal'
                  :collapse-transition.='false' class="el-menu-demo"
                  @select="handleSelect" text-color="#fff"
                  active-text-color="#fff" hover-text-color="#008CFF"
                  background-color="#008cff" hover-bg-color="#0707b3">
            <el-menu-item index="1" id="mainnav-map">Map</el-menu-item>
            <el-menu-item index="2" id="mainnav-register" >Register</el-menu-item>
            <el-menu-item index="5" id="mainnav-log-in">Log In</el-menu-item>
            <el-menu-item index="3" id="mainnav-about-us">About Us</el-menu-item>
            <el-menu-item index="4" id="mainnav-API">API</el-menu-item>
          </el-menu>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="grid-content bg-purple">
           <el-button circle @click="SignUp">
              <!-- <el-avatar v-bind:src="getAvatarUrl()" v-bind:alt="userName">{{userName}}</el-avatar>-->
              <el-avatar :src="getAvatarUrl.icon" v-bind:alt="userName">{{userName}}</el-avatar>
           </el-button>
        </div>
      </el-col>
    </el-row>
</template>

<script>
export default {
    name:'MainNav',
    // data function is called by Vue while creating a component instance and returns an object
    data() {
      return {
        activeIndex: '1',
        activeIndex2: '1',
        // How do we get the actual users username in here!?!?!?!?!
        userName:'user'
      };
    },
    computed: {
      getAvatarUrl () {
        return {
          // Hard coded for now - this is not good.
          icon: 'https://api.journeyti.me/get_profile_picture.do?username=' & this.userName
        }
      }
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
        if(key=='1'){
          this.$router.push({
            name:'MyMap',
          })
        }else if(key=='2'){
          this.$router.push({
            name:'Register',
          })
        }else if(key==3){
            this.$router.push({
            name:'AboutUs',
          })
        }
        else if(key=='4'){
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
        console.log("running success")
      }
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

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.el-button.is-circle {
    border-radius: 50%;
    padding: 4px;
}
.el-menu {
  font-family: element-icons !important;
}
</style>