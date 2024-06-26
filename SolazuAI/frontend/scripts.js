document.addEventListener("DOMContentLoaded", function () {
  const askButton = document.getElementById("askButton");
  const reqButton = document.getElementById("reqButton");
  const portalButton = document.getElementById("portalButton");
  const addInputButton = document.getElementById("addInputButton");
  const inputContainer = document.getElementById("inputContainer");

  // Xử lý sự kiện click cho mỗi mục sidebar
  askButton.addEventListener("click", function () {
    resetButtons();
    askButton.classList.add("active");
    window.location.href = "ask.html";
  });

  reqButton.addEventListener("click", function () {
    resetButtons();
    reqButton.classList.add("active");
    window.location.href = "req.html";
  });

  portalButton.addEventListener("click", function () {
    resetButtons();
    portalButton.classList.add("active");
    window.location.href = "portal.html";
  });

  // Xử lý sự kiện click cho button thêm input
  addInputButton.addEventListener("click", function () {
    const inputGroup = inputContainer.getElementsByClassName("input-group");
    const newInput = document.createElement("input");
    newInput.type = "text";
    newInput.className = "link-input";
    newInput.placeholder = "Input your Link";
    inputContainer.appendChild(newInput);
  });

  // Đặt active class cho mục tương ứng với trang hiện tại
  const currentPage = window.location.pathname.split("/").pop();
  if (currentPage === "ask.html") {
    resetButtons();
    askButton.classList.add("active");
  } else if (currentPage === "req.html") {
    resetButtons();
    reqButton.classList.add("active");
  } else if (currentPage === "portal.html") {
    resetButtons();
    portalButton.classList.add("active");
  }

  // Hàm resetButtons để loại bỏ class active từ tất cả các nút
  function resetButtons() {
    askButton.classList.remove("active");
    reqButton.classList.remove("active");
    portalButton.classList.remove("active");
  }

  // neu nhieu hon 5 o input bat dau cuon dco
});

function openReplyPage() {
  window.location.href = "reply.html";
}

// Click để gọi các câu hỏi khác trong req
// scripts.js

// scripts.js

function toggleDivs(divId) {
  var div1 = document.getElementById("question");
  var div2 = document.getElementById("chat-container");

  // Show the clicked div and hide the other
  if (divId === "question") {
    div1.style.display = "block";
    div2.style.display = "none";
  } else if (divId === "chat-container") {
    div1.style.display = "none";
    div2.style.display = "block";
  }
}

// Xử lý gửi tin nhắn và hiển thị tin nhắn trong cửa sổ chat
function sendMessage() {
  var messageInput = document.getElementById("message-input");
  var messageText = messageInput.value;

  if (messageText.trim() !== "") {
    var chatWindow = document.getElementById("chat-window");

    // Tạo phần tử tin nhắn mới
    var messageElement = document.createElement("div");
    messageElement.classList.add("message");
    messageElement.textContent = messageText;

    // Thêm tin nhắn mới vào cửa sổ chat
    chatWindow.appendChild(messageElement);

    // Cuộn xuống cuối cửa sổ chat
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Xóa nội dung trong ô nhập tin nhắn
    messageInput.value = "";
  }
}

function closeChat() {
  document.querySelector(".chat-container").style.display = "none";
}

// Di chuyển giữa các tab trong portal
function showTab(tabName) {
  // Get all tab elements
  var tabs = document.getElementsByClassName("tab");
  // Remove the active class from all tabs
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].classList.remove("active");
  }

  // Add the active class to the clicked tab
  document.getElementById(tabName + "Tab").classList.add("active");

  // Get all content elements
  var contents = document.getElementsByClassName("tab-content");
  // Hide all content elements
  for (var i = 0; i < contents.length; i++) {
    contents[i].style.display = "none";
  }

  // Show the content of the clicked tab
  document.getElementById(tabName + "Content").style.display = "block";
}

// Initially show the content of the first tab
document.getElementById("jiraContent").style.display = "block";
