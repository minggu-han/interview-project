<template>
  <div class="topbar">
    <strong>面试报告</strong>
    <button class="btn secondary" @click="$router.push('/admin')">返回后台</button>
  </div>
  <div class="container">
    <ReportView :report="report" :loadingText="loadingText" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import ReportView from '../components/ReportView.vue'

const route = useRoute()
const report = ref(null)
const loadingText = ref('加载中...')

onMounted(async () => {
  try {
    const { data } = await api.get(`/api/admin/interviews/${route.params.interviewId}/report`)
    report.value = data
  } catch (e) {
    loadingText.value = e.response?.data?.detail || '报告尚未生成（面试者可能还未完成答题）'
  }
})
</script>
