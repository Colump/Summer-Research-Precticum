<template>
  <div id="poster">
    <el-form :model="ruleForm" 
    :rules="rules"
    ref="ruleForm" 
    label-width="0px" 
    label-position="left"
    class="register-container">
        <h3 class="login_title">
            Register new account
            <el-button @click="toLogin()">LogIn</el-button>
        </h3>
        <el-form-item  prop="LoginName"  type="text">
            <el-input v-model="ruleForm.LoginName" placeholder="Account" prefix-icon="el-icon-user"></el-input>
        </el-form-item>
        <el-form-item  prop="name" type="text">
            <el-input v-model="ruleForm.name" placeholder="NickName" prefix-icon="el-icon-user"></el-input>
        </el-form-item>
        <el-form-item label="" prop="password">
            <el-input 
            type="password" 
            v-model="ruleForm.password" 
            autocomplete="off"
            placeholder="Password"
            prefix-icon="el-icon-lock"
            >
            </el-input>
        </el-form-item>
        <el-form-item  prop="checkPass">
            <el-input placeholder="Confirm Password" type="password" v-model="ruleForm.checkPass" autocomplete="off" prefix-icon="el-icon-lock"></el-input>
        </el-form-item>
        
        <el-form-item>
            <el-button type="primary" style="background:#505458 ;border:none" @click="submitForm(ruleForm)">Register</el-button>
            <el-button @click="resetForm('ruleForm')">reset</el-button>
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
          callback(new Error('enter you password place!'));
        } else {
          if (this.ruleForm.checkPass !== '') {
            this.$refs.ruleForm.validateField('checkPass');
          }
          callback();
        }
      };
      var validatePass2 = (rule, value, callback) => {
        if (value === '') {
          callback(new Error('enter you password again place!'));
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

        // 单独测试前端
        this.ruleForm = {};
                    this.$message({
                        message: `Registration is successful, the login page will be displayed three seconds later`,
                        type: 'success'
                    });
                    setTimeout(()=>{
                        this.$router.push({
                                    path:'/LogIn'
                                })
                        
                    },3000)
                    this.$bus.$emit('ToOtherPage',5)
        // 测试结束删掉


        // this.axios.post('后端路径',this.ruleForm).then(
        //     (resp) => {
        //         let data = resp.data
        //         if(data.success){
        //             this.ruleForm = {};
        //             this.$message({
        //                 message: `Registration is successful, the login page will be displayed three seconds later`,
        //                 type: 'success'
        //             });
        //             setTimeout(()=>{
        //                 this.$router.push({
        //                             path:'/LogIn'
        //                         })
        //                 this.$bus.$emit('ToOtherPage',1)
        //             },3000)
        //         }
        //     }
        // )

        
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