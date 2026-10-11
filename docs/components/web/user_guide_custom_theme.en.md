# User Guide: Themes & Custom CSS (Enterprise Style)

This guide is intended for **administrators** and **operators** of the RTMS platform who wish to tailor the visual appearance, color palette, and corporate branding of the RTMS web console.

---

## 1. Accessing Theme Settings

1. Log into the RTMS console with an account having the **Administrator** role (`admin` or `superadmin`).
2. In the left navigation menu, click **Configuration** (or navigate to `/scanner`).
3. Scroll down the page to the section:
   > 🎨 **Custom CSS & Enterprise Theme**
4. Click the section header to expand the customization options.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎨 Custom CSS & Enterprise Theme                        [ Active Theme ] ▾ │
│    Fully customize branding colors, typography and global stylesheet        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Method 1: Apply a Ready-to-Use Theme in 1 Click (Recommended)

To immediately adopt a striking, high-contrast look distinct from the standard RTMS theme, 3 built-in themes are provided:

| Theme | Button | Visual Style |
| :--- | :---: | :--- |
| **Emerald Cyber** | 🟢 | Vibrant electric emerald (`#10b981`), deep midnight-pine surfaces (`#06120e`), emerald gradient buttons, and styled scrollbars. |
| **Royal Purple** | 🟣 | High-tech SOC purple (`#8b5cf6`), deep dark obsidian (`#0c0a17`), and subtle lilac highlights for a command center vibe. |
| **Cyber Gold** | 🟡 | Warm executive amber (`#f59e0b`), carbon surfaces (`#120e06`), and golden accents for an executive board aesthetic. |

### How to apply:
1. Click any preset button (e.g. **🟢 Emerald Cyber**).
2. The live preview is **immediately applied across your entire screen** in real time.
3. If satisfied, click the blue **"Save Theme"** button at the bottom right to deploy it for all users.
4. If you wish to revert without saving, click **"Cancel Preview"**.

---

## 3. Method 2: Quick Customization (Palette & Typography)

You can quickly adjust branding colors and fonts without writing CSS code:

1. **Primary Accent Color (`--accent-primary`)**:
   - Click the color swatch or enter your hex code (e.g. `#10b981`).
   - Controls action buttons, active navigation tabs, and key metrics.
2. **Secondary Accent Color (`--accent-secondary`)**:
   - Determines badges, subtle highlights, and hover states.
3. **Font Family**:
   - Choose from the dropdown:
     - *Default (Inter / Outfit)*
     - *Modern System (Apple / Windows)*
     - *Inter (Clean & Highly Legible)*
     - *Outfit (Modern & Sleek)*
     - *Roboto*
     - *JetBrains Mono (Console / Tech)*

Click **"Test / Live Preview"** to test, then click **"Save Theme"**.

---

## 4. Method 3: Import or Write Custom CSS (Advanced)

For teams requiring custom white-labeling, custom web fonts, or component redesigns:

### Importing a `.css` file
1. Click **"Upload .css"** (upload icon).
2. Select your stylesheet file (such as the provided `example-corporate-theme.css`).
3. The content is loaded into the editor instantly.
4. Toggle **"Enable Custom CSS Styling"** on.

### Key CSS Tokens:
You can override standard design tokens in your `:root` block:

```css
:root {
  --accent-primary: #10b981 !important;    /* Main brand accent */
  --accent-secondary: #34d399 !important;  /* Secondary accent */
  --bg-primary: #06120e !important;        /* Deep page background */
  --bg-secondary: #0b1e17 !important;      /* Panel and card background */
  --glass-bg: rgba(11, 30, 23, 0.85) !important; /* Semi-transparent backdrop */
  --border-color: rgba(52, 211, 153, 0.22) !important; /* Card borders */
  --radius-md: 10px !important;            /* Corner radius */
}
```

Click **"Test / Live Preview"** to verify, then **"Save Theme"** to persist.

---

## 5. Restoring Default RTMS Styling

If you ever wish to revert to original RTMS styling (royal blue and dark slate):
1. In the **Custom CSS & Enterprise Theme** section, click **"Reset to Default"** (red button).
2. Confirm the modal dialog.
3. All custom rules are cleared and default styling is instantly restored.

---

## 6. Emergency Safe Mode Bypass

> [!WARNING]
> **What if a malformed CSS rule hides buttons or breaks navigation?**

An emergency **Safe Mode** is natively built into RTMS:

1. In your browser's address bar, append `?safe_mode=true` to any RTMS URL.  
   *Example:* `http://rtms.local:8000/scanner?safe_mode=true`
2. Press **Enter**.
3. All custom CSS is completely bypassed for your session, and a recovery banner appears at the top right.
4. Navigate to the Configuration page to edit your stylesheet or click **"Reset to Default"**.
