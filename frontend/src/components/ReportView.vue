<template>
  <div v-if="!report" class="card"><p class="muted">{{ loadingText }}</p></div>
  <template v-else>
    <div class="card">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h2>面试评估报告</h2>
        <div style="text-align:right;">
          <div class="score-badge">{{ report.overall_score ?? '-' }}</div>
          <div class="muted">综合得分</div>
        </div>
      </div>
      <p style="margin-top:8px; line-height:1.7;">{{ report.summary }}</p>
    </div>

    <div class="card">
      <h3>🎯 录用建议</h3>
      <p style="line-height:1.7;">{{ report.recommendation }}</p>
    </div>

    <div class="row">
      <div class="card">
        <h3>✅ 优点</h3>
        <ul style="padding-left:18px; line-height:1.8;">
          <li v-for="(s, i) in report.strengths || []" :key="i">{{ s }}</li>
        </ul>
      </div>
      <div class="card">
        <h3>⚠️ 待改进</h3>
        <ul style="padding-left:18px; line-height:1.8;">
          <li v-for="(w, i) in report.weaknesses || []" :key="i">{{ w }}</li>
        </ul>
      </div>
    </div>

    <div class="card">
      <h3>📊 知识点掌握度</h3>
      <div v-for="(v, k) in report.skill_mastery || {}" :key="k" style="margin:10px 0;">
        <div style="display:flex; justify-content:space-between; font-size:14px;">
          <span>{{ k }}</span><span>{{ v }}</span>
        </div>
        <div style="background:#eef0f4; border-radius:6px; height:10px; margin-top:4px;">
          <div :style="{ width: v + '%', background: bar(v), height: '10px', borderRadius: '6px' }"></div>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>📝 各题详情</h3>
      <div v-for="(q, i) in report.per_question || []" :key="i"
           style="border:1px solid #eef0f4; border-radius:10px; padding:14px; margin-top:12px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px;">
          <div style="flex:1;">
            <span class="tag" v-if="q.skill">{{ q.skill }}</span>
            <p style="font-weight:600; margin-top:6px;">第 {{ i + 1 }} 题：{{ q.question }}</p>
          </div>
          <div style="text-align:center; white-space:nowrap;">
            <div style="font-size:20px; font-weight:700;" :style="{ color: bar(q.score) }">{{ q.score }}</div>
            <div class="muted" style="font-size:12px;">得分</div>
          </div>
        </div>
        <div style="margin-top:10px;">
          <div class="muted" style="font-size:13px; margin-bottom:4px;">面试者回答：</div>
          <div style="background:#f8fafc; border-radius:8px; padding:10px; font-size:14px; line-height:1.6; white-space:pre-wrap;">{{ q.answer || '（未作答）' }}</div>
        </div>
        <div v-if="q.comment" style="margin-top:10px;">
          <div class="muted" style="font-size:13px; margin-bottom:4px;">AI 简评：</div>
          <p style="font-size:14px; line-height:1.6;">{{ q.comment }}</p>
        </div>
      </div>
    </div>
  </template>
</template>

<script setup>
defineProps({
  report: { type: Object, default: null },
  loadingText: { type: String, default: '加载中...' },
})
function bar(v) {
  if (v >= 75) return '#16a34a'
  if (v >= 50) return '#f59e0b'
  return '#ef4444'
}
</script>
