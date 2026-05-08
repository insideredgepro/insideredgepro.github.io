const SUPABASE_URL = 'https://etkvznyuxjrypxsuomsm.supabase.co';
const SUPABASE_KEY = 'sb_publishable_0lX_Wpsn1t2lnmJj55WTyg_xSQHuY5C';

const _sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

async function requireAuth() {
  const { data: { session } } = await _sb.auth.getSession();
  if (!session) {
    window.location.href = '/login.html';
    return null;
  }
  return session.user;
}

async function signInWithGoogle() {
  const { error } = await _sb.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: 'https://insideredgepro.github.io/index.html' }
  });
  if (error) console.error('Auth error:', error.message);
}

async function signOut() {
  await _sb.auth.signOut();
  window.location.href = '/login.html';
}

async function initAuthUI(containerEl) {
  const { data: { session } } = await _sb.auth.getSession();
  if (!session) return;

  const user = session.user;
  const name = user.user_metadata?.full_name || user.user_metadata?.name || user.email.split('@')[0];
  const avatar = user.user_metadata?.avatar_url;

  containerEl.innerHTML = `
    <div class="auth-user">
      ${avatar ? `<img src="${avatar}" class="auth-avatar" alt="${name}" referrerpolicy="no-referrer"/>` : ''}
      <span class="auth-name">${name}</span>
      <button class="auth-logout-btn" onclick="signOut()">Sign out</button>
    </div>
  `;
}
