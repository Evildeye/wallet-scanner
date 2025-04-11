window.addEventListener("DOMContentLoaded", () => {
  const fadeElements = document.querySelectorAll(".fade-in");
  fadeElements.forEach(el => {
    el.style.opacity = 1;
    el.style.transform = "translateX(0)";
  });
});
