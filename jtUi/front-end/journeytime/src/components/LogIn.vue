<template>
  <div id="poster">
    <el-form class="login-container" lable-position="left" label-width="0px">
    <h3 class="login_title">
        Log In&nbsp;
        <el-button @click="toRegister">Register</el-button>
    </h3>
    <el-form-item >
        <el-input type="text" v-model="loginform.loginName" autocomplete="off" placeholder="Account" id="login-loginname"></el-input>
    </el-form-item>
    <el-form-item >
        <el-input type="password" v-model="loginform.password" autocomplete="off" placeholder="Password" id="login-password"></el-input>
    </el-form-item>
    <el-form-item style="width: 100%;">
        <el-button type="primary" style="width: 100%;background:#505458;border:none ;" @click="login()" id="login-login">Log In</el-button>
    </el-form-item>
    </el-form>
  </div>
</template>

<script>
export default {
  name:'LogIn',
  data() {
    return {
      loginform: {
        loginName: '',
        password: '',
      }
    }
  },
  mounted(){
    // If route choices happen to be displayed... hide them.
    this.$bus.$emit('UserFormShowRouteChoices', false)
  },
  methods: {
    login() {

      // 测试代码
      this.loginForm = {};
      this.$bus.$emit('ToOtherPage',1)
      this.$message({
          message: 'LogIn successful',
          type: 'success'
          });
                  this.$router.push({
                      path:'/Map'
                  })

                  // 传递用户名
                  this.$bus.$emit('UserName',this.loginform.loginName)



        // 测试结束就删掉


      // this.axios.post('后端路径',this.loginform).then(
      //     (resp) => {
      //         let data = resp.data
      //         if(data.success){
      //             this.loginForm = {};
      //             this.$message({
      //             message: '成功登录',
      //             type: 'success'
      //             });
      //             this.$router.push({
      //                 path:'/Map'
      //             })
      //             this.$bus.$emit('ToOtherPage',1)
      //         }
      //     }
      // )

    },
    toRegister(){
      this.$router.push({
          path:'/Register'
      })
      this.$bus.$emit('ToOtherPage',2)
    }
  }
}
</script>

<style>
#poster{
    /* background-position: center; */
    height: 100%;
    width: 100%;
    background-size: cover;
    position: fixed;
    font-family: element-icons;

}
body{
    margin:0px;
    padding:0px;
    font-family: element-icons;


}
.login-container{
    border-radius: 15px;
    background-clip: padding-box;
    margin-top:90px;
    margin-left: 320px;
    width: 350px;
    font-family: element-icons;

}

</style>