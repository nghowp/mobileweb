function addToCart(e, id, name, price, img) {
  e.preventDefault();
  e.stopPropagation();

  fetch("/api/add-cart", {
    method: "post",
    body: JSON.stringify({
      id: id,
      name: name,
      price: price,
      img: img,
      quantity: 1,
    }),
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then(function (res) {
      if (!res.ok) {
        throw new Error("Lỗi khi thêm vào giỏ hàng");
      }
      return res.json();
    })
    .then(function (data) {
      let counter = document.getElementById("cartCounter");
      if (counter) {
        counter.innerText = data.total_quantity;
      }

      console.log("Đã thêm vào giỏ hàng:", data);
    })
    .catch(function (err) {
      console.error(err);
    });
}

function remove_item(id) {
  fetch("/api/remove-cart", {
    method: "POST",
    body: JSON.stringify({
      id: id,
    }),
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((res) => {
      if (!res.ok) {
        throw new Error("Server báo lỗi khi xóa sản phẩm.");
      }
      return res.json();
    })
    .then((data) => {
      if (data.code === 200) {
        location.reload();
      } else {
        alert(data.error || "Không thể xóa sản phẩm.");
      }
    })
    .catch((err) => {
      console.error("Lỗi khi xóa sản phẩm:", err);
      alert("Đã xảy ra lỗi kết nối. Vui lòng thử lại.");
    });
}
