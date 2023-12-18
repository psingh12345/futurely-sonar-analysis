!(function (a) {
    "use strict";
    a(".home-slider").owlCarousel({
        loop: !0,
        autoplay: !0,
        margin: 0,
        animateOut: "fadeOut",
        animateIn: "fadeIn",
        nav: !1,
        autoplayHoverPause: !1,
        items: 1,
        navText: ["<span class='ion-md-arrow-back'></span>", "<span class='ion-chevron-right'></span>"],
        responsive: { 0: { items: 1, nav: !1 }, 600: { items: 1, nav: !1 }, 1000: { items: 1, nav: !1 } },
    }),
        a(".carousel-work").owlCarousel({
            autoplay: !0,
            lazyLoad: !0,
            rewind: !0,
            margin: 20,
            responsiveClass: !0,
            autoHeight: !0,
            autoplayTimeout: 7e3,
            smartSpeed: 800,
            nav: !0,
            navText: ['<span class="ion-ios-arrow-back">', '<span class="ion-ios-arrow-forward">'],
            responsive: { 0: { items: 1 }, 600: { items: 2 }, 900: { items: 3 }, 1024: { items: 4 }, 1300: { items: 4 } },
        }),
        a(".testimonial_slider").owlCarousel({
            autoplay: !0,
            lazyLoad: !0,
            rewind: !0,
            margin: 20,
            responsiveClass: !0,
            autoHeight: !0,
            autoplayTimeout: 7e3,
            smartSpeed: 800,
            nav: !1,
            navText: ['<span class="ion-ios-arrow-back">', '<span class="ion-ios-arrow-forward">'],
            responsive: { 0: { items: 1 }, 600: { items: 1 }, 900: { items: 1 }, 1024: { items: 1 }, 1300: { items: 1 } },
        }),
        a("nav .dropdown").hover(
            function () {
                var e = a(this);
                e.addClass("show"), e.find("> a").attr("aria-expanded", !0), e.find(".dropdown-menu").addClass("show");
            },
            function () {
                var e = a(this);
                e.removeClass("show"), e.find("> a").attr("aria-expanded", !1), e.find(".dropdown-menu").removeClass("show");
            }
        ),
        a("#dropdown04").on("show.bs.dropdown", function () {
            console.log("show");
        });
    a(window).scroll(function () {
        var e = a(this).scrollTop(),
            s = a(".ftco_navbar"),
            o = a(".js-scroll-wrap");
        e > 150 && (s.hasClass("scrolled") || s.addClass("scrolled")),
            e < 150 && s.hasClass("scrolled") && s.removeClass("scrolled sleep"),
            e > 350 && (s.hasClass("awake") || s.addClass("awake"), o.length > 0 && o.addClass("sleep")),
            e < 350 && (s.hasClass("awake") && (s.removeClass("awake"), s.addClass("sleep")), o.length > 0 && o.removeClass("sleep"));
    });
    a(".smoothscroll[href^='#'], #ftco-nav ul li a[href^='#']").on("click", function (e) {
        e.preventDefault();
        var s = this.hash,
            o = a(".navbar-toggler");
        a("html, body").animate({ scrollTop: a(s).offset().top }, 700, "easeInOutExpo", function () {
            window.location.hash = s;
        }),
            o.is(":visible") && o.click();
    }),
        a("body").on("activate.bs.scrollspy", function () {
            console.log("nice");
        }),
        a(document).ready(function () {
            var e;
            a(".video-btn").click(function () {
                e = a(this).data("src");
            }),
                console.log(e),
                a("#myModal").on("shown.bs.modal", function (s) {
                    a("#video").attr("src", e + "?autoplay=1&amp;modestbranding=1&amp;showinfo=0");
                }),
                a("#myModal").on("hide.bs.modal", function (s) {
                    a("#video").attr("src", e);
                });
        });
})(jQuery);
