document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM fully loaded and parsed");

  const askButton = document.getElementById("askButton");
  const reqButton = document.getElementById("reqButton");
  const portalButton = document.getElementById("portalButton");
  const addInputButton = document.getElementById("addInputButton");
  const inputContainer = document.getElementById("inputContainer");
  const submitButton = document.getElementById("submitButton");
  const projectSelect = document.getElementById("projectSelect");
  const epicSelect = document.getElementById("epicSelect");
  const ticketSelect = document.getElementById("ticketSelect");

  let epicCache = {};
  let ticketCache = {};

  // Load danh sách project khi khởi động
  fetchProjects();

  // Debounce function to limit the rate of fetch calls
  function debounce(func, wait) {
    let timeout;
    return function (...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // Xử lý sự kiện nhấn nút submit
  submitButton.addEventListener("click", function () {
    const projectName = projectSelect.value;
    const epicKey =
      epicSelect.value !== "Select epics" ? epicSelect.value : null;
    const ticketKey =
      ticketSelect.value !== "Select ticket" ? ticketSelect.value : null;

    fetchLinks(projectName, epicKey, ticketKey);
  });
  function fetchLinks(projectName, epicKey, ticketKey) {
    console.log("fetchLinks called");

    const requestData = {
      projectName: projectName,
      epicKey: epicKey,
      ticketKey: ticketKey,
    };

    fetch(`http://127.0.0.1:5000/getLink`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestData),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        console.log("Links fetched from server:", data);

        const datasetTableBody = document.getElementById("datasetTableBody");
        datasetTableBody.innerHTML = ""; // Clear any existing rows

        if (data && data.length > 0 && data[0].links_status) {
          data[0].links_status.forEach((item) => {
            const row = document.createElement("tr");

            const fileNameCell = document.createElement("td");
            const fileNameLink = document.createElement("a");
            fileNameLink.href = item.url;
            fileNameLink.innerText = item.url;
            fileNameCell.appendChild(fileNameLink);
            row.appendChild(fileNameCell);

            const dateCell = document.createElement("td");
            dateCell.innerText = item.date;
            row.appendChild(dateCell);

            const statusCell = document.createElement("td");
            statusCell.className = "status";
            statusCell.innerText = item.status;
            row.appendChild(statusCell);

            datasetTableBody.appendChild(row);
          });
        } else {
          console.error("links_status is undefined or empty:", data);
          const noDataRow = document.createElement("tr");
          const noDataCell = document.createElement("td");
          noDataCell.colSpan = 3;
          noDataCell.innerText = "No links available.";
          noDataRow.appendChild(noDataCell);
          datasetTableBody.appendChild(noDataRow);
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("Đã xảy ra lỗi khi lấy dữ liệu: " + error.message);
      });
  }

  // Xử lý sự kiện thay đổi project
  projectSelect.addEventListener(
    "change",
    debounce(function () {
      const projectName = projectSelect.value;
      if (projectName && projectName !== "Select project") {
        if (epicCache[projectName]) {
          displayEpics(epicCache[projectName]);
        } else {
          fetchEpicsByProjectName(projectName);
        }
      } else {
        epicSelect.innerHTML = "<option>Select epics</option>";
        ticketSelect.innerHTML = "<option>Select ticket</option>";
      }
    }, 300)
  );

  // Xử lý sự kiện thay đổi epic
  epicSelect.addEventListener(
    "change",
    debounce(function () {
      const projectName = projectSelect.value;
      const epicKey = epicSelect.value;
      if (epicKey && epicKey !== "Select epics") {
        if (ticketCache[epicKey]) {
          displayTickets(ticketCache[epicKey]);
        } else {
          fetchTicketsByEpicKey(projectName, epicKey);
        }
      } else {
        ticketSelect.innerHTML = "<option>Select ticket</option>";
      }
    }, 300)
  );

  // Hàm fetch projects
  function fetchProjects() {
    fetch(`http://127.0.0.1:5000/getProjectsList`)
      .then((response) => response.json())
      .then((data) => {
        console.log("Projects fetched from server:", data);
        projectSelect.innerHTML = "<option>Select project</option>";
        data.forEach((project) => {
          const option = document.createElement("option");
          option.value = project;
          option.text = project;
          projectSelect.appendChild(option);
        });
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("Đã xảy ra lỗi khi lấy danh sách projects.");
      });
  }

  // Hàm fetch epics theo tên project
  function fetchEpicsByProjectName(projectName) {
    fetch(`http://127.0.0.1:5000/getEpicsList?projectName=${projectName}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("Epics fetched from server:", data);
        epicCache[projectName] = data.epics;
        displayEpics(data.epics);
      })
      .catch((error) => {
        console.error("Error:", error);
        alert(
          "Đã xảy ra lỗi khi lấy danh sách epics. Chi tiết lỗi: " +
            error.message
        );
      });
  }

  // Hàm display epics
  function displayEpics(epics) {
    const selectedEpic = epicSelect.value;
    epicSelect.innerHTML = "<option>Select epics</option>";
    ticketSelect.innerHTML = "<option>Select ticket</option>";
    if (epics && epics.length > 0) {
      epics.forEach((epic) => {
        const option = document.createElement("option");
        option.value = epic.key;
        option.text = epic.name;
        epicSelect.appendChild(option);
      });
    }
    if (selectedEpic) {
      epicSelect.value = selectedEpic;
    }
  }

  // Hàm fetch tickets theo tên epic
  function fetchTicketsByEpicKey(projectName, epicKey) {
    fetch(
      `http://127.0.0.1:5000/getTicketsList?projectName=${projectName}&epicKey=${epicKey}`
    )
      .then((response) => response.json())
      .then((data) => {
        console.log("Tickets fetched from server:", data);
        ticketCache[epicKey] = data.tickets;
        displayTickets(data.tickets);
      })
      .catch((error) => {
        console.error("Error:", error);
        alert(
          "Đã xảy ra lỗi khi lấy danh sách tickets. Chi tiết lỗi: " +
            error.message
        );
      });
  }

  // Hàm display tickets
  function displayTickets(tickets) {
    const selectedTicket = ticketSelect.value;
    ticketSelect.innerHTML = "<option>Select ticket</option>";
    if (tickets && tickets.length > 0) {
      tickets.forEach((ticket) => {
        const option = document.createElement("option");
        option.value = ticket.key;
        option.text = ticket.name;
        ticketSelect.appendChild(option);
      });
    }
    if (selectedTicket) {
      ticketSelect.value = selectedTicket;
    }
  }

  // Xử lý sự kiện click cho mỗi mục sidebar
  if (askButton) {
    askButton.addEventListener("click", function () {
      resetButtons();
      askButton.classList.add("active");
      window.location.href = "ask.html";
    });
  }

  if (reqButton) {
    reqButton.addEventListener("click", function () {
      resetButtons();
      reqButton.classList.add("active");
      window.location.href = "req.html";
    });
  }

  if (portalButton) {
    portalButton.addEventListener("click", function () {
      resetButtons();
      portalButton.classList.add("active");
      window.location.href = "portal.html";
    });
  }

  // Xử lý sự kiện click cho button thêm input
  if (addInputButton) {
    addInputButton.addEventListener("click", function () {
      const newInput = document.createElement("input");
      newInput.type = "text";
      newInput.className = "link-input";
      newInput.placeholder = "Input your link";
      inputContainer.appendChild(newInput);
    });
  }

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
    askButton?.classList.remove("active");
    reqButton?.classList.remove("active");
    portalButton?.classList.remove("active");
  }

  // Xử lý sự kiện click cho nút Submit
  if (submitButton) {
    submitButton.addEventListener("click", function () {
      console.log("Submit button clicked");
      const projectName = projectSelect.value;
      const epicKey =
        epicSelect.value !== "Select epics" ? epicSelect.value : null;
      const ticketKey =
        ticketSelect.value !== "Select ticket" ? ticketSelect.value : null;
      submitData(projectName, epicKey, ticketKey);
    });
  } else {
    console.error("Submit button not found");
  }
});

function openReplyPage() {
  window.location.href = "reply.html";
}

// Hàm hiển thị ẩn hiện question và chat
function showDiv2() {
  document.getElementById("question").classList.add("hidden");
  document.getElementById("chat-container").classList.remove("hidden");
}

function showDiv1() {
  document.getElementById("question").classList.remove("hidden");
  document.getElementById("chat-container").classList.add("hidden");
}

// Gán sự kiện click cho nút
document.getElementById("reply").addEventListener("click", showDiv2);
document.getElementById("Back").addEventListener("click", showDiv1);
// Xử lý gửi tin nhắn và hiển thị tin nhắn trong cửa sổ chat
document.getElementById("send-button").addEventListener("click", function () {
  var messageInput = document.getElementById("message-input");
  var messageText = messageInput.value.trim();

  if (messageText !== "") {
    var userMessage = document.createElement("div");
    userMessage.className = "message user-message";
    userMessage.innerHTML = "<p>" + messageText + "</p>";
    document.getElementById("chat-messages").appendChild(userMessage);

    // Scroll to the bottom
    document.getElementById("chat-messages").scrollTop =
      document.getElementById("chat-messages").scrollHeight;

    messageInput.value = "";
  }
});

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

/// post and get dữ liệu từ portal vào db và lấy
function submitData(projectName, epicKey, ticketKey) {
  console.log("submitData called");

  const linkInput = document.querySelector(".link-input");

  const data = {
    projectName: projectName,
    epicName: epicKey,
    ticketName: ticketKey,
    githubLink: null,
    jiraLink: null,
    docsLink: null,
    confluenceLink: null,
  };

  if (linkInput && linkInput.value) {
    if (linkInput.value.includes("github.com")) {
      data.githubLink = linkInput.value;
    } else if (linkInput.value.includes("jira.")) {
      data.jiraLink = linkInput.value;
    } else if (linkInput.value.includes("docs.google.com")) {
      data.docsLink = linkInput.value;
    } else if (linkInput.value.includes("confluence.")) {
      data.confluenceLink = linkInput.value;
    }
  }

  console.log("Data to be sent:", data);

  fetch("http://127.0.0.1:5000/addToDatabase", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Response from server:", data);
      if (data.error) {
        alert(data.error);
      } else {
        alert("Dữ liệu đã được thêm hoặc cập nhật thành công");
        fetchLinks(projectName, epicKey, ticketKey);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Đã xảy ra lỗi khi gửi dữ liệu.");
    });
}

// load epic và ticket khi chọn tên project

document
  .getElementById("projectSelect")
  .addEventListener("change", function () {
    const projectName = this.value;
    if (projectName && projectName !== "Select project") {
      fetchEpicsByProjectName(projectName);
    } else {
      document.getElementById("epicSelect").innerHTML =
        "<option>Select epics</option>";
      document.getElementById("ticketSelect").innerHTML =
        "<option>Select ticket</option>";
    }
  });

document.getElementById("epicSelect").addEventListener("change", function () {
  const projectName = document.getElementById("projectSelect").value;
  const epicKey = this.value;
  if (epicKey && epicKey !== "Select epics") {
    fetchTicketsByEpicKey(projectName, epicKey);
  } else {
    document.getElementById("ticketSelect").innerHTML =
      "<option>Select ticket</option>";
  }
});

//click submit mới xem được links
