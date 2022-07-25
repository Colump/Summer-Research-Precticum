<template>
  <div id="app">
    <!-- <MainNav></MainNav>
    <Header></Header> -->
    <!-- <StopsData></StopsData> -->
    <el-container>
      <el-aside width="250px">
        <div class="iconOfWeb">
          <img src="./assets/blueTheme_jt_journey_around_clock.png" width="50px" height="50px"/>
        </div>
        <div>
          <UserForms></UserForms>
          <ShowRouteButtom></ShowRouteButtom>
          <!-- <showMultpleRouteVue></showMultpleRouteVue> -->
        </div>
        
        <!-- <StopsData></StopsData> -->
        
      </el-aside>
      <el-container>
        <el-header>
          <MainNav></MainNav>
        </el-header>
        <el-main>
          <!-- <MyGoogleMap></MyGoogleMap> -->
          <!-- 在这里展示我们的四个页面 -->
          <router-view></router-view>
        </el-main>
        <el-footer>
        <p> Legal Stuff </p>
        <p> Privacy Policy </p>
        <p> Security </p>
       <!-- <p>Copyright @ 2022 Raduno Technologies</p>-->

          </el-footer>
      </el-container>
    </el-container>
   
  </div>
</template>

<script>
// import Header from './components/header'
// import Header from './components/header.vue'
import MainNav from './components/MainNav'
import AsideShowRoute from './components/AsideShowRoute'
import ShowRouteButtom from './components/ShowRouteButtom.vue'
import MyGoogleMap from './components/MyGoogleMap.vue'
// import showMultpleRoute from './components/showMultpleRoute.vue'

// 测试axios获取数据组件：test axios compoent
import StopsData from './components/StopsData.vue'
// 测试地址匹配框
import UserForms from './components/UserForms.vue'

export default {
  name: 'App',
  components: {
    MainNav,
    AsideShowRoute,
    ShowRouteButtom,
    MyGoogleMap,
    UserForms,
    StopsData,
    // showMultpleRouteVue
  },
  methods:{
    
  }

}
</script>

<style>
.el-header {
    /* background-color: #B3C0D1; */
    color: #333;
    text-align: center;
    line-height: 60px;
  }
   .el-footer{
 /* background-color: #B3C0D1; */
    line-height: 60px;
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: rgb(0, 140, 255);
    color: white;
    text-align: center;
    font-family: element-icons!important;
    display: flex;
    justify-content: space-between;
    line-height: 1px;
   }
  
  .el-aside {
    /* background-color: #D3DCE6; */
    color: #333;
    text-align: center;
    line-height: 200px;
    margin-left: 10px;
  }
  
  .el-main {
    /* background-color: #E9EEF3; */
    color: #333;
    text-align: center;
    line-height: 20px;
  }
  
  body > .el-container {
    margin-bottom: 40px;
  }
  
  .el-container:nth-child(5) .el-aside,
  .el-container:nth-child(6) .el-aside {
    line-height: 260px;
  }
  
  .el-container:nth-child(7) .el-aside {
    line-height: 320px;
  }
  
  element.style {
    width: 200px;
    padding-top: 50px;
  }
  .iconOfWeb{
    /* width: 100px; */
    margin-top: 10px;
    height: 80px;
    line-height: 100px;
    
  }
</style>
