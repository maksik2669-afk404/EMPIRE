---
name: wishlist-alert-mechanics
description: Specification for wishlists, saved items, and automated Price Drop & Back in Stock trigger notifications in E-commerce.
argument-hint: [concept of wishlist, saved items, or price alert triggers]
allowed-tools: Read, Write
preset: e-commerce
lifecycle: any
business-model: b2c
domain: e-commerce
stage: any
output-artifact: document
---

# E-com Wishlist & Trigger Notifications (wishlist-alert-mechanics)

Design an E-commerce wishlist and automated notification engine: saved items collections, price drop alerts, restock triggers (Back in Stock), abandoned wishlist re-engagement, and collaborative gift registries.

## Process

1. **Design Wishlist UX & Collection Management:**
   - 1-tap save to favorites from PLP and PDP with size preference retention.
   - Thematic folder organization: "Summer Vacation", "Holiday Gifts", "Home Decor".
   - "Move All to Bag" bulk action with live inventory validation.

2. **Design Price Drop Trigger Mechanics:**
   - Automated price drop tracking triggered upon saving an item.
   - Push and email notification dispatches: "Price dropped on [Item] by 20%".
   - Visual "Price Dropped by $X" badge on saved item cards.

3. **Design Restock Notifications (Back in Stock):**
   - In-stock alert button replacing missing size variants on PDP.
   - Multi-channel delivery: App Push, SMS, WhatsApp, or Email.
   - Priority checkout windows (e.g., 2-hour exclusive purchase reservation).

4. **Design Social Sharing & Gift Registries:**
   - Public shareable URL for birthday/event wishlists.
   - Automated marking of fulfilled items to prevent duplicate gifting.

5. **Formulate Engagement & Conversion Metrics:**
   - Apply the mandatory 5-question test to every metric.

## Output Format

```markdown
# Wishlist & Automated Notification Specification: [Project Name]

## 1. Wishlist Architecture
- **Sync:** Server-side persistence for authenticated profiles; LocalStorage fallback for guests.
- **Organization:** Custom folders with social sharing capabilities.

## 2. Notification Dispatch Matrix
| Trigger Event | Preferred Channel | SLA / Delay | Message Copy |
| :--- | :--- | :--- | :--- |
| Price Drop >= 10% | App Push / Email | Within 15 minutes | "Price Drop! [Item] from your wishlist is now $45." |
| Back in Stock | App Push / SMS | Instant upon inbound receipt | "Size M is back in stock. Tap to purchase before it sells out!" |
| Inactive Wishlist (7d) | Email | 7-day inactivity | "Items in your saved list are running low on stock." |

## 3. Anti-Spam & Frequency Capping
- Maximum 2 push notifications per user per rolling 7-day window.
- Strict quiet hours suppression between 10:00 PM and 9:00 AM local recipient time.

## 4. Key Metrics
- **Wishlist-to-Cart Conversion:** % of saved items transferred to cart and purchased.
- **Price Drop Push CTR:** Click-through rate on price decrease notifications.
- **Restock Purchase Rate:** % of users buying within 24h of Back in Stock alert.
- **Wishlist Engagement MAU:** Share of monthly active users interacting with saved items.
```

## Guardrails

- Enforce strict frequency capping to prevent notification fatigue and app uninstalls.
- Do not use em-dashes. Use colons, periods, or standard hyphens.
- Every metric must pass the 5-question test.
