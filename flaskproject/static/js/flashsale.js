// Đặt code này vào file JS của bạn, hoặc trong thẻ <script>
document.addEventListener("DOMContentLoaded", () => {
  // Tìm các phần tử HTML
  const flashSaleContainer = document.getElementById("flash-sale-container");
  const productsGrid = document.getElementById("flash-sale-products-grid");
  const timerElement = document.getElementById("countdown-timer");
  const hoursEl = document.getElementById("hours");
  const minutesEl = document.getElementById("minutes");
  const secondsEl = document.getElementById("seconds");
  const payUrl = window.flashSalePayUrl;
  let countdownInterval; // Biến để lưu trữ interval

  // Hàm gọi API
  async function fetchFlashSale() {
    try {
      // 1. Gọi API
      const response = await fetch("/api/get-flash-sale");
      if (!response.ok) {
        // Nếu backend báo lỗi (ví dụ: pool trống)
        throw new Error("Không thể tải flash sale");
      }
      const data = await response.json(); // data = { products: [...], sale_end_time: "..." }

      // 2. Xóa 5 sản phẩm cũ đi (nếu có)
      productsGrid.innerHTML = "";

      // 3. Lặp qua 5 sản phẩm mới và tạo HTML
      data.products.forEach((product) => {
        const detailUrl = `/product/${product.product_id}`;
        const productElement = document.createElement("div");
        productElement.className = "flash-sale-item"; // Class CSS

        productElement.innerHTML = `
                <a href="${detailUrl}">
                  <img src="/static/${product.image_url}" alt="${product.name}">
                  <div class="product-info">
                      <h3>${product.name}</h3>
                </a>
                    
                    <div class="price-wrapper">
                        <p class="old-price">${product.original_price.toLocaleString(
                          "vi-VN"
                        )}đ</p>
                        
                        <span class="discount-percent">-${
                          product.discount_percent
                        }%</span>
                    </div>
                    
                    <p class="new-price">${product.flash_sale_price.toLocaleString(
                      "vi-VN"
                    )}đ</p>
                    <a class="learn-more" href="${payUrl}">
                      <span class="circle" aria-hidden="true">
                        <span class="icon arrow"></span>
                      </span>
                      <span class="button-text">Mua ngay</span>
                    </a>
                </div>
            `;
        // 4. Thêm sản phẩm vào lưới
        productsGrid.appendChild(productElement);
      });

      // 5. Lấy thời gian kết thúc
      const saleEndTime = new Date(data.sale_end_time);

      // 6. Chạy đồng hồ đếm ngược
      startCountdown(saleEndTime);

      // 7. QUAN TRỌNG: Làm cho toàn bộ mục hiện lên
      flashSaleContainer.style.display = "block";
    } catch (error) {
      console.error("Lỗi Flash Sale:", error);
      flashSaleContainer.style.display = "none"; // Ẩn đi nếu có lỗi
    }
  }

  // Hàm đếm ngược
  function startCountdown(endTime) {
    if (countdownInterval) {
      clearInterval(countdownInterval);
    }

    countdownInterval = setInterval(() => {
      const now = new Date();
      const distance = endTime - now;

      if (distance < 0) {
        // Hết giờ
        clearInterval(countdownInterval);
        timerElement.innerHTML = "ĐÃ KẾT THÚC";
        // Tự động tải lại deal mới sau 5s
        setTimeout(fetchFlashSale, 5000);
        return;
      }

      // Tính toán giờ, phút, giây
      const hours = Math.floor(distance / (1000 * 60 * 60));
      const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((distance % (1000 * 60)) / 1000);

      // Hiển thị (thêm số 0 đằng trước nếu < 10)
      hoursEl.textContent = String(hours).padStart(2, "0");
      minutesEl.textContent = String(minutes).padStart(2, "0");
      secondsEl.textContent = String(seconds).padStart(2, "0");
    }, 1000); // Cập nhật mỗi giây
  }

  // Khởi chạy!
  fetchFlashSale();
});
