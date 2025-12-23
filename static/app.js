const API_URL = "http://localhost:8000";

let token = localStorage.getItem("access_token");

function showTab(tab) {
  document
    .querySelectorAll(".tabs button")
    .forEach((b) => b.classList.remove("active"));
  event.target.classList.add("active");

  if (tab == "login") {
      document.getElementById("login-form").style.display = "flex";
      document.getElementById("register-form").style.display = "none";
      
      console.log("login");
    } else {
      document.getElementById("login-form").style.display = "none";
      document.getElementById("register-form").style.display = "flex";
    console.log("register");
  }
}

async function login() {
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const msg = document.getElementById("auth-message");
  // FastAPI Users /auth/jwt/login expects form data (username, password)
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  console.log(formData);

  try {
    const response = await fetch(`${API_URL}/auth/jwt/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });

    if (response.ok) {
      const data = await response.json();
      token = data.access_token;
      localStorage.setItem("access_token", token);
      msg.textContent = "";
      showApp();
    } else {
      const data = await response.json();
      msg.textContent = "Error: " + (data.detail || "Login failed");
      msg.style.color = "red";
    }
  } catch (error) {
    console.error(error);
    msg.textContent = "Network error";
  }
}

async function register() {
  const email = document.getElementById("register-email").value;
  const password = document.getElementById("register-password").value;
  const msg = document.getElementById("auth-message");

  try {
    const response = fetch("${APP_URL}/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        is_active: true,
        is_superuser: false,
        is_verified: false,
      }),
    });
    if (response.ok) {
      const data = await response.json();
      msg.textContent = "Registration Successful! Please login.";
      msg.style.color = "green";
    } else {
      const data = await response.json();
      msg.textContent = "Error: " + (data.detail || "Registration failed");
      msg.style.color = "red";
    }
  } catch (error) {
    msg.textContent = "Network error";
    console.error(error);
  }
  console.log(email, password);
}

function showApp() {
  document.getElementById("auth-section").style.display = "none";
}
