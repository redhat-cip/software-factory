function loadTopmenu() {
        var iframe = document.createElement("iframe");
        iframe.setAttribute("src", "/topmenu.html");
        iframe.setAttribute("width", "100%");
        iframe.setAttribute("height", "51px");
        iframe.frameBorder = 0;
        document.body.insertBefore(iframe, document.body.firstChild);
        document.title += ' [SF <%= scope.function_hiera(["sf_version"]) %>]';
};

if (document.addEventListener) {
    document.addEventListener("DOMContentLoaded", loadTopmenu, false);
} else {
    window.onload = loadTopmenu;
}
