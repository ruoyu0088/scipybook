function renderMath() {
    function processNode(node) {
        if (node.tagName === "PRE") return; // Skip <pre> elements

        if (node.nodeType === Node.TEXT_NODE) {
            let text = node.nodeValue;
            if (!text.trim()) return;

            let parts = [];
            let lastIndex = 0;

            // Match both inline ($...$) and display ($$...$$) math
            text.replace(/\$\$(.*?)\$\$|\$(.*?)\$/gs, (match, displayMath, inlineMath, offset) => {
                // Push normal text before match
                if (offset > lastIndex) {
                    parts.push(document.createTextNode(text.slice(lastIndex, offset)));
                }

                // Create math element
                let mathElement = document.createElement(displayMath ? "div" : "span");
                mathElement.className = "math";
                mathElement.textContent = displayMath ? `\\[${displayMath}\\]` : `\\(${inlineMath}\\)`;
                parts.push(mathElement);

                lastIndex = offset + match.length;
            });

            // Push any remaining normal text
            if (lastIndex < text.length) {
                parts.push(document.createTextNode(text.slice(lastIndex)));
            }

            // Replace only if changes were made
            if (parts.length > 0) {
                let parent = node.parentNode;
                parts.forEach((el) => parent.insertBefore(el, node));
                parent.removeChild(node);
            }
        } else {
            // Recursively process child nodes
            Array.from(node.childNodes).forEach(processNode);
        }
    }

    processNode(document.body);
    MathJax.typeset();
}

document.addEventListener("DOMContentLoaded", renderMath);



document.addEventListener('DOMContentLoaded', () => {
    // ページ内のすべての <span> 要素を取得
    const spans = document.querySelectorAll('span.c1');
  
    // 各 <span> 要素を処理
    spans.forEach(span => {
      const textContent = span.textContent;
  
      // 丸数字 (❶～❾) に一致する場合
      const match = textContent.match(/#(❶|❷|❸|❹|❺|❻|❼|❽|❾)/);
      if (match) {
        // `#`と丸数字を分割し、新しいHTMLを設定
        span.innerHTML = `<span style="opacity: 0;">#</span><span style="font-size: 200%; color:#C76E00;">${match[1]}</span>`;
      }
    });


  const divs = document.querySelectorAll('div.cell_input.docutils.container');

  // Iterate through each div to check if it contains the code 'import panel as pn'
  divs.forEach(div => {
    if (div.textContent.includes('import panel as pn') || div.textContent.includes('import hvplot')) {
      console.log('Found the div containing "import panel as pn".');
      const nextDiv = div.nextElementSibling;
      if (nextDiv) {
        nextDiv.style.display = 'none'; // Hide the next div
      }      
    }
  });

  document.querySelectorAll(".plotly-graph-div").forEach(plotlyDiv => {
    let grandparent = plotlyDiv.parentElement?.parentElement;
    if (grandparent) {
        let elementBefore = grandparent.previousElementSibling;
        if (elementBefore) {
            elementBefore.style.display = "none";
        }
    }
});

renderMath();

});