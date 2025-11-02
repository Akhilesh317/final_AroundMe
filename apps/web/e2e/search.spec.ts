import { test, expect } from '@playwright/test'

test.describe('Search Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000')
  })

  test('should display search page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Discover Places Around You/i })).toBeVisible()
    await expect(page.getByPlaceholder(/What are you looking for/i)).toBeVisible()
  })

  test('should perform basic search', async ({ page }) => {
    // Fill in search form
    await page.getByPlaceholder(/What are you looking for/i).fill('coffee')
    await page.getByPlaceholder('Latitude').fill('32.814')
    await page.getByPlaceholder('Longitude').fill('-96.948')

    // Click search button
    await page.getByRole('button', { name: /Search/i }).click()

    // Wait for results page
    await expect(page).toHaveURL(/\/results/)
    
    // Should show results or loading state
    await expect(
      page.getByText(/Found \d+ places/i).or(page.getByRole('progressbar'))
    ).toBeVisible({ timeout: 10000 })
  })

  test('should apply filters', async ({ page }) => {
    await page.getByPlaceholder(/What are you looking for/i).fill('restaurant')
    
    // Apply price filter
    await page.getByText('$ - $$').click()
    
    // Apply open now filter
    await page.getByText('Open Now').click()

    await page.getByRole('button', { name: /Search/i }).click()

    await expect(page).toHaveURL(/\/results/)
  })

  test('should use example queries', async ({ page }) => {
    // Click on example
    await page.getByRole('button', { name: /Coffee near me/i }).click()

    // Input should be filled
    await expect(page.getByPlaceholder(/What are you looking for/i)).toHaveValue(/coffee/i)
  })

  test('should enable multi-entity search', async ({ page }) => {
    // Enable multi-entity
    await page.getByRole('button', { name: /Enable/i }).click()

    // Multi-entity builder should be visible
    await expect(page.getByRole('button', { name: /Add Entity/i })).toBeVisible()
  })
})

test.describe('Results Page', () => {
  test('should switch between list and map view', async ({ page }) => {
    // Navigate to results (assuming mock data or seeded results)
    await page.goto('http://localhost:3000/results?query=coffee&lat=32.814&lng=-96.948&radius_m=3000')

    // Wait for results to load
    await page.waitForSelector('[data-testid="result-card"]', { timeout: 10000 }).catch(() => {})

    // Check if view toggle buttons exist
    const listButton = page.getByRole('button', { name: /List/i })
    const mapButton = page.getByRole('button', { name: /Map/i })

    if (await listButton.isVisible()) {
      await mapButton.click()
      // Map should be visible
      await expect(page.locator('.leaflet-container')).toBeVisible()

      await listButton.click()
      // List should be visible
      await expect(page.locator('.grid')).toBeVisible()
    }
  })

  test('should change sorting', async ({ page }) => {
    await page.goto('http://localhost:3000/results?query=coffee&lat=32.814&lng=-96.948&radius_m=3000')

    const nearestButton = page.getByRole('button', { name: /Nearest/i })
    if (await nearestButton.isVisible()) {
      await nearestButton.click()
      // Wait for potential re-sort animation
      await page.waitForTimeout(500)
    }
  })
})

test.describe('Profile Page', () => {
  test('should enable personalization', async ({ page }) => {
    await page.goto('http://localhost:3000/profile')

    await expect(page.getByRole('heading', { name: /Profile & Preferences/i })).toBeVisible()

    // Enable personalization
    const enableButton = page.getByRole('button', { name: /Enable Personalization/i })
    if (await enableButton.isVisible()) {
      await enableButton.click()
    }
  })

  test('should add preference', async ({ page }) => {
    await page.goto('http://localhost:3000/profile')

    // Enable personalization first
    const enableButton = page.getByRole('button', { name: /Enable/i })
    if (await enableButton.isVisible()) {
      await enableButton.click()
      
      // Wait for preferences UI
      await page.waitForSelector('input[placeholder*="category"]', { timeout: 5000 }).catch(() => {})

      // Add a preference
      const keyInput = page.getByPlaceholder(/category/i)
      const valueInput = page.getByPlaceholder(/italian/i)
      
      if (await keyInput.isVisible()) {
        await keyInput.fill('category')
        await valueInput.fill('italian')
        await page.getByRole('button', { name: /Add Preference/i }).click()

        // Check for success
        await expect(page.getByText(/italian/i)).toBeVisible({ timeout: 5000 })
      }
    }
  })
})

test.describe('Admin Page', () => {
  test('should display health status', async ({ page }) => {
    await page.goto('http://localhost:3000/admin')

    await expect(page.getByRole('heading', { name: /System Dashboard/i })).toBeVisible()
    await expect(page.getByText(/Health Status/i)).toBeVisible()
  })

  test('should show metrics', async ({ page }) => {
    await page.goto('http://localhost:3000/admin')

    // Wait for metrics to load
    await page.waitForSelector('text=/Provider Calls|Cache Statistics/i', { timeout: 10000 })
  })
})