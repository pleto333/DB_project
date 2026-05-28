<template>
  <div class="auth-wrapper">
    <div class="auth-card">
      <div class="logo-area">
        <div class="logo-icon">📈</div>
        <h1 class="logo-title">StockAI</h1>
        <p class="logo-sub">LS증권 뉴스 기반 주식 추천 서비스</p>
      </div>

      <div class="tab-group">
        <button :class="['tab-btn', { active: mode === 'login' }]" @click="mode = 'login'">로그인</button>
        <button :class="['tab-btn', { active: mode === 'register' }]" @click="mode = 'register'">회원가입</button>
      </div>

      <!-- 로그인 폼 -->
      <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="form">
        <div class="input-group">
          <label>아이디</label>
          <input v-model="loginForm.id" type="text" placeholder="아이디를 입력하세요" required />
        </div>
        <div class="input-group">
          <label>비밀번호</label>
          <input v-model="loginForm.password" type="password" placeholder="비밀번호를 입력하세요" required />
        </div>
        <button type="submit" class="submit-btn" :disabled="loginLoading">
          {{ loginLoading ? '로그인 중...' : '로그인' }}
        </button>
        <p v-if="loginError" class="error-msg">{{ loginError }}</p>
      </form>

      <!-- 회원가입 폼 -->
      <form v-if="mode === 'register'" @submit.prevent="handleRegister" class="form">
        <div class="input-group">
          <label>아이디</label>
          <input v-model="registerForm.id" type="text" placeholder="영문+숫자 6~20자" required />
        </div>
        <div class="input-group">
          <label>비밀번호</label>
          <input v-model="registerForm.password" type="password" placeholder="8자 이상" required />
        </div>
        <div class="input-group">
          <label>비밀번호 확인</label>
          <input v-model="registerForm.passwordConfirm" type="password" placeholder="비밀번호를 다시 입력하세요" required />
          <span v-if="registerForm.passwordConfirm && !passwordMatch" class="field-error">비밀번호가 일치하지 않습니다</span>
          <span v-if="registerForm.passwordConfirm && passwordMatch" class="field-ok">✓ 비밀번호 일치</span>
        </div>
        <div class="input-group">
          <label>이메일</label>
          <input v-model="registerForm.email" type="email" placeholder="example@email.com" required />
        </div>
        <div class="input-group">
          <label>닉네임</label>
          <input v-model="registerForm.nickname" type="text" placeholder="닉네임을 입력하세요" required />
        </div>
        <button type="submit" class="submit-btn" :disabled="!passwordMatch || registerLoading">
          {{ registerLoading ? '처리 중...' : '회원가입' }}
        </button>
        <p v-if="registerSuccess" class="success-msg">{{ registerSuccess }}</p>
        <p v-if="registerError" class="error-msg">{{ registerError }}</p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const BASE_URL = 'http://localhost:8080'

const mode = ref('login')

const loginForm = ref({ id: '', password: '' })
const registerForm = ref({ id: '', password: '', passwordConfirm: '', email: '', nickname: '' })

const loginError = ref('')
const loginLoading = ref(false)
const registerSuccess = ref('')
const registerError = ref('')
const registerLoading = ref(false)

const passwordMatch = computed(() =>
  registerForm.value.password && registerForm.value.password === registerForm.value.passwordConfirm
)

async function handleLogin() {
  loginError.value = ''
  loginLoading.value = true
  try {
    const response = await axios.post(`${BASE_URL}/login`, {
      id: loginForm.value.id,
      password: loginForm.value.password
    })
    console.log('로그인 성공:', response.data)
    localStorage.setItem('user_id', response.data.user_id)
    localStorage.setItem('username', response.data.username)
    localStorage.setItem('user_created_at', response.data.created_at || '')
    router.push('/main')
  } catch (error) {
    loginError.value = error.response?.data?.detail?.message || error.response?.data?.message || '아이디 또는 비밀번호가 올바르지 않습니다.'
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  registerError.value = ''
  registerSuccess.value = ''
  registerLoading.value = true
  try {
    const response = await axios.post(`${BASE_URL}/register`, {
      id: registerForm.value.id,
      password: registerForm.value.password,
      email: registerForm.value.email,
      nickname: registerForm.value.nickname
    })
    console.log('회원가입 성공:', response.data)
    registerSuccess.value = '회원가입이 완료되었습니다! 로그인해주세요.'
    setTimeout(() => { mode.value = 'login' }, 1500)
  } catch (error) {
    registerError.value = error.response?.data?.detail?.message || error.response?.data?.message || '회원가입에 실패했습니다. 다시 시도해주세요.'
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped>
.auth-wrapper {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
}

.auth-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 48px 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
}

.logo-area { text-align: center; margin-bottom: 32px; }
.logo-icon { font-size: 48px; margin-bottom: 8px; }
.logo-title {
  font-size: 28px; font-weight: 700; color: #fff;
  margin: 0; letter-spacing: -0.5px;
}
.logo-sub { font-size: 13px; color: rgba(255,255,255,0.5); margin: 6px 0 0; }

.tab-group {
  display: flex; background: rgba(255,255,255,0.08);
  border-radius: 12px; padding: 4px; margin-bottom: 28px;
}
.tab-btn {
  flex: 1; padding: 10px; border: none; background: transparent;
  color: rgba(255,255,255,0.5); border-radius: 10px;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.tab-btn.active {
  background: #3b82f6; color: #fff;
  box-shadow: 0 4px 12px rgba(59,130,246,0.4);
}

.form { display: flex; flex-direction: column; gap: 16px; }
.input-group { display: flex; flex-direction: column; gap: 6px; }
.input-group label { font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.7); }
.input-group input {
  padding: 12px 16px; background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12); border-radius: 10px;
  color: #fff; font-size: 14px; outline: none; transition: border 0.2s;
}
.input-group input:focus {
  border-color: #3b82f6; background: rgba(59,130,246,0.1);
}
.input-group input::placeholder { color: rgba(255,255,255,0.3); }

.submit-btn {
  margin-top: 4px; padding: 14px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border: none; border-radius: 12px; color: #fff;
  font-size: 15px; font-weight: 700; cursor: pointer;
  transition: all 0.2s; box-shadow: 0 4px 16px rgba(59,130,246,0.35);
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(59,130,246,0.5);
}
.submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.error-msg { color: #f87171; font-size: 13px; text-align: center; margin: 0; }
.success-msg { color: #34d399; font-size: 13px; text-align: center; margin: 0; }
.field-error { color: #f87171; font-size: 12px; }
.field-ok { color: #34d399; font-size: 12px; }
</style>
