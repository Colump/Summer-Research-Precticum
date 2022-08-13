<template>
  <div>This is our <a href="https://api.journeyti.me"> API page</a></div>
</template>

<script>
export default {
  Name:'MyAPI',
  mounted(){
    // If route choices happen to be displayed... hide them.
    this.$bus.$emit('UserFormShowRouteChoices', false)
  }
}
</script>

<style>

</style>