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
      el.value = settings[key];
      // Update range slider labels
      var valSpan = document.getElementById(key + "-val");
      if (valSpan) valSpan.textContent = settings[key];
    });
  }

  function readControls() {
    Object.keys(DEFAULTS).forEach(function (key) {
      var el = document.getElementById(key);
      if (el) settings[key] = el.value;
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

      // Label text
      var text = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "text"
      );
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

      text.setAttribute("x", tx);
      text.setAttribute("y", ty);
      text.setAttribute("fill", color);
      text.setAttribute("font-size", fontSize);
      text.setAttribute("font-family", "monospace");
      text.setAttribute("text-anchor", anchor);
      // Background for readability
      text.setAttribute("stroke", "#000");
      text.setAttribute("stroke-width", "3");
      text.setAttribute("paint-order", "stroke");
      text.textContent = labelStr;
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
      var event = el.tagName === "SELECT" ? "change" : "input";
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
