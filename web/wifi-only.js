/* Wi-Fi-only network gate for optional local-model downloads.
 * Fail closed: unknown connection type is NOT treated as Wi-Fi.
 * This module performs no network requests and stores no user data.
 */
(function (root) {
  "use strict";

  function readState() {
    var nav = root.navigator || {};
    var connection = nav.connection || nav.mozConnection || nav.webkitConnection || null;
    var online = nav.onLine === true;
    var type = connection && typeof connection.type === "string"
      ? connection.type.toLowerCase()
      : "unknown";
    var allowed = online && type === "wifi";

    return {
      allowed: allowed,
      online: online,
      connectionType: type,
      status: allowed ? "WIFI_READY" : (!online ? "OFFLINE" : (type === "unknown" ? "WIFI_STATUS_UNAVAILABLE" : "WIFI_REQUIRED")),
      message: allowed
        ? "Wi-Fi confirmado. Ação de rede pode ser oferecida após confirmação do usuário."
        : (!online
          ? "Sem conexão. Operação pausada."
          : (type === "unknown"
            ? "O navegador não informa o tipo de rede. Por segurança, download bloqueado."
            : "Conecte-se ao Wi-Fi. Dados móveis e outros tipos de rede são bloqueados."))
    };
  }

  function assertAllowed() {
    var state = readState();
    if (!state.allowed) {
      var error = new Error(state.status);
      error.code = state.status;
      throw error;
    }
    return state;
  }

  function watch(callback) {
    if (typeof callback !== "function") throw new TypeError("callback_required");
    var connection = root.navigator &&
      (root.navigator.connection || root.navigator.mozConnection || root.navigator.webkitConnection);
    var notify = function () { callback(readState()); };
    root.addEventListener("online", notify);
    root.addEventListener("offline", notify);
    if (connection && connection.addEventListener) connection.addEventListener("change", notify);
    notify();
    return function unsubscribe() {
      root.removeEventListener("online", notify);
      root.removeEventListener("offline", notify);
      if (connection && connection.removeEventListener) connection.removeEventListener("change", notify);
    };
  }

  root.AIBridgeWifiOnly = Object.freeze({
    readState: readState,
    assertAllowed: assertAllowed,
    watch: watch
  });
})(window);
