<template>
  <div id="app-root">
    <el-container style="min-height: 100vh; background: #f5f7fa;">
      <el-aside width="200px" style="background: #1a1a2e; color: white;">
        <div class="sidebar-header">
          <h2 style="margin:0; font-size:18px;">📊 企微监控</h2>
        </div>
        <el-menu
          :default-active="route.path"
          router
          background-color="#1a1a2e"
          text-color="#ccc"
          active-text-color="#409eff"
        >
          <el-menu-item index="/">
            <el-icon><DataBoard /></el-icon>
            <span>总览看板</span>
          </el-menu-item>
          <el-menu-item index="/groups">
            <el-icon><ChatDotSquare /></el-icon>
            <span>群聊管理</span>
          </el-menu-item>
          <el-menu-item index="/operations">
            <el-icon><TrendCharts /></el-icon>
            <span>运营看板</span>
          </el-menu-item>
          <el-menu-item index="/group-manager">
            <el-icon><Edit /></el-icon>
            <span>群管理</span>
          </el-menu-item>
          <el-menu-item index="/daily-board">
            <el-icon><DataAnalysis /></el-icon>
            <span>当日看板</span>
          </el-menu-item>
          <el-menu-item index="/external-board">
            <el-icon><Link /></el-icon>
            <span>外部售后群</span>
          </el-menu-item>
          <el-menu-item index="/person-board">
            <el-icon><User /></el-icon>
            <span>人员看板</span>
          </el-menu-item>
          <el-menu-item index="/impact-board">
            <el-icon><WarningFilled /></el-icon>
            <span>影响业务群</span>
          </el-menu-item>
          <el-menu-item index="/ai-analyze">
            <el-icon><MagicStick /></el-icon>
            <span>AI群分析</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main>
        <router-view :key="route.path" />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<style>
body { margin: 0; font-family: -apple-system, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif; }
.sidebar-header { padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.el-menu { border-right: none !important; }
.el-main { padding: 20px; background: #f5f7fa; }
</style>
