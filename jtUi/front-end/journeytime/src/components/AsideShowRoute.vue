<template>
  <div class="block">
    <el-timeline style="height: 1000px; margin-top: 20px;">
      <el-timeline-item style="height: 50px" :hide-timestamp="true"
        v-for="(activity, index) in activities"
        :key="index"
        :icon="activity.icon"
        :type="activity.type"
        :color="activity.color"
        :size="activity.size"
        :timestamp="activity.timestamp">
        {{activity.content}}
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script>
export default {
    name:'AsideShowRoute',
    data() {
      return {
        activities: [{
          content: 'stop1',
          // timestamp: '2018-04-12 20:46',
          size: 'large',
          type: 'primary',
          icon: 'el-icon-more'
        }, {
          content: 'stop2',
          // timestamp: '2018-04-03 20:46',
          color: '#0bbd87'
        }, {
          content: 'stop3',
          // timestamp: '2018-04-03 20:46',
          size: 'large'
        }, {
          content: 'stop4',
          // timestamp: '2018-04-03 20:46'
        }]
      };
    },
    mounted(){
      this.$bus.$on('stopBystopInfo',(data)=>{
        this.activities = data
        console.log("stop by stop model ======")
        console.log(data)
      })
    }
}
    

</script>

<style>
.el-timeline-item__wrapper {
    position: relative;
    padding-left: 28px;
    top: -94px;
}
.el-timeline-item{
  font-family: element-icons;
}
</style>