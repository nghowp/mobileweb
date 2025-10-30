// --- XỬ LÝ HÌNH ẢNH ---
const mainImage = document.getElementById("main-image");
const thumbnails = document.querySelectorAll(".thumbnail-img");

thumbnails.forEach((thumb) => {
  thumb.addEventListener("click", function () {
    mainImage.src = this.dataset.src;
    thumbnails.forEach((t) => {
      t.classList.remove("border-blue-500", "border-transparent");
      t.classList.add("border-transparent");
    });
    this.classList.remove("border-transparent");
    this.classList.add("border-blue-500");
  });
});

// --- XỬ LÝ TĂNG GIẢM SỐ LƯỢNG ---
const qtyPlus = document.getElementById("qty-plus");
const qtyMinus = document.getElementById("qty-minus");
const qtyInput = document.getElementById("quantity-input");

if (qtyPlus) {
  qtyPlus.addEventListener("click", () => {
    qtyInput.value = parseInt(qtyInput.value) + 1;
  });
}

if (qtyMinus) {
  qtyMinus.addEventListener("click", () => {
    const currentValue = parseInt(qtyInput.value);
    if (currentValue > 1) {
      qtyInput.value = currentValue - 1;
    }
  });
}

// --- XỬ LÝ THÊM VÀO GIỎ HÀNG (ĐÃ GỘP VÀ XÓA SIZE/COLOR) ---
const addToCartButton = document.getElementById("add-to-cart-btn");
const productDetailsDiv = document.getElementById("product-details");

if (addToCartButton) {
  addToCartButton.addEventListener("click", function (e) {
    e.preventDefault();

    // 1. Lấy dữ liệu CỐ ĐỊNH của sản phẩm
    const productId = productDetailsDiv.dataset.productId;
    const productName = productDetailsDiv.dataset.productName;
    const productPrice = productDetailsDiv.dataset.productPrice;
    const productImg = productDetailsDiv.dataset.productImg;

    // 2. Lấy dữ liệu TÙY CHỌN (CHỈ CÒN SỐ LƯỢNG)
    const quantity = parseInt(qtyInput.value);

    // --- CÁC DÒNG LẤY MÀU SẮC VÀ KÍCH CỠ ĐÃ BỊ XÓA ---

    // 3. Gửi FETCH request
    fetch("/api/add-cart", {
      method: "post",
      body: JSON.stringify({
        // Gửi đi các thông tin cơ bản
        id: productId,
        name: productName,
        price: productPrice,
        img: productImg,
        quantity: quantity,

        // --- CÁC DÒNG GỬI MÀU SẮC VÀ KÍCH CỠ ĐÃ BỊ XÓA ---
      }),
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("Phản hồi từ server không tốt");
        }
        return res.json();
      })
      .then(function (data) {
        // 4. Cập nhật UI
        let counter = document.getElementById("cartCounter");
        if (counter) {
          counter.innerText = data.total_quantity;
        }
        showToast(`Đã thêm ${quantity} "${productName}" vào giỏ!`, "success");
      })
      .catch(function (err) {
        console.error(err);
        showToast("Có lỗi xảy ra, không thể thêm vào giỏ!", "error");
      });
  });
}

// --- HÀM SHOW TOAST ---
function showToast(message, type = "success") {
  const toastContainer = document.getElementById("toast-notification");
  if (!toastContainer) return;

  // Tạo một phần tử <div> mới cho thông báo
  const toast = document.createElement("div");

  // Dùng class "toast" chung và class "error" riêng
  toast.className = "toast";
  if (type === "error") {
    toast.classList.add("error");
  }

  toast.innerText = message;

  // Thêm thông báo vào vùng chứa
  toastContainer.appendChild(toast);

  // Tự động xóa thông báo sau 3 giây
  setTimeout(() => {
    toast.remove();
  }, 3000);
}
