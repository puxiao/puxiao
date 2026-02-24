"use strict";
exports.__esModule = true;
var page_module_css_1 = require("./page.module.css");
function Home() {
    return (React.createElement("div", { className: page_module_css_1["default"].page },
        React.createElement("main", { className: page_module_css_1["default"].main },
            React.createElement("h1", { className: page_module_css_1["default"].title }, "Welcome to Puxiao.com!"),
            React.createElement("p", { className: page_module_css_1["default"].description }, "I'm a Front End Web Developer: ",
                React.createElement("code", { className: page_module_css_1["default"].code }, "React,Vue,Threejs,Electron,WebGPU"),
                React.createElement("br", null),
                "I wrote some tutorials to share with you."),
            React.createElement("div", { className: page_module_css_1["default"].grid },
                React.createElement("a", { href: "https://github.com/puxiao/react-hook-tutorial", className: page_module_css_1["default"].card },
                    React.createElement("h2", null, "react-hook-tutorial \u2192"),
                    React.createElement("p", null, "https://github.com/puxiao/react-hook-tutorial")),
                React.createElement("a", { href: "https://github.com/puxiao/threejs-tutorial", className: page_module_css_1["default"].card },
                    React.createElement("h2", null, "threejs-tutorial \u2192"),
                    React.createElement("p", null, "https://github.com/puxiao/threejs-tutorial")),
                React.createElement("a", { href: "https://github.com/puxiao/webgpu-tutorial", className: page_module_css_1["default"].card },
                    React.createElement("h2", null, "webgpu-tutorial \u2192"),
                    React.createElement("p", null, "https://github.com/puxiao/webgpu-tutorial")),
                React.createElement("a", { href: "https://github.com/puxiao/wgsl-tutorial", className: page_module_css_1["default"].card },
                    React.createElement("h2", null, "wgsl-tutorial \u2192"),
                    React.createElement("p", null, "https://github.com/puxiao/wgsl-tutorial"))))));
}
exports["default"] = Home;
