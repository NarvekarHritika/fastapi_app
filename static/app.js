const API_URL = "http://localhost:8000"; // Adjust if necessary

// --- State Management ---
let token = localStorage.getItem("access_token");

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  if (token) {
    showApp();
  } else {
    showAuth();
  }
});

// --- Auth Functions ---

function showTab(tab) {
  document
    .querySelectorAll(".tabs button")
    .forEach((b) => b.classList.remove("active"));
  event.target.classList.add("active");

  if (tab === "login") {
    document.getElementById("login-form").style.display = "flex";
    document.getElementById("register-form").style.display = "none";
  } else {
    document.getElementById("login-form").style.display = "none";
    document.getElementById("register-form").style.display = "flex";
  }
}

async function login() {
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const msg = document.getElementById("auth-message");

  // FastAPI Users /auth/jwt/login expects form data (username, password)
  const formData = new URLSearchParams();
  formData.append("username", email); // FastAPI OAuth2PasswordRequestForm uses 'username'
  formData.append("password", password);

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
    const response = await fetch(`${API_URL}/auth/register`, {
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
      msg.textContent = "Registration successful! Please login.";
      msg.style.color = "green";
      showTab("login");
    } else {
      const data = await response.json();
      msg.textContent = "Error: " + (data.detail || "Registration failed");
      msg.style.color = "red";
    }
  } catch (error) {
    console.error(error);
    msg.textContent = "Network error";
  }
}

function showApp() {
  document.getElementById("auth-section").style.display = "none";
  document.getElementById("app-section").style.display = "block";
  // Ideally fetch user info here to show email
  fetchFeed();
}
function showAuth() {
  document.getElementById("auth-section").style.display = "block";
  document.getElementById("app-section").style.display = "none";
}

function logout() {
  token = null;
  localStorage.removeItem("access_token");
  showAuth();
}

// --- App Functions ---

async function fetchFeed() {
  const container = document.getElementById("feed-container");
  container.innerHTML = "Loading...";

  try {
    const response = await fetch(`${API_URL}/feed`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.status === 401) {
      logout();
      return;
    }

    const data = await response.json();
    renderFeed(data.posts);
  } catch (error) {
    console.error(error);
    container.innerHTML = "Error loading feed.";
  }
}

function renderFeed(posts) {
  const container = document.getElementById("feed-container");
  container.innerHTML = "";

  if (posts.length === 0) {
    container.innerHTML = "<p>No posts yet.</p>";
    return;
  }

  posts.forEach((post) => {
    const isImage = post.file_type === "image";
    const mediaHtml = isImage
      ? `<img src="${post.url}" class="post-media" alt="Post content">`
      : `<video src="${post.url}" class="post-media" controls></video>`;

    const deleteBtn = post.is_owner
      ? `<button class="btn-delete" onclick="deletePost('${post.id}')">Delete</button>`
      : "";

    const postHtml = `
            <div class="post">
                <div class="post-header">
                    <span>${post.email || "User"}</span>
                    <span>${new Date(post.created_at).toLocaleString()}</span>
                </div>
                ${mediaHtml}
                <div class="post-caption">${post.caption}</div>
                <div style="margin-top: 10px; text-align: right;">
                    ${deleteBtn}
                </div>
            </div>
        `;
    container.innerHTML += postHtml;
  });
}

async function uploadFile() {
  const fileInput = document.getElementById("file-input");
  const captionInput = document.getElementById("caption-input");
  const msg = document.getElementById("upload-message");

  if (fileInput.files.length === 0) {
    msg.textContent = "Please select a file.";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("caption", captionInput.value);

  msg.textContent = "Uploading...";

  try {
    const response = await fetch(`${API_URL}/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    if (response.ok) {
      msg.textContent = "Upload successful!";
      msg.style.color = "green";
      fileInput.value = "";
      captionInput.value = "";
      fetchFeed();
    } else {
      const data = await response.json();
      msg.textContent = "Error: " + (data.detail || "Upload failed");
      msg.style.color = "red";
    }
  } catch (error) {
    console.error(error);
    msg.textContent = "Network error";
  }
}

async function deletePost(postId) {
  if (!confirm("Are you sure you want to delete this post?")) return;

  try {
    const response = await fetch(`${API_URL}/delete/${postId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.ok) {
      fetchFeed();
    } else {
      const data = await response.json();
      alert("Error: " + (data.detail || "Delete failed"));
    }
  } catch (error) {
    console.error(error);
    alert("Network error");
  }
}
