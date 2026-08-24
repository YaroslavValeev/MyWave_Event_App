(function () {
  "use strict";

  var analyticsEvents = {
    view: "mywave_event_app_card_viewed",
    select: "mywave_event_app_platform_selected",
    click: "mywave_event_app_download_clicked",
    success: "mywave_event_app_download_succeeded",
    error: "mywave_event_app_download_failed"
  };

  function DownloadCenter(root) {
    this.root = root;
    this.manifestUrl = root.dataset.manifestUrl;
    this.analyticsUrl = root.dataset.analyticsUrl || "/analytics/log";
    this.apiBase = this.manifestUrl.replace(/\/manifest\/?$/, "");
    this.artifacts = {};
    this.selectedId = null;
    this.previousFocus = null;
    this.viewTracked = false;
    this.bindElements();
    this.bindEvents();
    this.observeView();
    this.loadManifest();
  }

  DownloadCenter.prototype.bindElements = function () {
    this.tabs = Array.prototype.slice.call(this.root.querySelectorAll("[data-artifact-id]"));
    this.panel = this.root.querySelector("[data-artifact-panel]");
    this.fileState = this.root.querySelector("[data-file-state]");
    this.fileStateText = this.root.querySelector("[data-file-state-text]");
    this.downloadButton = this.root.querySelector("[data-download-button]");
    this.retryButton = this.root.querySelector("[data-retry-button]");
    this.liveRegion = this.root.querySelector("[data-live-region]");
    this.modal = this.root.querySelector("[data-download-modal]");
    this.confirmButton = this.root.querySelector("[data-confirm-download]");
  };

  DownloadCenter.prototype.bindEvents = function () {
    var self = this;
    this.tabs.forEach(function (tab, index) {
      tab.addEventListener("click", function () {
        self.selectArtifact(tab.dataset.artifactId, true);
      });
      tab.addEventListener("keydown", function (event) {
        var nextIndex;
        if (event.key === "ArrowRight" || event.key === "ArrowDown") nextIndex = (index + 1) % self.tabs.length;
        if (event.key === "ArrowLeft" || event.key === "ArrowUp") nextIndex = (index - 1 + self.tabs.length) % self.tabs.length;
        if (event.key === "Home") nextIndex = 0;
        if (event.key === "End") nextIndex = self.tabs.length - 1;
        if (typeof nextIndex === "number") {
          event.preventDefault();
          self.tabs[nextIndex].focus();
          self.selectArtifact(self.tabs[nextIndex].dataset.artifactId, true);
        }
      });
    });
    this.downloadButton.addEventListener("click", function () { self.openConfirm(); });
    this.retryButton.addEventListener("click", function () { self.refreshStatus(); });
    this.confirmButton.addEventListener("click", function () { self.startDownload(); });
    this.root.querySelectorAll("[data-modal-close]").forEach(function (button) {
      button.addEventListener("click", function () { self.closeConfirm(); });
    });
    this.modal.addEventListener("keydown", function (event) { self.handleModalKeydown(event); });
  };

  DownloadCenter.prototype.observeView = function () {
    var self = this;
    if (!("IntersectionObserver" in window)) {
      this.track(analyticsEvents.view, {});
      this.viewTracked = true;
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      if (!self.viewTracked && entries.some(function (entry) { return entry.isIntersecting; })) {
        self.viewTracked = true;
        self.track(analyticsEvents.view, {});
        observer.disconnect();
      }
    }, { threshold: 0.35 });
    observer.observe(this.root);
  };

  DownloadCenter.prototype.track = function (eventName, meta) {
    var payload = JSON.stringify({
      event: eventName,
      context: "projects/checklist-org",
      channel: "web",
      meta: Object.assign({ app_id: "mywave-event-app" }, meta || {})
    });
    try {
      fetch(this.analyticsUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
        keepalive: true,
        credentials: "same-origin"
      }).catch(function () {});
    } catch (_error) {}
  };

  DownloadCenter.prototype.loadManifest = function () {
    var self = this;
    this.setState("loading", "Загружаем варианты…");
    fetch(this.manifestUrl, { headers: { Accept: "application/json" }, credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("manifest_" + response.status);
        return response.json();
      })
      .then(function (manifest) {
        (manifest.artifacts || []).forEach(function (artifact) { self.artifacts[artifact.id] = artifact; });
        var readiness = self.root.querySelector("[data-app-readiness-text]");
        var appStatus = self.root.querySelector("[data-app-status]");
        if (manifest.app && manifest.app.readiness) {
          readiness.textContent = manifest.app.readiness;
          appStatus.textContent = manifest.app.readiness;
        }
        var first = self.tabs.length ? self.tabs[0].dataset.artifactId : null;
        if (first) self.selectArtifact(first, false);
      })
      .catch(function () {
        self.setState("error", "Не удалось загрузить каталог файлов.");
        self.retryButton.hidden = false;
        self.downloadButton.disabled = true;
        self.downloadButton.textContent = "Каталог недоступен";
        self.announce("Ошибка загрузки каталога. Нажмите «Повторить проверку».");
        self.track(analyticsEvents.error, { stage: "manifest" });
      });
  };

  DownloadCenter.prototype.selectArtifact = function (artifactId, shouldTrack) {
    if (!this.artifacts[artifactId]) return;
    this.selectedId = artifactId;
    this.tabs.forEach(function (tab) {
      var active = tab.dataset.artifactId === artifactId;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
      tab.tabIndex = active ? 0 : -1;
    });
    this.panel.setAttribute("aria-labelledby", "event-app-tab-" + artifactId);
    this.renderArtifact(this.artifacts[artifactId]);
    if (shouldTrack) this.track(analyticsEvents.select, { artifact_id: artifactId });
    this.refreshStatus();
  };

  DownloadCenter.prototype.renderArtifact = function (artifact) {
    this.root.querySelector("[data-artifact-label]").textContent = artifact.label;
    this.root.querySelector("[data-artifact-format]").textContent = artifact.format;
    this.root.querySelector("[data-artifact-version]").textContent = artifact.version || "Не опубликована";
    this.root.querySelector("[data-artifact-size]").textContent = artifact.size || "Уточняется";
    this.root.querySelector("[data-artifact-updated]").textContent = artifact.last_updated || "Не указана";
    this.fillList(this.root.querySelector("[data-artifact-requirements]"), artifact.requirements || []);
  };

  DownloadCenter.prototype.refreshStatus = function () {
    var self = this;
    var artifactId = this.selectedId;
    if (!artifactId) {
      this.loadManifest();
      return;
    }
    this.setState("loading", "Проверяем доступность…");
    this.retryButton.hidden = true;
    this.downloadButton.disabled = true;
    this.downloadButton.textContent = "Проверяем файл…";
    fetch(this.apiBase + "/" + encodeURIComponent(artifactId) + "/status", {
      headers: { Accept: "application/json" },
      credentials: "same-origin"
    })
      .then(function (response) {
        return response.json().then(function (body) {
          if (!response.ok) throw new Error(body.message || "status_" + response.status);
          return body;
        });
      })
      .then(function (artifact) {
        if (self.selectedId !== artifactId) return;
        self.artifacts[artifactId] = artifact;
        self.renderArtifact(artifact);
        self.setState(artifact.state, artifact.message);
        if (artifact.state === "available") {
          self.downloadButton.disabled = false;
          self.downloadButton.textContent = artifact.action_label;
        } else {
          self.downloadButton.disabled = true;
          self.downloadButton.textContent = "Файл временно недоступен";
        }
      })
      .catch(function () {
        if (self.selectedId !== artifactId) return;
        self.setState("error", "Ошибка проверки доступности.");
        self.downloadButton.disabled = true;
        self.downloadButton.textContent = "Не удалось проверить файл";
        self.retryButton.hidden = false;
        self.announce("Ошибка проверки файла. Доступна повторная попытка.");
        self.track(analyticsEvents.error, { artifact_id: artifactId, stage: "status" });
      });
  };

  DownloadCenter.prototype.setState = function (state, message) {
    this.fileState.className = "event-app-download__file-state is-" + state;
    this.fileStateText.textContent = message;
  };

  DownloadCenter.prototype.openConfirm = function () {
    var artifact = this.artifacts[this.selectedId];
    if (!artifact || artifact.state !== "available") return;
    this.track(analyticsEvents.click, { artifact_id: artifact.id, version: artifact.version });
    this.root.querySelector("[data-confirm-title]").textContent = "Скачать " + artifact.label;
    this.root.querySelector("[data-confirm-description]").textContent =
      "Вы выбрали " + artifact.platform + ". После подтверждения начнётся скачивание или откроется страница установки.";
    this.root.querySelector("[data-confirm-version]").textContent = artifact.version || "Не опубликована";
    this.root.querySelector("[data-confirm-format]").textContent = artifact.format;
    this.root.querySelector("[data-confirm-size]").textContent = artifact.size || "Уточняется";
    this.fillList(this.root.querySelector("[data-confirm-requirements]"), artifact.requirements || []);
    this.previousFocus = document.activeElement;
    this.modal.hidden = false;
    document.body.classList.add("event-app-modal-open");
    this.confirmButton.disabled = false;
    this.confirmButton.textContent = "Начать скачивание";
    this.modal.querySelector(".event-app-download__modal-close").focus();
  };

  DownloadCenter.prototype.closeConfirm = function () {
    if (this.modal.hidden) return;
    this.modal.hidden = true;
    document.body.classList.remove("event-app-modal-open");
    if (this.previousFocus && this.previousFocus.focus) this.previousFocus.focus();
  };

  DownloadCenter.prototype.handleModalKeydown = function (event) {
    if (event.key === "Escape") {
      event.preventDefault();
      this.closeConfirm();
      return;
    }
    if (event.key !== "Tab") return;
    var focusable = Array.prototype.slice.call(
      this.modal.querySelectorAll("button:not([disabled]), a[href], [tabindex]:not([tabindex='-1'])")
    ).filter(function (element) { return !element.hidden; });
    if (!focusable.length) return;
    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  DownloadCenter.prototype.startDownload = function () {
    var self = this;
    var artifact = this.artifacts[this.selectedId];
    if (!artifact) return;
    this.confirmButton.disabled = true;
    this.confirmButton.textContent = "Запускаем…";
    fetch(this.apiBase + "/" + encodeURIComponent(artifact.id) + "/handoff", {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: "{}",
      credentials: "same-origin"
    })
      .then(function (response) {
        return response.json().then(function (body) {
          if (!response.ok || !body.location) throw new Error(body.message || "handoff_" + response.status);
          return body;
        });
      })
      .then(function (handoff) {
        self.track(analyticsEvents.success, { artifact_id: artifact.id, version: artifact.version });
        self.closeConfirm();
        self.setState("success", handoff.message || "Скачивание успешно запущено.");
        self.announce("Скачивание успешно запущено.");
        window.setTimeout(function () {
          var link = document.createElement("a");
          link.href = handoff.location;
          link.rel = "noopener noreferrer";
          if (!handoff.open_in_new_tab) link.setAttribute("download", "");
          if (handoff.open_in_new_tab) link.target = "_blank";
          document.body.appendChild(link);
          link.click();
          link.remove();
        }, 250);
      })
      .catch(function (error) {
        self.closeConfirm();
        self.setState("error", "Ошибка скачивания. Повторите попытку.");
        self.retryButton.hidden = false;
        self.downloadButton.disabled = false;
        self.downloadButton.textContent = "Повторить скачивание";
        self.announce("Не удалось начать скачивание. Попробуйте ещё раз.");
        self.track(analyticsEvents.error, {
          artifact_id: artifact.id,
          stage: "handoff",
          reason: String(error.message || "unknown").slice(0, 80)
        });
      });
  };

  DownloadCenter.prototype.fillList = function (list, items) {
    list.textContent = "";
    items.forEach(function (item) {
      var li = document.createElement("li");
      li.textContent = item;
      list.appendChild(li);
    });
  };

  DownloadCenter.prototype.announce = function (message) {
    this.liveRegion.textContent = "";
    var self = this;
    window.setTimeout(function () { self.liveRegion.textContent = message; }, 20);
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-event-app-download]").forEach(function (root) {
      new DownloadCenter(root);
    });
  });
})();
