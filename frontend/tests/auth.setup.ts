import { test as setup } from "@playwright/test";
import { firstSuperuser, firstSuperuserPassword } from "./config";

const authFile = "playwright/.auth/user.json";

setup("authenticate", async ({ page }) => {
    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(firstSuperuser);
    await page.getByLabel(/password/i).fill(firstSuperuserPassword);
    await page.getByRole("button", { name: /log in|sign in/i }).click();
    await page.waitForURL("/");

    // Workaround for WebKit on localhost:
    // WebKit does not accept Secure cookies on http://localhost, so we strip the Secure flag.
    // This affects the shared storage state for all browsers, which is fine for local testing.
    const context = page.context();
    const cookies = await context.cookies();
    const insecureCookies = cookies.map((cookie) => {
        if (cookie.secure) {
            return { ...cookie, secure: false };
        }
        return cookie;
    });
    await context.clearCookies();
    await context.addCookies(insecureCookies);

    await page.context().storageState({ path: authFile });
});
