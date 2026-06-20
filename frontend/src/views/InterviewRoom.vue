<template>
  <div class="topbar">
    <strong>智能面试 · 答题</strong>
    <div>
      <span class="muted" style="margin-right:12px;">{{ username }}</span>
      <button class="btn secondary" @click="logout">退出</button>
    </div>
  </div>

  <div class="container" style="max-width: 820px;">
    <div v-if="status === 'loading'" class="card"><p class="muted">加载面试信息中...</p></div>

    <div v-else-if="status === 'notready'" class="card">
      <h2>题库准备中</h2>
      <p class="muted">AI 正在为你的岗位生成并质检面试题，请稍后刷新。</p>
      <button class="btn" style="margin-top:12px;" @click="reload">刷新</button>
    </div>

    <div v-else-if="status === 'finished'" class="card" style="text-align:center; padding:48px 24px;">
      <h2>面试完成 🎉</h2>
      <p class="muted" style="margin-top:8px;">你的答卷已成功提交，感谢参与本次面试。</p>
      <button class="btn secondary" style="margin-top:20px;" @click="logout">退出</button>
    </div>

    <template v-else>
      <div class="card">
        <h2>面试答题</h2>
        <p class="muted">共 {{ questions.length }} 道题，请在每题下方填写你的回答，全部完成后点击底部「提交」。</p>
      </div>

      <div class="card" v-for="(q, i) in questions" :key="q.id">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h3>第 {{ i + 1 }} 题</h3>
          <span class="tag" v-if="q.skill">{{ q.skill }}</span>
        </div>
        <p style="font-size:15px; line-height:1.6; margin:8px 0 12px;">{{ q.content }}</p>
        <textarea v-model="answers[q.id]" rows="5" placeholder="在此输入你的回答..."></textarea>
      </div>

      <div class="card" style="text-align:center;">
        <button class="btn green" :disabled="submitting" @click="submit">
          {{ submitting ? '提交中...' : '提交面试' }}
        </button>
        <p class="muted" style="margin-top:10px;">提交后将无法修改，请确认所有题目已作答。</p>
      </div>
    </template>
  </div>
</template>

<script setup>
// 面试者答题间：拉取题目 → 逐题作答 → 一次性提交 → 显示「面试完成」。
// 评分/报告由后端后台静默处理，面试者本人看不到报告。
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const username = localStorage.getItem('username')
// 页面状态机：loading(加载中) | notready(题库还在生成) | active(答题中) | finished(已提交)
const status = ref('loading')
const questions = ref([])
const answers = reactive({}) // 答案表：{ [question_id]: 文本 }
const submitting = ref(false)

// 拉取当前面试者的面试信息，并据 status/题目情况决定页面状态
async function reload() {
  status.value = 'loading'
  try {
    const { data } = await api.get('/api/interview/my')
    // 已提交或已出报告 → 直接显示完成页
    if (data.status === 'reported' || data.status === 'finished') {
      status.value = 'finished'
      return
    }
    // 题库尚未生成（后台 AI 还在出题/质检）→ 提示稍后刷新
    if (!data.questions || !data.questions.length) {
      status.value = 'notready'
      return
    }
    questions.value = data.questions
    data.questions.forEach((q) => { answers[q.id] = '' }) // 初始化每题答案为空
    status.value = 'active'
  } catch (e) {
    status.value = 'notready'
  }
}

// 提交全部答案：先做未答提醒与二次确认，再一次性 POST 给后端
async function submit() {
  const unanswered = questions.value.filter((q) => !(answers[q.id] || '').trim()).length
  let msg = '确认提交面试？提交后将无法修改。'
  if (unanswered > 0) msg = `还有 ${unanswered} 道题未作答，确认提交吗？提交后将无法修改。`
  if (!confirm(msg)) return

  submitting.value = true
  try {
    // 按题目顺序组装答案数组（即使某题为空也带上，便于后端逐题评分）
    const payload = {
      answers: questions.value.map((q) => ({ question_id: q.id, answer: answers[q.id] || '' })),
    }
    await api.post('/api/interview/submit', payload)
    status.value = 'finished' // 后端立即返回完成，评分在其后台异步进行
  } catch (e) {
    alert(e.response?.data?.detail || '提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

function logout() {
  localStorage.clear()
  router.push('/login')
}

onMounted(reload) // 进入页面即加载面试信息
</script>
