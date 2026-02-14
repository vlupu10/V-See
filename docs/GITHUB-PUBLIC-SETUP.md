# GitHub Settings for Public V-See Project

Follow these steps in order. All paths start from: **https://github.com/vlupu10/V-See** → **Settings**.

---

## Step 1: Branch protection (main)

1. In the left sidebar, click **Branches**
2. Under **Branch protection rules**, click **Add rule** (or edit existing rule for `main`)
3. Set **Branch name pattern** to `main`
4. Enable:
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass** (if you add CI later)
   - ✅ **Do not allow bypassing the above settings**
   - ✅ **Restrict who can push to matching branches** (optional: add yourself)
5. Click **Create** or **Save changes**

---

## Step 2: Pull request settings

1. In the left sidebar, click **General**
2. Scroll to **Pull Requests**
3. Enable:
   - ✅ **Always suggest updating pull request branches**
   - ✅ **Automatically delete head branches** (after merge)

---

## Step 3: Issue templates ✓ (already added)

Bug report and feature request templates are in `.github/ISSUE_TEMPLATE/`.  
Commit and push these files; GitHub will use them when creating new issues.

---

## Step 4: Release immutability

1. In **Settings** → **General**
2. Scroll to **Releases**
3. Enable: ✅ **Enable release immutability**

---

## Step 5: Social preview image

1. In **Settings** → **General**
2. Scroll to **Social preview**
3. Click **Edit**
4. Upload an image (1280×640px recommended)
5. Click **Save changes**

---

## Optional: Discussions / Wiki

- **Discussions**: Settings → General → Features → ✅ Discussions
- **Wiki**: Settings → General → Features → ✅ Wikis
