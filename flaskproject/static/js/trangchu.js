window.onload = function () {
  khoiTao();

  // Thêm hình vào banner
  // addBanner(
  //   "/static/img/banners/banner0.gif",
  //   "/static/img/banners/banner0.gif"
  // );
  var numBanner = 5; // Số lượng hình banner
  for (var i = 1; i <= numBanner; i++) {
    var linkimg = "/static/img/banners/banner" + i + ".png";
    addBanner(linkimg, linkimg);
  }

  // Khởi động thư viện hỗ trợ banner - chỉ chạy khi đã tạo hình trong banner
  var owl = $(".owl-carousel");
  owl.owlCarousel({
    items: 1.5,
    margin: 100,
    center: true,
    loop: true,
    smartSpeed: 450,
    autoplay: true,
    autoplayTimeout: 3500,
  });

  // Thêm banner
  function addBanner(img, link) {
    var newDiv =
      `<div class='item'>
						<a target='_blank' href=` +
      link +
      `>
							<img src=` +
      img +
      `>
						</a>
					</div>`;
    var banner = document.getElementsByClassName("owl-carousel")[0];
    banner.innerHTML += newDiv;
  }
};
