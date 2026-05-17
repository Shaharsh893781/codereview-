const token = localStorage.getItem("token");
const loginForm = document.querySelector("#loginForm");
const registerForm = document.querySelector("#registerForm");
const forgotForm = document.querySelector("#forgotForm");
const showLogin = document.querySelector("#showLogin");
const showRegister = document.querySelector("#showRegister");
const showForgot = document.querySelector("#showForgot");
const authStatus = document.querySelector("#authStatus");
const resetFields = document.querySelector("#resetFields");

if (token) {
  window.location.href = "/dashboard";
}

function setStatus(message, isError = false) {
  authStatus.textContent = message;
  authStatus.classList.toggle("error", isError);
}

function showForm(mode) {
  const isLogin = mode === "login";
  const isRegister = mode === "register";
  const isForgot = mode === "forgot";
  loginForm.classList.toggle("hidden", !isLogin);
  registerForm.classList.toggle("hidden", !isRegister);
  forgotForm.classList.toggle("hidden", !isForgot);
  showLogin.classList.toggle("active", isLogin);
  showRegister.classList.toggle("active", isRegister);
  showForgot.classList.toggle("active", isForgot);
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
showForgot.addEventListener("click", () => showForm("forgot"));
document.querySelector("#forgotPasswordLink").addEventListener("click", () => showForm("forgot"));

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

document.querySelector("#requestResetBtn").addEventListener("click", async () => {
  setStatus("Creating OTP...");
  try {
    const data = await postJson("/api/auth/forgot-password", {
      email: document.querySelector("#resetEmail").value.trim(),
    });
    if (data.otp) {
      resetFields.classList.remove("hidden");
      document.querySelector("#resetOtp").value = data.otp;
      setStatus("OTP created. Enter it with your new password to continue.");
      return;
    }
    resetFields.classList.add("hidden");
    setStatus(data.message);
  } catch (error) {
    setStatus(error.message, true);
  }
});

forgotForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Updating password...");
  try {
    const data = await postJson("/api/auth/reset-password", {
      email: document.querySelector("#resetEmail").value.trim(),
      otp: document.querySelector("#resetOtp").value.trim(),
      password: document.querySelector("#newPassword").value,
    });
    completeAuthentication(data);
  } catch (error) {
    setStatus(error.message, true);
  }
});
