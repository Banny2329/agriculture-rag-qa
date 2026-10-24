<template>
  <div class="layout">
    <!-- 左侧历史会话栏 -->
    <aside class="sidebar">
      <div class="side-brand hand-font">农技问答</div>
      <button class="new-chat" @click="newConversation">
        <el-icon><Plus /></el-icon>&nbsp;创建新对话
      </button>
      <div class="side-section">最近</div>
      <div class="side-list">
        <div
          v-for="c in conversations"
          :key="c.id"
          class="side-item"
          :class="{ active: c.id === activeId }"
          @click="switchConversation(c.id)"
        >
          <span class="side-dot" :class="{ on: c.id === activeId }"></span>
          <span class="side-name">{{ c.title }}</span>
        </div>
      </div>

      <!-- 底部用户区 -->
      <div class="side-user-area">
        <el-dropdown trigger="click" @command="onUserCommand" placement="top-start">
          <div class="user-chip" title="切换用户 / 新建用户">
            <span class="user-avatar" :style="{ background: currentUser?.color || '#b8c4b8' }">{{ currentUser?.emoji || '👤' }}</span>
            <span class="user-info">
              <span class="user-name">{{ currentUser?.name || '未登录' }}</span>
              <span class="user-role">{{ currentUser?.role || '请登录账号' }}</span>
            </span>
            <el-icon class="user-arrow"><ArrowUp /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="u in users"
                :key="u.id"
                :command="u"
              >
                <span class="dd-avatar" :style="{ background: u.color }">{{ u.emoji }}</span>
                <span class="dd-name">{{ u.name }}</span>
                <span class="dd-role">{{ u.role }}</span>
              </el-dropdown-item>
              <el-dropdown-item divided command="__new_user__">
                <el-icon class="dd-new-icon"><Plus /></el-icon>
                <span class="dd-new">新建用户</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </aside>

    <!-- 新建用户弹窗 -->
    <el-dialog v-model="userDialogVisible" title="新建用户" width="360px" align-center>
      <div class="new-user-form">
        <div class="nu-row">
          <label>头像</label>
          <div class="emoji-picker">
            <button
              v-for="e in EMOJIS"
              :key="e"
              type="button"
              class="emoji-opt"
              :class="{ on: newUserEmoji === e }"
              @click="newUserEmoji = e"
            >{{ e }}</button>
          </div>
        </div>
        <div class="nu-row">
          <label>用户名</label>
          <el-input v-model="newUserName" placeholder="请输入用户名" maxlength="12" clearable />
        </div>
        <div class="nu-row">
          <label>密码</label>
          <el-input v-model="newUserPassword" type="password" show-password placeholder="请设置密码（至少 4 位）" maxlength="20" />
        </div>
        <div class="nu-row">
          <label>确认密码</label>
          <el-input v-model="newUserConfirm" type="password" show-password placeholder="请再次输入密码" maxlength="20" @keyup.enter="addUser" />
        </div>
      </div>
      <template #footer>
        <el-button round @click="userDialogVisible = false">取消</el-button>
        <el-button type="success" round @click="addUser">创建</el-button>
      </template>
    </el-dialog>

    <!-- 登录确认弹窗 -->
    <el-dialog v-model="loginDialogVisible" title="请登录账号" width="360px" align-center>
      <div class="new-user-form">
        <!-- 带头像的账号选择器：点击展开下拉，选择要登录的账号 -->
        <div class="login-user-pick" @click="loginPickOpen = !loginPickOpen">
          <span class="dd-avatar" :style="{ background: loginUser.color }">{{ loginUser.emoji }}</span>
          <span class="dd-name">{{ loginUser.name }}</span>
          <span class="dd-role">{{ loginUser.role }}</span>
          <span class="login-pick-arrow">{{ loginPickOpen ? '▲' : '▼' }}</span>
        </div>
        <div v-if="loginPickOpen" class="login-user-list">
          <div
            v-for="u in users"
            :key="u.id"
            class="login-user-item"
            :class="{ active: u.id === loginUser.id }"
            @click="pickLoginUser(u)"
          >
            <span class="dd-avatar" :style="{ background: u.color }">{{ u.emoji }}</span>
            <span class="dd-name">{{ u.name }}</span>
            <span class="dd-role">{{ u.role }}</span>
          </div>
        </div>
        <div class="nu-row">
          <label>密码</label>
          <el-input v-model="loginPassword" type="password" show-password placeholder="请输入密码" maxlength="20" @keyup.enter="doLogin" />
        </div>
        <div class="nu-tip">默认密码：123456</div>
      </div>
      <template #footer>
        <el-button round @click="loginDialogVisible = false">取消</el-button>
        <el-button type="success" round @click="doLogin">登录</el-button>
      </template>
    </el-dialog>

    <!-- 用户详情弹窗 -->
    <el-dialog v-model="profileDialogVisible" title="用户信息" width="360px" align-center>
      <div class="profile-body">
        <div class="profile-avatar" :style="{ background: profileUser.color }">{{ profileUser.emoji }}</div>
        <div class="profile-name">{{ profileUser.name }}</div>
        <div class="profile-role">{{ profileUser.role }}</div>
        <el-tag v-if="currentUser && profileUser.id === currentUser.id" type="success" effect="light" round>当前登录</el-tag>
      </div>
      <div class="profile-actions">
        <el-button
          type="success"
          round
          :disabled="!currentUser || profileUser.id !== currentUser.id"
          @click="logoutUser"
        >退出该用户</el-button>
        <el-button
          type="danger"
          round
          :disabled="!currentUser || profileUser.id !== currentUser.id"
          @click="openDeleteConfirm"
        >注销该用户</el-button>
      </div>
      <div v-if="!currentUser || profileUser.id !== currentUser.id" class="profile-tip">
        需先登录该账户后方可注销
        <span class="profile-login-link" @click="loginFromProfile">登录该账户</span>
      </div>
    </el-dialog>

    <!-- 注销确认弹窗 -->
    <el-dialog v-model="confirmDeleteDialogVisible" title="确认注销" width="340px" align-center>
      <p class="confirm-del-text">
        是否确认注销账户「{{ confirmDeleteUser.name }}」？<br />
        该账号及全部会话记录将永久删除。
      </p>
      <template #footer>
        <el-button round @click="confirmDeleteDialogVisible = false">否</el-button>
        <el-button type="danger" round @click="doDeleteUser">是</el-button>
      </template>
    </el-dialog>

    <!-- 右侧聊天区 -->
    <div class="page">
      <!-- 顶部 -->
      <header class="header">
        <div class="header-left">
          <div class="logo hand-font">农</div>
          <div>
            <h1 class="title hand-font">农技问答小助手</h1>
          </div>
        </div>
        <div class="header-right">
          <el-tag :type="kbReady ? 'success' : 'warning'" effect="light" round size="large">
            {{ kbReady ? `知识库已就绪（${kbChunks} 个片段）` : '知识库未建档' }}
          </el-tag>
          <el-button v-if="!kbReady" type="primary" plain round @click="onIngest">
            扫描建档
          </el-button>
        </div>
      </header>

      <!-- 主体 -->
      <main class="main" ref="mainRef">
        <div v-if="!messages.length" class="welcome">
          <h2 class="hand-font">你好呀，我是你的农技小助手</h2>
          <p>可以问我作物种植、病虫害防治、施肥用药、田间管理等问题。</p>
          <div class="quick">
            <button v-for="q in quickQuestions" :key="q" class="quick-chip" @click="send(q)">
              {{ q }}
            </button>
          </div>
        </div>

        <div v-else class="chat-list">
          <MessageBubble v-for="(m, i) in messages" :key="i" :msg="m" />
        </div>
      </main>

      <!-- 上传文件卡片 -->
      <div v-if="uploadItems.length" class="upload-list">
        <div v-for="(item, i) in uploadItems" :key="i" class="upload-card" :class="item.status">
          <span class="file-icon">PDF</span>
          <div class="file-info">
            <div class="file-name">{{ item.name }}</div>
            <div class="file-meta">{{ item.size }} · {{ statusText(item) }}</div>
          </div>
          <span v-if="item.status === 'uploading'" class="status-spinner"></span>
          <span v-else class="status-mark" :class="item.status">{{ item.status === 'done' ? '✓' : '✕' }}</span>
          <button class="remove-file" title="删除该文件" @click="removeUpload(i)">
            <el-icon><Close /></el-icon>
          </button>
        </div>
      </div>

      <!-- 输入区 -->
      <footer class="footer">
        <div class="input-bar">
          <el-upload
            :show-file-list="false"
            :auto-upload="false"
            accept=".pdf"
            multiple
            :on-change="onFilesChange"
          >
            <el-button class="upload-btn" round>
              <el-icon><Upload /></el-icon>&nbsp;上传PDF
            </el-button>
          </el-upload>
          <el-input
            v-model="input"
            class="chat-input"
            placeholder="输入你的问题，例如：玉米叶子上出现黄斑怎么办？"
            :disabled="sending"
            @keyup.enter="send()"
          />
          <el-button type="success" round size="large" :loading="sending" @click="send()">
            发送
          </el-button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Close, Plus, ArrowUp } from '@element-plus/icons-vue'
import MessageBubble from './components/MessageBubble.vue'
import { chat, kbStatus, kbIngest, uploadPdfs } from './api'

/* ---------- 用户 ---------- */
// 初始种子用户：所有用户均为普通用户，均可登录/退出/注销
const USERS_STORAGE_KEY = 'agri_rag_users'
const PRESET_USERS = [
  { id: 'u_banny', name: 'Banny', role: '普通用户', emoji: '🧑‍🌾', color: '#3f7d3a', password: '123456' },
  { id: 'u_mandy', name: 'Mandy', role: '普通用户', emoji: '👩‍🌾', color: '#4a7ba6', password: '123456' },
]

function saveUsers(list) {
  try {
    localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(list))
  } catch (e) {
    /* ignore */
  }
}

// 读取用户列表；首次访问播种 Banny / Mandy，并兼容迁移旧的独立自定义用户数据
function seedUsers() {
  try {
    const saved = localStorage.getItem(USERS_STORAGE_KEY)
    if (saved) {
      const list = JSON.parse(saved)
      if (Array.isArray(list) && list.length) return list
    }
  } catch (e) {
    /* ignore */
  }
  let custom = []
  try {
    custom = JSON.parse(localStorage.getItem('agri_rag_custom_users') || '[]')
  } catch (e) {
    /* ignore */
  }
  const list = [...PRESET_USERS, ...custom]
  saveUsers(list)
  return list
}
const EMOJIS = ['👩‍🌾', '🧑‍🌾', '👨‍🌾', '🧑‍🔬', '👩‍💻', '🧑‍💻', '🐔', '🐂', '🐏', '🍅', '🌽', '🍚']
const USER_COLORS = ['#5da44e', '#3f7d3a', '#8a5a35', '#c77b3f', '#4a7ba6', '#9b59b6']

const users = ref([]) // 预设 + 自定义
const currentUser = ref(PRESET_USERS[0]) // 模板会同步访问，需避免为 null
const STORAGE_CURRENT_USER = 'agri_rag_current_user'
const STORAGE_KEY_PREFIX = 'agri_rag_conversations_'
const STORAGE_ACTIVE_PREFIX = 'agri_rag_active_'
const convKey = () => STORAGE_KEY_PREFIX + (currentUser.value?.id ?? 'u_banny')
const activeKey = () => STORAGE_ACTIVE_PREFIX + (currentUser.value?.id ?? 'u_banny')

/* ---------- 多会话状态 ---------- */
const conversations = ref([]) // [{ id, title, messages, files, createdAt, updatedAt }]
const activeId = ref('')
const current = ref(null) // 指向 conversations 中当前会话对象
const messages = computed(() => current.value?.messages || [])

function persist() {
  try {
    localStorage.setItem(convKey(), JSON.stringify(conversations.value))
  } catch (e) {
    /* 存储不可用时忽略 */
  }
}
watch(conversations, persist, { deep: true })

function persistActive() {
  try {
    localStorage.setItem(activeKey(), activeId.value)
  } catch (e) {
    /* ignore */
  }
}

/* 新建用户弹窗状态 */
const userDialogVisible = ref(false)
const newUserName = ref('')
const newUserEmoji = ref(EMOJIS[0])
const newUserPassword = ref('')
const newUserConfirm = ref('')

/* 登录确认弹窗状态 */
const loginDialogVisible = ref(false)
const loginUser = ref(PRESET_USERS[0])
const loginName = ref('')
const loginPickOpen = ref(false)
const loginPassword = ref('')

/* 用户详情弹窗状态 */
const profileDialogVisible = ref(false)
const profileUser = ref(PRESET_USERS[0])

/* 注销确认弹窗状态 */
const confirmDeleteDialogVisible = ref(false)
const confirmDeleteUser = ref(PRESET_USERS[0])

function refreshUsers() {
  users.value = seedUsers()
}

function onUserCommand(cmd) {
  if (cmd === '__new_user__') {
    newUserName.value = ''
    newUserEmoji.value = EMOJIS[0]
    newUserPassword.value = ''
    newUserConfirm.value = ''
    userDialogVisible.value = true
    return
  }
  // 点击用户项：打开该用户的详情页
  profileUser.value = cmd
  profileDialogVisible.value = true
}

function pickLoginUser(u) {
  loginUser.value = u
  loginName.value = u.name
  loginPassword.value = ''
  loginPickOpen.value = false
}

function loginFromProfile() {
  const u = profileUser.value
  if (currentUser.value && u.id === currentUser.value.id) {
    ElMessage.info('当前已是该用户')
    profileDialogVisible.value = false
    return
  }
  loginUser.value = u
  loginName.value = u.name
  loginPickOpen.value = false
  loginPassword.value = ''
  loginDialogVisible.value = true
}

function logoutUser() {
  const u = profileUser.value
  if (u.id !== currentUser.value?.id) {
    ElMessage.warning('当前未登录该用户')
    return
  }
  // 先保存当前用户会话，再退出登录
  persist()
  persistActive()
  currentUser.value = null
  try {
    localStorage.removeItem(STORAGE_CURRENT_USER)
  } catch (e) {
    /* ignore */
  }
  profileDialogVisible.value = false
  ElMessage.success(`已退出用户「${u.name}」`)
  // 退出后弹出登录弹窗，要求输入密码
  loginUser.value = u
  loginName.value = u.name
  loginPickOpen.value = false
  loginPassword.value = ''
  loginDialogVisible.value = true
}

function openDeleteConfirm() {
  const u = profileUser.value
  if (u.id !== currentUser.value?.id) {
    ElMessage.warning('请先登录该账户后再注销')
    return
  }
  confirmDeleteUser.value = u
  confirmDeleteDialogVisible.value = true
}

function doDeleteUser() {
  const u = confirmDeleteUser.value
  const id = u.id
  const name = u.name
  users.value = users.value.filter((x) => x.id !== id)
  saveUsers(users.value)
  // 清理该用户的会话数据
  try {
    localStorage.removeItem(STORAGE_KEY_PREFIX + id)
    localStorage.removeItem(STORAGE_ACTIVE_PREFIX + id)
  } catch (e) {
    /* ignore */
  }
  confirmDeleteDialogVisible.value = false
  profileDialogVisible.value = false
  // 注销的是当前登录用户：退出登录并弹出登录弹窗
  if (currentUser.value?.id === id) {
    currentUser.value = null
    try {
      localStorage.removeItem(STORAGE_CURRENT_USER)
    } catch (e) {
      /* ignore */
    }
    conversations.value = []
    activeId.value = ''
    current.value = null
    if (users.value.length) {
      loginUser.value = users.value[0]
      loginName.value = users.value[0].name
      loginPickOpen.value = false
      loginPassword.value = ''
      loginDialogVisible.value = true
      ElMessage.success(`已注销账户「${name}」`)
    } else {
      ElMessage.warning(`已注销账户「${name}」，当前无可用账户，请新建用户`)
    }
    return
  }
  ElMessage.success(`已注销账户「${name}」`)
}

function openLogin() {
  loginName.value = currentUser.value?.name || ''
  loginPassword.value = ''
  loginDialogVisible.value = true
}

function doLogin() {
  const name = loginName.value.trim()
  const pwd = loginPassword.value
  if (!name || !pwd) {
    ElMessage.warning('请选择账号并输入密码')
    return
  }
  const target = users.value.find((u) => u.name === name)
  if (!target || target.password !== pwd) {
    ElMessage.error('用户名或密码错误')
    return
  }
  loginDialogVisible.value = false
  loginPassword.value = ''
  loginPickOpen.value = false
  profileDialogVisible.value = false
  if (currentUser.value && target.id === currentUser.value.id) {
    ElMessage.info('当前已是该用户')
    return
  }
  switchUser(target)
}

function addUser() {
  const name = newUserName.value.trim()
  const pwd = newUserPassword.value
  if (!name) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (users.value.some((u) => u.name === name)) {
    ElMessage.warning('该用户名已存在')
    return
  }
  if (!pwd || pwd.length < 4) {
    ElMessage.warning('密码至少 4 位')
    return
  }
  if (pwd !== newUserConfirm.value) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  const user = {
    id: 'u_custom_' + Date.now(),
    name,
    role: '普通用户',
    emoji: newUserEmoji.value,
    color: USER_COLORS[users.value.length % USER_COLORS.length],
    password: pwd,
  }
  users.value.push(user)
  saveUsers(users.value)
  userDialogVisible.value = false
  ElMessage.success(`已创建用户「${name}」`)
  // 创建成功视为已通过密码验证，直接登录
  switchUser(user)
}

function initUser() {
  refreshUsers()
  if (!users.value.length) {
    currentUser.value = null
    return
  }
  let u = users.value[0]
  try {
    const saved = localStorage.getItem(STORAGE_CURRENT_USER)
    u = users.value.find((x) => x.id === saved) || u
  } catch (e) {
    /* ignore */
  }
  currentUser.value = u
}

function switchUser(user) {
  if (currentUser.value && user.id === currentUser.value.id) return
  if (currentUser.value) persist()
  if (currentUser.value) persistActive()
  currentUser.value = user
  try {
    localStorage.setItem(STORAGE_CURRENT_USER, user.id)
  } catch (e) {
    /* ignore */
  }
  loadPersisted()
}

function activate(c) {
  activeId.value = c.id
  current.value = c
  uploadItems.value = []
  recentUploads.value = c.files || []
  c.files = recentUploads.value
  persistActive()
  scrollBottom()
}

function newConversation() {
  const c = {
    id: 'c' + Date.now(),
    title: '新对话',
    messages: [],
    files: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
  conversations.value.push(c)
  activate(c)
}

function switchConversation(id) {
  const c = conversations.value.find((x) => x.id === id)
  if (c && c.id !== activeId.value) activate(c)
}

function loadPersisted() {
  let raw = null
  try {
    raw = localStorage.getItem(convKey())
    // 首次升级：把旧版全局会话迁移到默认用户名下，避免历史数据丢失
    if (!raw && currentUser.value) {
      const legacy = localStorage.getItem('agri_rag_conversations_v1')
      if (legacy) {
        localStorage.setItem(convKey(), legacy)
        localStorage.setItem(activeKey(), localStorage.getItem('agri_rag_active_conversation') || '')
        raw = legacy
      }
    }
  } catch (e) {
    /* ignore */
  }
  try {
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length) {
        // 只保留结构合法的会话
        conversations.value = parsed
          .filter((c) => c && Array.isArray(c.messages))
          .map((c) => ({ ...c, files: Array.isArray(c.files) ? c.files : [] }))
      }
    }
  } catch (e) {
    /* 损坏数据直接忽略 */
  }
  if (conversations.value.length) {
    const saved = localStorage.getItem(activeKey())
    const target =
      conversations.value.find((c) => c.id === saved) ||
      conversations.value[conversations.value.length - 1]
    activeId.value = target.id
    current.value = target
    recentUploads.value = target.files || []
    target.files = recentUploads.value
  } else {
    newConversation()
  }
}

/* ---------- 聊天 ---------- */
const input = ref('')
const sending = ref(false)
const kbReady = ref(false)
const kbChunks = ref(0)
const mainRef = ref(null)
const uploadItems = ref([])
const recentUploads = ref([])

const quickQuestions = [
  '小麦赤霉病怎么防治？',
  '玉米苗期叶片发黄是什么原因？',
  '水稻什么时候施穗肥最合适？',
]

function fmtSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function statusText(item) {
  if (item.status === 'uploading') return '处理中…'
  if (item.status === 'done') return `已入库${item.chunks ? ` ${item.chunks} 片段` : ''}`
  return '上传失败'
}

function scrollBottom() {
  nextTick(() => {
    if (mainRef.value) mainRef.value.scrollTop = mainRef.value.scrollHeight
  })
}

function pushMsg(msg) {
  messages.value.push(msg)
  scrollBottom()
}

async function send(text) {
  const q = (text ?? input.value).trim()
  if (!q || sending.value) return
  if (!currentUser.value) {
    ElMessage.warning('请先登录账号')
    return
  }
  input.value = ''
  const files = [...recentUploads.value]
  pushMsg({ role: 'user', content: q, files })
  // 首个问题作为会话标题
  if (!current.value.title || current.value.title === '新对话') {
    current.value.title = q.replace(/\s+/g, '').slice(0, 18) || '新对话'
  }
  const idx = messages.value.length
  pushMsg({ role: 'assistant', content: '', loading: true })
  sending.value = true
  try {
    const { data } = await chat(q, files)
    messages.value[idx] = {
      role: 'assistant',
      content: data.answer,
      sources: data.sources || [],
    }
    // 文件已随消息成功发送，清空输入区卡片
    uploadItems.value = []
    recentUploads.value = []
    current.value.files = recentUploads.value
  } catch (err) {
    const detail = err.response?.data?.detail || err.message
    messages.value[idx] = {
      role: 'assistant',
      content: `抱歉，我暂时无法回答：${detail}`,
      sources: [],
    }
  } finally {
    sending.value = false
    scrollBottom()
  }
}

async function refreshStatus() {
  try {
    const { data } = await kbStatus()
    kbReady.value = data.chunks > 0
    kbChunks.value = data.chunks
  } catch (e) {
    /* 后端未启动时忽略 */
  }
}

async function onIngest() {
  try {
    const { data } = await kbIngest()
    ElMessage.success(`建档完成：${data.ingested_files} 份文档，${data.chunks} 个片段`)
    refreshStatus()
  } catch (err) {
    ElMessage.error(`建档失败：${err.response?.data?.detail || err.message}`)
  }
}

async function onFilesChange(file, files) {
  if (!files.length) return
  const rawFiles = files.map((f) => f.raw).filter(Boolean)
  if (!rawFiles.length) return
  ElMessage.closeAll()
  const before = kbChunks.value
  uploadItems.value = rawFiles.map((f) => ({
    name: f.name,
    size: fmtSize(f.size),
    status: 'uploading',
    chunks: 0,
  }))
  try {
    const { data } = await uploadPdfs(rawFiles)
    const chunks = data.chunks || 0
    uploadItems.value.forEach((it, i) => {
      it.status = 'done'
      if (rawFiles.length === 1) it.chunks = chunks
    })
    recentUploads.value = rawFiles.map((f) => f.name)
    current.value.files = recentUploads.value
    ElMessage.success(
      `上传成功：${(data.uploaded || []).join('、')}，新增 ${chunks} 个片段` +
        (data.skipped?.length ? `；跳过：${data.skipped.join('；')}` : '')
    )
    refreshStatus()
  } catch (err) {
    const detail = err.response?.data?.detail
    const msg =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => (typeof d === 'object' ? d.msg || JSON.stringify(d) : d)).join('；')
          : detail
            ? JSON.stringify(detail)
            : err.message || '未知错误'
    // 代理/网络层中断：请求可能仍被后端完整处理，刷新知识库确认真实结果
    if (!err.response && kbChunks.value > 0) {
      ElMessage.warning('连接中断，正在确认文件是否已建档…')
      await refreshStatus()
      if (kbChunks.value > before) {
        uploadItems.value.forEach((it) => { it.status = 'done' })
        recentUploads.value = rawFiles.map((f) => f.name)
        current.value.files = recentUploads.value
        ElMessage.success(`文件已成功建档（新增 ${kbChunks.value - before} 个片段）`)
      } else {
        uploadItems.value.forEach((it) => { it.status = 'failed' })
        ElMessage.error(`上传失败：${msg || '连接中断，请重试'}`)
      }
    } else {
      uploadItems.value.forEach((it) => { it.status = 'failed' })
      ElMessage.error(`上传失败：${msg}`)
    }
  }
}

function removeUpload(i) {
  const name = uploadItems.value[i]?.name
  if (!name) return
  uploadItems.value.splice(i, 1)
  recentUploads.value = recentUploads.value.filter((n) => n !== name)
  current.value.files = recentUploads.value
}

onMounted(() => {
  initUser()
  loadPersisted()
  refreshStatus()
})
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 左侧会话栏 */
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--bg);
  border-right: 2.5px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 16px 12px;
  overflow-y: auto;
}
.side-brand {
  font-size: 20px;
  color: var(--leaf-dark);
  padding: 0 6px 14px;
}
.new-chat {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  border: 2px dashed var(--leaf);
  background: var(--leaf-light);
  color: var(--leaf-dark);
  border-radius: 12px;
  padding: 9px 12px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.new-chat:hover {
  background: var(--leaf);
  color: #fff;
}
.side-section {
  font-size: 12px;
  color: var(--ink-light);
  padding: 14px 6px 6px;
}
.side-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.side-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  color: var(--ink);
  transition: background 0.2s;
}
.side-item:hover {
  background: var(--leaf-light);
}
.side-item.active {
  background: var(--card);
  font-weight: bold;
  box-shadow: var(--shadow);
}
.side-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--border);
  flex-shrink: 0;
}
.side-dot.on {
  background: var(--leaf);
}
.side-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 右侧聊天区 */
.page {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  max-width: 900px;
  margin: 0 auto;
  padding: 0 18px;
}

/* 顶部 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 0 10px;
  gap: 12px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.logo {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--leaf), var(--leaf-dark));
  color: #fff;
  font-size: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow);
  transform: rotate(-8deg);
}
.title {
  margin: 0;
  font-size: 26px;
  color: var(--leaf-dark);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 用户切换 */
.side-user-area {
  margin-top: auto;
  padding-top: 14px;
  border-top: 2.5px solid var(--border);
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--card);
  border: 2.5px solid var(--border);
  border-radius: 14px;
  padding: 8px 10px;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: border-color 0.2s;
}
.user-chip:hover {
  border-color: var(--leaf);
}
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #fff;
  flex-shrink: 0;
}
.user-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.user-name {
  font-size: 14px;
  font-weight: bold;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-role {
  font-size: 11px;
  color: var(--ink-light);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-arrow {
  color: var(--ink-light);
  font-size: 12px;
  flex-shrink: 0;
}

/* 新建用户弹窗 */
.new-user-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.nu-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.nu-row label {
  font-size: 13px;
  font-weight: bold;
  color: var(--ink);
}
.emoji-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.emoji-opt {
  width: 38px;
  height: 38px;
  border: 2px solid var(--border);
  border-radius: 10px;
  background: var(--card);
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
}
.emoji-opt:hover {
  border-color: var(--leaf);
}
.emoji-opt.on {
  border-color: var(--leaf);
  background: var(--leaf-light);
  box-shadow: var(--shadow);
}
.nu-login-user {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--leaf-light);
  border: 2px solid var(--border);
  border-radius: 12px;
  padding: 10px 12px;
}
.nu-tip {
  font-size: 12px;
  color: var(--ink-light);
  text-align: center;
}

/* 登录弹窗：带头像的账号选择器 */
.login-user-pick {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--leaf-light);
  border: 2px solid var(--border);
  border-radius: 12px;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
  transition: border-color 0.2s;
}
.login-user-pick:hover {
  border-color: var(--leaf-dark);
}
.login-pick-arrow {
  margin-left: auto;
  font-size: 10px;
  color: var(--ink-light);
}
.login-user-list {
  max-height: 200px;
  overflow-y: auto;
  border: 2px solid var(--border);
  border-radius: 12px;
  margin-top: 6px;
  background: #fff;
}
.login-user-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.15s;
}
.login-user-item:hover {
  background: var(--leaf-light);
}
.login-user-item.active {
  background: var(--leaf-light);
}

/* 用户详情弹窗 */
.profile-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 6px 0 10px;
}
.profile-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: #fff;
  box-shadow: var(--shadow);
}
.profile-name {
  font-size: 20px;
  font-weight: bold;
  color: var(--ink);
}
.profile-role {
  font-size: 13px;
  color: var(--ink-light);
}
.profile-tip {
  font-size: 12px;
  color: var(--ink-light);
  text-align: center;
  margin-top: -8px;
}
.profile-actions {
  display: flex;
  justify-content: center;
  gap: 14px;
  padding: 2px 0 16px;
}
.profile-login-link {
  color: var(--leaf-dark);
  font-weight: bold;
  text-decoration: underline;
  cursor: pointer;
  margin-left: 4px;
}
.profile-login-link:hover {
  opacity: 0.8;
}
.confirm-del-text {
  font-size: 14px;
  color: var(--ink);
  line-height: 1.7;
  text-align: center;
}

/* 主体 */
.main {
  flex: 1;
  overflow-y: auto;
  padding: 16px 6px;
  background: var(--card);
  border: 2.5px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}
.chat-list {
  padding: 0 12px;
}

.welcome {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 8px;
  padding: 0 24px;
}
.welcome h2 {
  font-size: 30px;
  color: var(--leaf-dark);
  margin: 0;
}
.welcome p {
  color: var(--ink-light);
}
.quick {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-top: 10px;
}
.quick-chip {
  border: 2px dashed var(--leaf);
  background: var(--leaf-light);
  color: var(--leaf-dark);
  border-radius: 999px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.quick-chip:hover {
  background: var(--leaf);
  color: #fff;
}

/* 输入区 */
.footer {
  padding: 14px 0 16px;
}
.input-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  background: var(--card);
  border: 2.5px solid var(--border);
  border-radius: 999px;
  padding: 8px 10px 8px 14px;
  box-shadow: var(--shadow);
}
.upload-btn {
  border: none;
  color: var(--leaf-dark);
}
.chat-input :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none !important;
  font-size: 15px;
}

/* 上传文件卡片 */
.upload-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0 6px 8px;
}
.upload-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--card);
  border: 2.5px solid var(--border);
  border-radius: 12px;
  padding: 8px 14px;
  min-width: 230px;
  box-shadow: var(--shadow);
  transition: border-color 0.2s;
}
.upload-card.done {
  border-color: var(--leaf);
}
.upload-card.failed {
  border-color: #dc3545;
}
.file-icon {
  width: 34px;
  height: 42px;
  background: #e05a4e;
  color: #fff;
  border-radius: 6px;
  font-size: 11px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.file-info {
  flex: 1;
  min-width: 0;
}
.file-name {
  font-size: 13px;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-meta {
  font-size: 12px;
  color: var(--ink-light);
  margin-top: 2px;
}
.status-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--leaf-light);
  border-top-color: var(--leaf);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.status-mark {
  font-size: 16px;
  font-weight: bold;
  flex-shrink: 0;
}
.status-mark.done {
  color: var(--leaf-dark);
}
.status-mark.failed {
  color: #dc3545;
}
.remove-file {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--ink-light);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s, color 0.2s;
}
.remove-file:hover {
  background: #fdeceb;
  color: #dc3545;
}
</style>

<!-- 下拉菜单挂载在 body 上，需使用全局样式 -->
<style>
.el-dropdown-menu .dd-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #fff;
  margin-right: 8px;
  flex-shrink: 0;
}
.el-dropdown-menu .dd-name {
  font-size: 13px;
  color: var(--ink);
  margin-right: 10px;
}
.el-dropdown-menu .dd-role {
  font-size: 11px;
  color: var(--ink-light);
}
.el-dropdown-menu .dd-new-icon {
  color: var(--leaf-dark);
  margin-right: 6px;
}
.el-dropdown-menu .dd-new {
  font-size: 13px;
  color: var(--leaf-dark);
  font-weight: bold;
}
</style>
