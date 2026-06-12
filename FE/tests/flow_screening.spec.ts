import { test, expect } from '@playwright/test';

test.describe('Screening Flow E2E', () => {
  test('User can navigate from Home to Screening', async ({ page }) => {
    // Navigasi ke halaman utama
    await page.goto('/');
    
    // Pastikan judul ada
    await expect(page.locator('h1').first()).toContainText('DyLeks');
    
    // Klik tombol Mulai Petualangan
    await page.click('text="Mulai Petualangan"');
    
    // Pastikan sudah masuk ke halaman screening
    await expect(page).toHaveURL(/.*\/screening/);
    await expect(page.locator('text=/Halaman Skrining/')).toBeVisible();
  });
});
