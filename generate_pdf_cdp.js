// generate_pdf_cdp.js
const { chromium } = require("playwright-core");
const { spawn } = require("child_process");
const path = require("path");

(async () => {
  console.log("🚀 Launching Termux native Chromium via CDP...");

  // Spawn Chromium with remote debugging enabled
  const browserProcess = spawn("chromium", [
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    "--remote-debugging-port=9222",
    "--hide-scrollbars"
  ]);

  // Wait for CDP to be ready
  console.log("⏳ Waiting for CDP connection (port 9222)...");
  await new Promise((resolve) => setTimeout(resolve, 2000));

  try {
    // Connect via Chrome DevTools Protocol
    const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
    const page = await browser.newPage();

    const filePath = path.resolve("./pa_aca_briefing_py2027_final.html");
    await page.goto(`file://${filePath}`, { waitUntil: "networkidle" });

    console.log("📄 Generating PDF with margins and landscape layout...");
    await page.pdf({
      path: "./final_package/pa_aca_briefing_py2027.pdf",
      format: "Letter",
      landscape: true,
      printBackground: true,
      margin: { top: "0.5in", bottom: "0.5in", left: "0.5in", right: "0.5in" }
    });

    await browser.close();
    console.log("✅ PDF generated via CDP.");
  } catch (err) {
    console.error("❌ CDP connection failed:", err.message);
    throw err;
  } finally {
    browserProcess.kill();
  }
})();
