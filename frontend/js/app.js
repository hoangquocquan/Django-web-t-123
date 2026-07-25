/*
  File này xử lý phần frontend.
  Frontend sẽ gọi API từ backend Python để lấy dữ liệu trong SQLite.
*/

const emptySiteData = {
  products: [],
  capabilities: [],
  news: [],
};

let siteData = emptySiteData;

async function fetchJson(url) {
  // fetch gọi API backend. Nếu backend trả lỗi, hàm sẽ báo lỗi rõ ràng.
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`API lỗi ${response.status}: ${url}`);
  }

  return response.json();
}

async function loadSiteData() {
  /*
    Khi chạy qua backend, dữ liệu đến từ /api/home.
    Nếu bạn mở trực tiếp file HTML bằng file://, fetch sẽ không chạy đúng;
    lúc đó app.js dùng window.siteData từ data.js làm dữ liệu dự phòng.
  */
  try {
    siteData = await fetchJson("/api/home");
  } catch (error) {
    console.warn("Không gọi được API, dùng dữ liệu dự phòng từ data.js.", error);
    siteData = window.siteData || emptySiteData;
  }
}

function renderProducts() {
  // Tìm khu vực có id="productGrid" trong HTML.
  const productGrid = document.querySelector("#productGrid");

  if (!productGrid) return;
  if (productGrid.children.length > 0) return;

  productGrid.innerHTML = siteData.products
    .map(
      (product) => `
        <article class="product-card">
          <img src="${product.image}" alt="${product.name}" />
          <div>
            <span class="tag">${product.category}</span>
            <h3>${product.name}</h3>
            <p>${product.description}</p>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderCapabilities() {
  // Tạo card năng lực sản xuất từ dữ liệu API.
  const capabilityGrid = document.querySelector("#capabilityGrid");

  if (!capabilityGrid) return;
  if (capabilityGrid.children.length > 0) return;

  capabilityGrid.innerHTML = siteData.capabilities
    .map(
      (item, index) => `
        <article class="capability-card">
          <span>${item.icon || String(index + 1).padStart(2, "0")}</span>
          <h3>${item.title}</h3>
          <p>${item.text}</p>
        </article>
      `,
    )
    .join("");
}

function renderNews() {
  // Tạo card tin tức từ dữ liệu API.
  const newsGrid = document.querySelector("#newsGrid");

  if (!newsGrid) return;
  if (newsGrid.children.length > 0) return;

  newsGrid.innerHTML = siteData.news
    .map(
      (item) => `
        <article class="news-card">
          <img src="${item.image}" alt="${item.title}" />
          <div>
            <span class="tag">${item.category}</span>
            <h3>${item.title}</h3>
            <p>${item.description}</p>
          </div>
        </article>
      `,
    )
    .join("");
}

function setupMobileMenu() {
  // Nút menu mobile là nút 3 gạch.
  const header = document.querySelector(".site-header");
  const button = document.querySelector(".menu-button");

  if (!header || !button) return;

  button.addEventListener("click", () => {
    const isOpen = header.classList.toggle("is-open");
    button.setAttribute("aria-expanded", String(isOpen));
  });
}

function setupContactForm() {
  // Form liên hệ sẽ gửi dữ liệu vào API /api/contact để lưu xuống SQLite.
  const form = document.querySelector("#contactForm");
  const message = document.querySelector("#formMessage");

  if (!form || !message) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(form);
    const attachment = formData.get("attachment_file");
    const payload = {
      name: formData.get("name"),
      company: formData.get("company"),
      phone: formData.get("phone"),
      email: formData.get("email"),
      contact: formData.get("email") || formData.get("phone"),
      country: formData.get("country"),
      interested_product: formData.get("interested_product"),
      attachment_url: attachment && attachment.name ? attachment.name : "",
      message: formData.get("message"),
      captcha_answer: formData.get("captcha_answer"),
    };

    try {
      const result = await fetchJsonWithBody("/api/contact", payload);
      form.reset();
      message.textContent = result.message;
    } catch (error) {
      console.error(error);
      message.textContent = "Chưa gửi được yêu cầu. Hãy kiểm tra backend đang chạy chưa.";
    }
  });
}

function setupQuoteForm() {
  // Form báo giá tạo dữ liệu cho CMS Quote.
  const form = document.querySelector("#quoteForm");
  const message = document.querySelector("#quoteMessage");

  if (!form || !message) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = {
      name: formData.get("name"),
      company: formData.get("company"),
      email: formData.get("email"),
      phone: formData.get("phone"),
      product: formData.get("product"),
      quantity: formData.get("quantity"),
      tolerance: formData.get("tolerance"),
      drawing_pdf: formData.get("drawing_pdf"),
      step_file: formData.get("step_file"),
      dwg_file: formData.get("dwg_file"),
      deadline: formData.get("deadline"),
      note: formData.get("note"),
    };

    try {
      const result = await fetchJsonWithBody("/api/quote-request", payload);
      form.reset();
      message.textContent = result.message;
    } catch (error) {
      console.error(error);
      message.textContent = "Chưa gửi được báo giá. Hãy kiểm tra dữ liệu hoặc backend.";
    }
  });
}

function setupApiAwsDemo() {
  // Trang /api-aws.html dùng hàm này để demo frontend gọi API backend.
  const button = document.querySelector("#apiAwsDemoButton");
  const output = document.querySelector("#apiAwsDemoOutput");

  if (!button || !output) return;

  button.addEventListener("click", async () => {
    output.textContent = "Đang gọi API /api/aws-demo...";

    try {
      const result = await fetchJson("/api/aws-demo");
      // JSON.stringify(..., null, 2) giúp JSON hiển thị dễ đọc, có thụt dòng.
      output.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
      console.error(error);
      output.textContent = "Không gọi được API. Hãy kiểm tra backend Python đang chạy chưa.";
    }
  });
}

function setupExternalApiDemo() {
  // Demo API liên kết ngoại: frontend gọi backend local, backend gọi tiếp Open-Meteo.
  const button = document.querySelector("#externalApiDemoButton");
  const output = document.querySelector("#externalApiDemoOutput");

  if (!button || !output) return;

  button.addEventListener("click", async () => {
    output.textContent = "Đang gọi backend /api/external/weather...";

    try {
      const result = await fetchJson("/api/external/weather");
      output.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
      console.error(error);
      output.textContent = "Không gọi được API liên kết ngoại. Hãy kiểm tra backend đang chạy chưa.";
    }
  });
}

function setupAdminCmsHelpers() {
  // Hỏi xác nhận trước khi xóa dữ liệu trong CMS.
  document.querySelectorAll("[data-confirm-delete]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const ok = window.confirm("Bạn chắc chắn muốn xóa mục này?");
      if (!ok) {
        event.preventDefault();
      }
    });
  });

  // Xem trước ảnh khi nhập URL ảnh hoặc chọn file upload.
  document.querySelectorAll(".admin-form").forEach((form) => {
    const preview = form.querySelector("[data-image-preview]");
    const inputs = form.querySelectorAll("[data-image-preview-input]");

    if (!preview || inputs.length === 0) return;

    inputs.forEach((input) => {
      input.addEventListener("input", () => {
        if (input.type !== "file") {
          preview.src = input.value;
        }
      });

      input.addEventListener("change", () => {
        if (input.type === "file" && input.files && input.files[0]) {
          preview.src = URL.createObjectURL(input.files[0]);
        }
      });
    });
  });

  // Copy URL media trong Media Manager.
  document.querySelectorAll("[data-copy-url]").forEach((button) => {
    button.addEventListener("click", async () => {
      const url = button.getAttribute("data-copy-url");
      try {
        await navigator.clipboard.writeText(`${window.location.origin}${url}`);
        const oldText = button.textContent;
        button.textContent = "Đã copy";
        window.setTimeout(() => {
          button.textContent = oldText;
        }, 1200);
      } catch (error) {
        console.error(error);
        window.prompt("Copy URL media:", `${window.location.origin}${url}`);
      }
    });
  });
}

async function fetchJsonWithBody(url, payload) {
  // Gửi dữ liệu JSON lên backend, dùng cho form liên hệ.
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || `API lỗi ${response.status}: ${url}`);
  }

  return data;
}

async function initApp() {
  // Thứ tự chạy: lấy dữ liệu từ API trước, sau đó mới render giao diện.
  await loadSiteData();
  renderProducts();
  renderCapabilities();
  renderNews();
  setupMobileMenu();
  setupContactForm();
  setupQuoteForm();
  setupApiAwsDemo();
  setupExternalApiDemo();
  setupAdminCmsHelpers();
}

initApp();
