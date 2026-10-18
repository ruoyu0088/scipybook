// 语言切换：在 /ja/ 和 /zh/ 的同一页面之间跳转
// scipybook 的日文文件名带 -jp 后缀、中文版没有，所以要按后缀换算目标页，
// 并准备几个候选（换不过去就退到对方语言的首页）。
(function () {
  var m = location.pathname.match(/^(.*\/)(ja|zh)\/(.*)$/);
  if (!m) return;

  var root = m[1];
  var lang = m[2];
  var page = m[3] || "index.html";
  var other = lang === "ja" ? "zh" : "ja";

  // 目标页候选：① 后缀换算 ② 同名页 ③ 对方首页
  var name = page.indexOf("/") === -1 ? page : page.split("/").pop();
  var cands = [];
  if (lang === "ja") {
    cands.push(name.replace(/-jp\.html$/, ".html"));
  } else {
    cands.push(name.replace(/\.html$/, "-jp.html"));
  }
  cands.push(name);
  cands.push("index.html");
  cands = cands.filter(function (v, i) { return v && cands.indexOf(v) === i; });

  function target(c) {
    return root + other + "/" + c;
  }

  var a = document.createElement("a");
  a.href = target(cands[0]);
  a.textContent = other === "zh" ? "中文" : "日本語";
  a.title = other === "zh" ? "切换到中文版" : "日本語版へ";
  a.rel = "alternate";
  a.hreflang = other;
  a.style.cssText = [
    "position:fixed", "top:10px", "right:14px", "z-index:9999",
    "padding:3px 10px", "border:1px solid currentColor", "border-radius:4px",
    "font-size:13px", "line-height:1.6", "text-decoration:none",
    "opacity:.75", "background:var(--pst-color-background, transparent)"
  ].join(";");

  // 对方语言没有这一页时（日文版有 legacy 页面），退到对方首页
  function resolve(i) {
    if (i >= cands.length - 1) return;
    fetch(target(cands[i]), { method: "HEAD" })
      .then(function (r) {
        if (!r.ok) {
          a.href = target(cands[i + 1]);
          resolve(i + 1);
        }
      })
      .catch(function () {
        a.href = target(cands[cands.length - 1]);
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.body.appendChild(a);
    resolve(0);
  });
})();
