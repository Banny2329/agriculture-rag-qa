<template>
  <div class="msg-row" :class="msg.role">
    <!-- 客服头像 -->
    <div v-if="msg.role === 'assistant'" class="avatar assistant">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3c1.6 0 2.9 1.3 2.9 2.9 0 .9-.4 1.7-1 2.3.6.3 1 1 1 1.7 0 .9-.5 1.6-1.2 2 .7.4 1.2 1.1 1.2 2 0 1.2-1 2.2-2.2 2.2h-1.4c-1.2 0-2.2-1-2.2-2.2V8.7C9.1 5.6 10.4 3 12 3z" />
        <path d="M9 19c-1.5.5-2.7 1.6-3.4 3M15 19c1.5.5 2.7 1.6 3.4 3" />
      </svg>
    </div>

    <div class="bubble" :class="msg.role">
      <template v-if="msg.loading">
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      </template>
      <template v-else>
        <div v-if="msg.role === 'user' && msg.files && msg.files.length" class="msg-files">
          <span class="msg-file" v-for="(f, i) in msg.files" :key="i">📎 {{ f }}</span>
        </div>
        <div class="bubble-text">{{ msg.content }}</div>
      </template>
    </div>

    <!-- 用户头像 -->
    <div v-if="msg.role === 'user'" class="avatar user">农</div>
  </div>
</template>

<script setup>
defineProps({
  msg: { type: Object, required: true },
})
</script>

<style scoped>
.msg-row {
  display: flex;
  gap: 10px;
  margin: 14px 0;
  align-items: flex-start;
}
.msg-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow);
}
.avatar.assistant {
  background: linear-gradient(135deg, var(--leaf), var(--leaf-dark));
  transform: rotate(-6deg);
}
.avatar.user {
  background: var(--sun);
  font-family: "Ma Shan Zheng", cursive;
  font-size: 18px;
  color: #7a5a12;
  transform: rotate(6deg);
}

.bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  line-height: 1.75;
  font-size: 15px;
  word-break: break-word;
  white-space: pre-wrap;
}
.bubble.assistant {
  background: var(--card);
  border: 2px solid var(--border);
  border-top-left-radius: 4px;
  box-shadow: var(--shadow);
}
.bubble.user {
  background: var(--leaf);
  color: #fff;
  border-top-right-radius: 4px;
  box-shadow: var(--shadow);
}

.bubble-text {
  text-align: left;
}

.msg-files {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
  margin-bottom: 6px;
}
.msg-file {
  display: inline-flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.22);
  border: 1.5px dashed rgba(255, 255, 255, 0.6);
  color: #fff;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 999px;
  max-width: 100%;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin: 0 2px;
  background: var(--leaf);
  border-radius: 50%;
  animation: bounce 1.2s infinite ease-in-out;
}
.dot:nth-child(2) { animation-delay: 0.15s; }
.dot:nth-child(3) { animation-delay: 0.3s; }

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
  40% { transform: translateY(-6px); opacity: 1; }
}
</style>
