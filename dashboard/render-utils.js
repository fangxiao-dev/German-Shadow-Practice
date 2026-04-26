(function (globalScope) {
  function formatResetHint(item) {
    const resetCount = Number(item?.reset_count || 0);
    if (!Number.isFinite(resetCount) || resetCount <= 0) {
      return null;
    }
    return `reset ${resetCount}x`;
  }

  const api = {
    formatResetHint,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }

  globalScope.shadowDashboardRenderUtils = api;
})(typeof window !== "undefined" ? window : globalThis);
