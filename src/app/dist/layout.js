"use strict";
exports.__esModule = true;
exports.metadata = void 0;
var image_1 = require("next/image");
var google_1 = require("next/font/google");
require("./globals.css");
var page_module_css_1 = require("./page.module.css");
var tongji_js_1 = require("./tongji.js");
var geistSans = google_1.Geist({
    variable: "--font-geist-sans",
    subsets: ["latin"]
});
var geistMono = google_1.Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"]
});
exports.metadata = {
    title: "Puxiao.com",
    description: "I am a front-end developer. Nice to meet you."
};
function RootLayout(_a) {
    var children = _a.children;
    return (React.createElement("html", { lang: "en" },
        React.createElement("head", null,
            React.createElement("script", null, tongji_js_1["default"])),
        React.createElement("body", { className: geistSans.variable + " " + geistMono.variable },
            children,
            React.createElement("footer", { className: page_module_css_1["default"].footer },
                React.createElement("a", { href: "https://github.com/puxiao", target: "_blank", rel: "noopener noreferrer" },
                    React.createElement("span", { className: page_module_css_1["default"].logo },
                        React.createElement(image_1["default"], { src: "/github.svg", alt: "Github", width: 18, height: 18 })),
                    "https://github.com/puxiao")))));
}
exports["default"] = RootLayout;
