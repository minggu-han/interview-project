<template>
  <div class="topbar">
    <strong>智能面试 · 管理后台</strong>
    <div>
      <span class="muted" style="margin-right:12px;">{{ username }}（管理员）</span>
      <button class="btn secondary" @click="logout">退出</button>
    </div>
  </div>

  <div class="container">
    <div class="card">
      <h2>添加面试者</h2>
      <form @submit.prevent @keydown.enter.prevent>
        <div class="row">
          <label>姓名 *<input v-model="form.name" required /></label>
          <label>面试岗位 *<input v-model="form.position" required placeholder="如：后端工程师" /></label>
        </div>
        <div class="row">
          <label>级别
            <select v-model="form.seniority">
              <option value="">不限</option>
              <option value="初级">初级</option>
              <option value="中级">中级</option>
              <option value="高级">高级</option>
            </select>
          </label>
          <label>邮箱<input v-model="form.email" placeholder="用于生成登录名（可选）" /></label>
          <label>电话<input v-model="form.phone" /></label>
        </div>
        <label>岗位所需技术</label>
        <div style="margin:-4px 0 12px;">
          <span v-for="(s, i) in form.skills" :key="i" class="tag">
            {{ s }} <a style="cursor:pointer;color:#ef4444;" @click="form.skills.splice(i,1)">×</a>
          </span>
          <button type="button" class="btn secondary" style="padding:4px 12px; font-size:13px;" @click="openSkillModal">
            + 添加技能
          </button>
        </div>
        <div class="row">
          <label>题目数量
            <input type="number" v-model.number="form.num_questions" min="1" max="20" />
          </label>
          <label>备注<input v-model="form.notes" /></label>
        </div>
        <button type="button" class="btn green" :disabled="creating" @click="createCandidate">{{ creating ? '创建中...' : '创建并生成账号' }}</button>
      </form>

      <div v-if="created" class="card" style="background:#f0fdf4; margin-top:20px;">
        <h3>✅ 账号已生成（请发送给面试者，密码仅显示一次）</h3>
        <p>姓名：<strong>{{ created.name }}</strong>　岗位：{{ created.position }}</p>
        <p>登录用户名：<strong style="color:#2563eb;">{{ created.login_username }}</strong></p>
        <p>登录密码：<strong style="color:#2563eb;">{{ created.login_password }}</strong></p>
        <p class="muted">题库正在后台由 AI 生成与质检，稍后可在列表中查看。</p>
        <button type="button" class="btn secondary" style="margin-top:10px;" @click="dismissCreated">我已记录，关闭</button>
      </div>
    </div>

    <div class="card">
      <h2>面试者列表</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>姓名</th><th>岗位</th><th>技术</th><th>级别</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="c in candidates" :key="c.id">
            <td>{{ c.id }}</td>
            <td>{{ c.name }}</td>
            <td>{{ c.position }}</td>
            <td><span v-for="s in c.skills" :key="s" class="tag">{{ s }}</span></td>
            <td>{{ c.seniority || '-' }}</td>
            <td>
              <button class="btn" @click="viewReport(c)">查看报告</button>
              <button class="btn secondary" @click="resetPw(c)">重置密码</button>
            </td>
          </tr>
          <tr v-if="!candidates.length"><td colspan="6" class="muted">暂无面试者</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- 添加技能弹框 -->
  <div v-if="showSkillModal" class="modal-mask" @click.self="closeSkillModal">
    <div class="modal-box">
      <h3>添加技能</h3>
      <input ref="skillInputEl" v-model="skillInput" placeholder="请输入一个技能，如：Python"
             @keydown.enter.prevent="confirmSkill" style="margin-top:12px;" />
      <div style="display:flex; gap:10px; justify-content:flex-end; margin-top:16px;">
        <button type="button" class="btn secondary" @click="closeSkillModal">取消</button>
        <button type="button" class="btn green" @click="confirmSkill">确定</button>
      </div>
    </div>
  </div>
</template>

<script setup>
// 管理后台：添加面试者（自动生成登录账号）、查看面试者列表、查看报告、重置密码。
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const username = localStorage.getItem('username')
// 添加面试者的表单。skills 为技能标签数组，num_questions 控制 AI 出题数量
const form = ref({ name: '', position: '', seniority: '', email: '', phone: '', skills: [], num_questions: 5, notes: '' })
const skillInput = ref('')
const creating = ref(false)
// 最近一次创建返回的账号密码。从 sessionStorage 恢复，避免跳转到报告页再返回后账号信息丢失
const created = ref(JSON.parse(sessionStorage.getItem('lastCreated') || 'null'))
const candidates = ref([])

// ——— 添加技能弹框 ———
const showSkillModal = ref(false)
const skillInputEl = ref(null)

async function openSkillModal() {
  skillInput.value = ''
  showSkillModal.value = true
  await nextTick()
  skillInputEl.value?.focus() // 弹框渲染后自动聚焦输入框
}
function closeSkillModal() {
  showSkillModal.value = false
}
function confirmSkill() {
  const v = skillInput.value.trim().replace(/[,，]/g, '') // 去掉中英文逗号，避免一次混入多个
  if (!v) { alert('请输入技能'); return }
  if (!form.value.skills.includes(v)) form.value.skills.push(v) // 去重后加入标签
  showSkillModal.value = false
}

// 创建面试者：后端会自动建账号、建面试，并在后台异步出题
async function createCandidate() {
  if (!form.value.name.trim() || !form.value.position.trim()) {
    alert('请填写姓名和面试岗位')
    return
  }
  const ok = confirm(
    `确认提交以下面试者信息？\n\n姓名：${form.value.name}\n岗位：${form.value.position}\n` +
    `技术：${form.value.skills.join('、') || '（未填）'}\n题目数量：${form.value.num_questions}`
  )
  if (!ok) return
  creating.value = true
  created.value = null
  try {
    const { data } = await api.post('/api/admin/candidates', form.value)
    // 返回的账号密码明文仅展示一次，持久化到 sessionStorage 以防误操作丢失
    created.value = data
    sessionStorage.setItem('lastCreated', JSON.stringify(data))
    // 重置表单并刷新列表
    form.value = { name: '', position: '', seniority: '', email: '', phone: '', skills: [], num_questions: 5, notes: '' }
    await loadCandidates()
  } catch (e) {
    alert(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

// 关闭账号展示卡片（确认已记录账号密码后）
function dismissCreated() {
  created.value = null
  sessionStorage.removeItem('lastCreated')
}

async function loadCandidates() {
  const { data } = await api.get('/api/admin/candidates')
  candidates.value = data
}

// 查看报告：先查该面试者最新一场面试拿到 interviewId，再跳到报告页
async function viewReport(c) {
  const { data } = await api.get(`/api/admin/candidates/${c.id}/interview`)
  router.push(`/admin/report/${data.id}`)
}

// 重置密码：后端生成新随机密码并返回明文
async function resetPw(c) {
  if (!confirm(`确定重置 ${c.name} 的密码？`)) return
  const { data } = await api.post(`/api/admin/candidates/${c.id}/reset-password`)
  alert(`新账号：${data.login_username} / ${data.login_password}`)
}

function logout() {
  localStorage.clear()
  sessionStorage.removeItem('lastCreated')
  router.push('/login')
}

onMounted(loadCandidates) // 进入后台即加载面试者列表
</script>
