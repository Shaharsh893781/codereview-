const token = localStorage.getItem("token");
const loginForm = document.querySelector("#loginForm");
const registerForm = document.querySelector("#registerForm");
const showLogin = document.querySelector("#showLogin");
const showRegister = document.querySelector("#showRegister");
const authStatus = document.querySelector("#authStatus");

if (token) {
  window.location.href = "/dashboard";
}

function setStatus(message, isError = false) {
  authStatus.textContent = message;
  authStatus.classList.toggle("error", isError);
}

function showForm(mode) {
  const isLogin = mode === "login";
  loginForm.classList.toggle("hidden", !isLogin);
  registerForm.classList.toggle("hidden", isLogin);
  showLogin.classList.toggle("active", isLogin);
  showRegister.classList.toggle("active", !isLogin);
  setStatus("");
}

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Authentication failed");
  }
  return data;
}

function completeAuthentication(data) {
  localStorage.setItem("token", data.access_token);
  window.location.href = "/dashboard";
}

showLogin.addEventListener("click", () => showForm("login"));
showRegister.addEventListener("click", () => showForm("register"));

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Signing in...");
  try {
    const data = await postJson("/api/auth/login", {
      email: document.querySelector("#loginEmail").value.trim(),
      password: document.querySelector("#loginPassword").value,
    });
    completeAuthentication(data);
  } catch (error) {
    setStatus(error.message, true);
  }
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Creating account...");
  try {
    const data = await postJson("/api/auth/register", {
      full_name: document.querySelector("#registerName").value.trim(),
      email: document.querySelector("#registerEmail").value.trim(),
      password: document.querySelector("#registerPassword").value,
    });
    completeAuthentication(data);
  } catch (error) {
    setStatus(error.message, true);
  }
});
