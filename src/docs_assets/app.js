/* DINO Bounding Box Viewer — client-side rendering */

(function () {
  "use strict";

  // ---- Default settings ----
  var DEFAULTS = {
    model: "DinoManWoman",
    threshold: "0.25",
    man_color: "#0000ff",
    woman_color: "#ff0000",
    thickness: "2",
    font_size: "14",
    text_v: "top",
    text_h: "left",
    text_place: "outside",
    fix_overlap: "0",
  };

  // ---- State ----
  var settings = {};
  var detectionCache = {};

  // ---- Hash ↔ Settings ----

  function parseHash() {
    var hash = location.hash.replace(/^#/, "");
    var params = {};
    if (hash) {
      hash.split("&").forEach(function (pair) {
        var parts = pair.split("=");
        if (parts.length === 2) {
          params[decodeURIComponent(parts[0])] = decodeURIComponent(parts[1]);
        }
      });
    }
    return params;
  }

  function buildHash(s) {
    var parts = [];
    Object.keys(s).forEach(function (key) {
      parts.push(encodeURIComponent(key) + "=" + encodeURIComponent(s[key]));
    });
    return parts.join("&");
  }

  function updateHash() {
    history.replaceState(null, "", "#" + buildHash(settings));
  }

  function loadSettings() {
    var params = parseHash();
    Object.keys(DEFAULTS).forEach(function (key) {
      settings[key] = params[key] !== undefined ? params[key] : DEFAULTS[key];
    });
  }

  function populateControls() {
    Object.keys(settings).forEach(function (key) {
      var el = document.getElementById(key);
      if (!el) return;
      if (el.type === "checkbox") {
        el.checked = settings[key] === "1";
      } else {
        el.value = settings[key];
      }
      // Update range slider labels
      var valSpan = document.getElementById(key + "-val");
      if (valSpan) valSpan.textContent = settings[key];
    });
  }

  function readControls() {
    Object.keys(DEFAULTS).forEach(function (key) {
      var el = document.getElementById(key);
      if (!el) return;
      if (el.type === "checkbox") {
        settings[key] = el.checked ? "1" : "0";
      } else {
        settings[key] = el.value;
      }
    });
  }

  // ---- Detection data loading ----

  function dataBasePath() {
    // Detect if we're on an image page (path contains /image/)
    if (location.pathname.indexOf("/image/") !== -1) {
      return "../data/";
    }
    return "data/";
  }

  function fetchDetections(model, imageId, callback) {
    var cacheKey = model + "_" + imageId;
    if (detectionCache[cacheKey]) {
      callback(detectionCache[cacheKey]);
      return;
    }
    var url = dataBasePath() + model + "_" + imageId + ".json";
    fetch(url)
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        detectionCache[cacheKey] = data;
        callback(data);
      })
      .catch(function () {
        callback(null);
      });
  }

  // ---- SVG rendering ----

  function colorForLabel(label) {
    if (label.indexOf("woman") !== -1) return settings.woman_color;
    return settings.man_color;
  }

  // Approximate bounding rect for a monospace SVG text element.
  // ty is the baseline y; the visual top is roughly ty - fontSize.
  function textBBox(tx, ty, anchor, labelStr, fontSize) {
    var charW = fontSize * 0.6;
    var textW = labelStr.length * charW;
    var left;
    if (anchor === "start") left = tx;
    else if (anchor === "middle") left = tx - textW / 2;
    else left = tx - textW;
    return {
      left: left,
      top: ty - fontSize,
      right: left + textW,
      bottom: ty + fontSize * 0.25,
    };
  }

  function bboxOverlaps(a, b) {
    return a.left < b.right && a.right > b.left
        && a.top < b.bottom && a.bottom > b.top;
  }

  function resolveOverlaps(labels, fontSize) {
    // Greedy: for each label, if it overlaps a previous one,
    // nudge it down by fontSize increments until clear.
    for (var i = 1; i < labels.length; i++) {
      var tries = 0;
      while (tries < 20) {
        var dominated = false;
        var bb = textBBox(
          labels[i].tx, labels[i].ty,
          labels[i].anchor, labels[i].str, fontSize
        );
        for (var j = 0; j < i; j++) {
          var prev = textBBox(
            labels[j].tx, labels[j].ty,
            labels[j].anchor, labels[j].str, fontSize
          );
          if (bboxOverlaps(bb, prev)) {
            dominated = true;
            break;
          }
        }
        if (!dominated) break;
        labels[i].ty += fontSize + 2;
        tries++;
      }
    }
  }

  function renderBoxes(svg, data) {
    // Clear existing boxes
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    if (!data || !data.boxes) return;

    var threshold = parseFloat(settings.threshold);
    var thickness = parseInt(settings.thickness, 10);
    var fontSize = parseInt(settings.font_size, 10);
    var textV = settings.text_v;
    var textH = settings.text_h;
    var textPlace = settings.text_place;
    var fixOverlap = settings.fix_overlap === "1";

    // First pass: draw rectangles, compute label positions
    var labels = [];
    data.boxes.forEach(function (box) {
      if (box.score < threshold) return;

      var color = colorForLabel(box.label);
      var w = box.x1 - box.x0;
      var h = box.y1 - box.y0;

      // Rectangle
      var rect = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "rect"
      );
      rect.setAttribute("x", box.x0);
      rect.setAttribute("y", box.y0);
      rect.setAttribute("width", w);
      rect.setAttribute("height", h);
      rect.setAttribute("fill", "none");
      rect.setAttribute("stroke", color);
      rect.setAttribute("stroke-width", thickness);
      svg.appendChild(rect);

      var labelStr = box.label + " " + box.score.toFixed(2);
      var pad = 4;

      // Horizontal position + anchor
      var tx, anchor;
      if (textH === "left") {
        tx = box.x0 + pad;
        anchor = "start";
      } else if (textH === "center") {
        tx = box.x0 + w / 2;
        anchor = "middle";
      } else {
        tx = box.x1 - pad;
        anchor = "end";
      }

      // Vertical position (inside/outside flips direction)
      var ty;
      if (textV === "top") {
        ty = textPlace === "outside"
          ? box.y0 - pad
          : box.y0 + fontSize + pad;
      } else if (textV === "center") {
        ty = box.y0 + h / 2 + fontSize / 3;
      } else {
        ty = textPlace === "outside"
          ? box.y1 + fontSize + pad
          : box.y1 - pad;
      }

      labels.push({ tx: tx, ty: ty, anchor: anchor, str: labelStr, color: color });
    });

    // Resolve overlaps if enabled
    if (fixOverlap) resolveOverlaps(labels, fontSize);

    // Second pass: create text elements
    labels.forEach(function (lbl) {
      var text = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "text"
      );
      text.setAttribute("x", lbl.tx);
      text.setAttribute("y", lbl.ty);
      text.setAttribute("fill", lbl.color);
      text.setAttribute("font-size", fontSize);
      text.setAttribute("font-family", "monospace");
      text.setAttribute("text-anchor", lbl.anchor);
      text.setAttribute("stroke", "#000");
      text.setAttribute("stroke-width", "3");
      text.setAttribute("paint-order", "stroke");
      text.textContent = lbl.str;
      svg.appendChild(text);
    });
  }

  // ---- Render all overlays on the page ----

  function renderAll() {
    var model = settings.model;

    // Gallery cards
    var cards = document.querySelectorAll(".card[data-image-id]");
    cards.forEach(function (card) {
      var imageId = card.getAttribute("data-image-id");
      var svg = card.querySelector("svg.overlay");
      if (!svg) return;
      fetchDetections(model, imageId, function (data) {
        renderBoxes(svg, data);
      });
    });

    // Single image page
    var wrap = document.querySelector(
      ".single-image-wrap[data-image-id]"
    );
    if (wrap) {
      var imageId = wrap.getAttribute("data-image-id");
      var svg = wrap.querySelector("svg.overlay");
      if (svg) {
        fetchDetections(model, imageId, function (data) {
          renderBoxes(svg, data);
          updateDetectionsTable(data);
        });
      }
    }
  }

  // ---- Detections table (image page only) ----

  function updateDetectionsTable(data) {
    var tbody = document.querySelector("#detections-table tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    if (!data || !data.boxes) return;

    var threshold = parseFloat(settings.threshold);
    data.boxes.forEach(function (box) {
      var tr = document.createElement("tr");
      if (box.score < threshold) tr.className = "hidden-box";
      tr.innerHTML =
        "<td>" +
        box.label +
        "</td><td>" +
        box.score.toFixed(4) +
        "</td><td>" +
        (box.score >= threshold ? "Yes" : "No") +
        "</td>";
      tbody.appendChild(tr);
    });
  }

  // ---- Zip download ----

  function isoDatetime() {
    var d = new Date();
    var pad = function (n) { return n < 10 ? "0" + n : "" + n; };
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" +
      pad(d.getDate()) + "T" + pad(d.getHours()) + "." +
      pad(d.getMinutes()) + "." + pad(d.getSeconds());
  }

  function triggerDownload(blob, filename) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Composite an <img> and its sibling SVG overlay into a PNG blob.
  function compositeImage(imgEl, svgEl, width, height) {
    return new Promise(function (resolve, reject) {
      var canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      var ctx = canvas.getContext("2d");

      // Draw the photograph
      ctx.drawImage(imgEl, 0, 0, width, height);

      // Clone SVG, set explicit dimensions so it rasterises correctly
      var clone = svgEl.cloneNode(true);
      clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
      clone.setAttribute("width", width);
      clone.setAttribute("height", height);

      var svgData = new XMLSerializer().serializeToString(clone);
      var svgBlob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
      var svgUrl = URL.createObjectURL(svgBlob);

      var svgImg = new Image();
      svgImg.onload = function () {
        ctx.drawImage(svgImg, 0, 0, width, height);
        URL.revokeObjectURL(svgUrl);
        canvas.toBlob(function (blob) {
          resolve(blob);
        }, "image/png");
      };
      svgImg.onerror = function () {
        URL.revokeObjectURL(svgUrl);
        reject(new Error("SVG rasterisation failed"));
      };
      svgImg.src = svgUrl;
    });
  }

  function downloadSingleImage(imageId, btn) {
    readControls();
    updateHash();
    btn.disabled = true;
    btn.textContent = "Zipping\u2026";
    var model = settings.model;
    var pageUrl = location.href;

    var wrap = document.querySelector(
      ".single-image-wrap[data-image-id=\"" + imageId + "\"]"
    );
    var imgEl = wrap.querySelector("img");
    var svgEl = wrap.querySelector("svg.overlay");
    var w = parseInt(wrap.getAttribute("data-width"), 10);
    var h = parseInt(wrap.getAttribute("data-height"), 10);

    compositeImage(imgEl, svgEl, w, h).then(function (blob) {
      var zip = new JSZip();
      zip.file(imageId + ".png", blob);
      zip.file("url.txt", pageUrl + "\n");
      var zipName = isoDatetime() + "_" + model + "_" + imageId + ".zip";
      return zip.generateAsync({ type: "blob" }).then(function (content) {
        triggerDownload(content, zipName);
        btn.disabled = false;
        btn.textContent = "Download image (.zip)";
      });
    }).catch(function () {
      btn.disabled = false;
      btn.textContent = "Download image (.zip)";
    });
  }

  function downloadAllImages(btn) {
    readControls();
    updateHash();
    btn.disabled = true;
    btn.textContent = "Zipping\u2026";
    var model = settings.model;
    var pageUrl = location.href;

    var cards = document.querySelectorAll(".card[data-image-id]");
    var zip = new JSZip();
    zip.file("url.txt", pageUrl + "\n");

    var composites = [];
    cards.forEach(function (card) {
      var id = card.getAttribute("data-image-id");
      var imgEl = card.querySelector("img");
      var svgEl = card.querySelector("svg.overlay");
      var w = parseInt(card.getAttribute("data-width"), 10);
      var h = parseInt(card.getAttribute("data-height"), 10);
      composites.push(
        compositeImage(imgEl, svgEl, w, h).then(function (blob) {
          zip.file(id + ".png", blob);
        })
      );
    });

    Promise.all(composites).then(function () {
      var zipName = isoDatetime() + "_" + model + "_Tropes1500.zip";
      return zip.generateAsync({ type: "blob" }).then(function (content) {
        triggerDownload(content, zipName);
        btn.disabled = false;
        btn.textContent = "Download all images (.zip)";
      });
    }).catch(function () {
      btn.disabled = false;
      btn.textContent = "Download all images (.zip)";
    });
  }

  // ---- Settings change handlers ----

  function onSettingsChange() {
    readControls();
    updateHash();
    renderAll();
  }

  function attachHandlers() {
    // All settings controls
    Object.keys(DEFAULTS).forEach(function (key) {
      var el = document.getElementById(key);
      if (!el) return;
      var event = (el.tagName === "SELECT" || el.type === "checkbox") ? "change" : "input";
      el.addEventListener(event, function () {
        // Update label for range sliders
        var valSpan = document.getElementById(key + "-val");
        if (valSpan) valSpan.textContent = el.value;
        onSettingsChange();
      });
    });

    // Gallery card links — preserve settings in hash
    var cards = document.querySelectorAll("a.card[data-image-id]");
    cards.forEach(function (card) {
      card.addEventListener("click", function (e) {
        e.preventDefault();
        readControls();
        var imageId = card.getAttribute("data-image-id");
        location.href = "image/" + imageId + ".html#" + buildHash(settings);
      });
    });

    // "Use these settings for all images" button
    var useForAll = document.getElementById("use-for-all");
    if (useForAll) {
      useForAll.addEventListener("click", function () {
        readControls();
        location.href = "../index.html#" + buildHash(settings);
      });
    }

    // "Back to gallery" link — preserve settings
    var backLink = document.getElementById("back-link");
    if (backLink) {
      backLink.addEventListener("click", function (e) {
        e.preventDefault();
        readControls();
        location.href = "../index.html#" + buildHash(settings);
      });
    }

    // Download single image
    var dlImage = document.getElementById("download-image");
    if (dlImage) {
      dlImage.addEventListener("click", function () {
        downloadSingleImage(dlImage.getAttribute("data-image-id"), dlImage);
      });
    }

    // Download all images
    var dlAll = document.getElementById("download-all");
    if (dlAll) {
      dlAll.addEventListener("click", function () {
        downloadAllImages(dlAll);
      });
    }
  }

  // ---- Init ----

  function init() {
    loadSettings();
    populateControls();
    updateHash();
    attachHandlers();
    renderAll();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
