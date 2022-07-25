<template>
  <div id="poster">
    <el-form :model="ruleForm" 
    :rules="rules"
    ref="ruleForm" 
    label-width="0px" 
    label-position="left"
    class="register-container">
        <h3 class="login_title">
            Register&nbsp;
            <el-button @click="toLogin()">Log In</el-button>
        </h3>
        <el-form-item  prop="LoginName"  type="text">
            <el-input v-model="ruleForm.LoginName" placeholder="Account" prefix-icon="el-icon-user" id="register-loginname"></el-input>
        </el-form-item>
        <el-form-item  prop="name" type="text">
            <el-input v-model="ruleForm.name" placeholder="Nickname" prefix-icon="el-icon-user" id="register-nickname"></el-input>
        </el-form-item>
        <el-form-item label="" prop="password">
            <el-input 
            type="password" 
            v-model="ruleForm.password" 
            autocomplete="off"
            placeholder="Password"
            prefix-icon="el-icon-lock"
            id="register-password">
            </el-input>
        </el-form-item>
        <el-form-item  prop="checkPass">
            <el-input placeholder="Confirm Password" type="password" v-model="ruleForm.checkPass" autocomplete="off" prefix-icon="el-icon-lock" id="register-confirm-password"></el-input>
        </el-form-item>
        
        <el-form-item>
            <el-button type="primary" style="background:#505458 ;border:none" @click="submitForm(ruleForm)" id="register-register">Register</el-button>
            <el-button @click="resetForm('ruleForm')" id="register-reset">Reset</el-button>
        </el-form-item>
    </el-form>
</div>
</template>

<script>
export default {
    name:'Register',
    data() {
      var validatePass = (rule, value, callback) => {
        if (value === '') {
          callback(new Error('Enter your password please!'));
        } else {
          if (this.ruleForm.checkPass !== '') {
            this.$refs.ruleForm.validateField('checkPass');
          }
          callback();
        }
      };
      var validatePass2 = (rule, value, callback) => {
        if (value === '') {
          callback(new Error('Enter your password again please!'));
        } else if (value !== this.ruleForm.password) {
          callback(new Error('The two passwords are inconsistent!'));
        } else {
          callback();
        }
      };
      return {
        ruleForm: {
          password: '',
          checkPass: '',
          name: '',
          LoginName:''
        },
        rules: {
          LoginName: [
            { required: true,message: "Please enter your account" ,trigger: 'blur' },
            { min: 4,max: 15 ,message:"4-15 long for you account" ,trigger: 'blur' }
          ],
          password: [
            { validator: validatePass, trigger: 'blur' }
          ],
          checkPass: [
            { validator: validatePass2, trigger: 'blur' }
          ],
        }
      };
    },
    methods: {
      submitForm(ruleForm) {
        var bcrypt = require('bcryptjs');    //引入bcryptjs库
        var salt = bcrypt.genSaltSync(10);    //定义密码加密的计算强度,默认10
        var hash = bcrypt.hashSync(ruleForm.password, salt);    //把自己的密码(this.registerForm.passWord)带进去,变量hash就是加密后的密码
        var hash2 = bcrypt.hashSync(ruleForm.checkPass, salt);
        this.ruleForm.password = hash;
        this.ruleForm.checkPass = hash2;
        // 单独测试前端
        // this.ruleForm = {};
        // console.log(this.ruleForm)
        // console.log(this.ruleForm.password === this.ruleForm.checkPass)
        // console.log(this.ruleForm.password.length)
        //             this.$message({
        //                 message: `Registration is successful, the login page will be displayed three seconds later`,
        //                 type: 'success'
        //             });
        //             setTimeout(()=>{
        //                 this.$router.push({
        //                             path:'/LogIn'
        //                         })
                        
        //             },3000)
        //             this.$bus.$emit('ToOtherPage',5)
        // 测试结束删掉

        var ruleFormToBackEnd={
          username:this.ruleForm.LoginName,
          password_hash:this.ruleForm.password
        }
        // console.log(ruleFormToBackEnd);
        this.axios.post('/api/register.do',ruleFormToBackEnd).then(
            (resp) => {
                let data = resp.data
                // console.log(data);
                if(data.success){
                    this.ruleForm = {};
                    this.$message({
                        message: `Registration is successful, the login page will be displayed three seconds later`,
                        type: 'success'
                    });
                    setTimeout(()=>{
                        this.$router.push({
                                    path:'/LogIn'
                                })
                        this.$bus.$emit('ToOtherPage',5)
                    },3000)
                }
            }
        )

        
      },
      resetForm(formName) {
        this.$refs[formName].resetFields();
        
      },
      toLogin(){
        this.$router.push({
                        path:'/LogIn'
                    })
        this.$bus.$emit('ToOtherPage',5)
      }
    }


}
</script>

<style scoped>
#poster{
    background-position: center;
    height: 100%;
    width: 100%; 
    background-size: cover; 
    position: fixed;
    margin:0px;
    padding:0px;
}

.register-container{
    border-radius: 15px;
    background-clip: padding-box;
    margin-top:50px;
    margin-left: 320px;
    width: 350px;
}
</style>