// Hàm này chạy khi toàn bộ tài liệu được tải xong
document.addEventListener("DOMContentLoaded", function () {
  // Lấy tất cả các nút dropdown
  var dropdownButtons = document.querySelectorAll(".dropbtn");

  // Thêm sự kiện click cho mỗi nút
  dropdownButtons.forEach(function (button) {
    button.onclick = function (event) {
      // Ngăn sự kiện click lan ra ngoài (để window.onclick không bị kích hoạt)
      event.stopPropagation();

      // Lấy nội dung dropdown ngay bên cạnh nút này
      var dropdownContent = this.nextElementSibling;

      // Lấy tất cả các nội dung dropdown đang mở
      var openDropdowns = document.querySelectorAll(".dropdown-content.show");

      // Đóng tất cả các dropdown khác trước
      openDropdowns.forEach(function (openContent) {
        if (openContent !== dropdownContent) {
          openContent.classList.remove("show");
        }
      });

      // Sau đó, bật/tắt (toggle) dropdown hiện tại
      dropdownContent.classList.toggle("show");
    };
  });

  // Thêm sự kiện click cho toàn bộ cửa sổ (để đóng dropdown khi click ra ngoài)
  window.onclick = function (event) {
    // Nếu click không phải là vào nút dropbtn
    if (!event.target.matches(".dropbtn")) {
      // Lấy tất cả nội dung dropdown đang mở
      var dropdowns = document.querySelectorAll(".dropdown-content.show");

      // Đóng tất cả chúng lại
      dropdowns.forEach(function (openDropdown) {
        openDropdown.classList.remove("show");
      });
    }
  };
});
