const AUTH_ACCESS = "awaaz_access";
const AUTH_REFRESH = "awaaz_refresh";

function getToken() {
  return localStorage.getItem(AUTH_ACCESS);
}

function setTokens(access, refresh) {
  localStorage.setItem(AUTH_ACCESS, access);
  if (refresh) localStorage.setItem(AUTH_REFRESH, refresh);
}

function clearTokens() {
  localStorage.removeItem(AUTH_ACCESS);
  localStorage.removeItem(AUTH_REFRESH);
}

function requireAuth() {
  const token = getToken();
  if (!token) {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = "/login/?next=" + next;
    return null;
  }
  return token;
}

function authHeaders() {
  const token = getToken();
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = "Bearer " + token;
  return headers;
}

function handleAuthError(status) {
  if (status === 401) {
    clearTokens();
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = "/login/?next=" + next;
    return true;
  }
  return false;
}
