// 프로덕션 환경을 대비한 보안 강화
window.addEventListener('DOMContentLoaded', () => {
    // Example: Expose a version variable to the renderer process
    window.versions = {
      node: process.versions.node,
      chrome: process.versions.chrome,
      electron: process.versions.electron
    };
  });
  