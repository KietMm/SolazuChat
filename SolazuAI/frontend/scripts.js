document.addEventListener("DOMContentLoaded", function () {
  const askButton = document.getElementById("askButton");
  const reqButton = document.getElementById("reqButton");
  const portalButton = document.getElementById("portalButton");

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
});
