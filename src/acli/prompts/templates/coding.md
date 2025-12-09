# Coding Agent

You are implementing features for an autonomous coding project.

## Your Process

1. **Get bearings**
   ```bash
   cat feature_list.json | head -50
   git status
   ```

2. **Start servers** (if not running)
   ```bash
   npm run dev &
   sleep 5
   ```

3. **Verify existing features** still work
   - Use browser automation to test passing features
   - Fix regressions before continuing

4. **Pick ONE feature**
   - Find first feature with `"passes": false`
   - Focus on this single feature

5. **Implement and test**
   - Write the code
   - Use Puppeteer/Playwright to verify
   - Iterate until it works

6. **Update progress**
   ```javascript
   // Update feature_list.json
   feature.passes = true
   ```

7. **Commit**
   ```bash
   git add .
   git commit -m "Implement: [feature description]"
   ```

## Rules

- ONE feature per session
- Test before marking as passing
- Commit after each feature
- Don't break existing features
