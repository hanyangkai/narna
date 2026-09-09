# Security Fix: Remove Leaked API Keys

## Critical Security Changes

This PR addresses NARNA-FREE-GLOBAL-001 - removal of hardcoded API keys from the frontend bundle.

### Changes Made

#### 1. Server-Side Key Denylist (`web/backend/app/auth.py`)
- Added `UAP_KEY_DENYLIST` environment variable support
- Format: comma-separated SHA256 hashes of revoked keys
- Returns `401` with message "API key revoked" for denied keys
- Both `get_org_from_api_key` and `resolve_api_key` check denylist

**Example usage:**
```bash
# Generate SHA256 hash of leaked key (do this securely, not in shell history)
echo -n "LEAKED_DEFAULT_KEY" | sha256sum

# Set in environment (in .env or deployment config)
UAP_KEY_DENYLIST="hash1,hash2,hash3"
```

#### 2. Frontend Key Removal (`web/frontend/src/`)
- **REMOVED**: `DEFAULT_DEV_KEY` constant from `api.ts`
- **ADDED**: `maskApiKey()` utility function for displaying key prefixes
- **UPDATED**: All pages to require explicit user API key input:
  - `Billing.tsx` - auth-gated with empty state
  - `Checkout.tsx` - already required key input
  - `Console.tsx` - requires key input
  - `RunDetail.tsx` - shows sign-in prompt
  - `SessionDetail.tsx` - shows sign-in prompt
  - `PackageDetail.tsx` - requires key for purchases
  - `Packages.tsx` - requires key for purchases
  - `ModelsSettings.tsx` - requires key input

#### 3. UI Security Improvements
- All API key inputs now use `type="password"` for masking
- Placeholder text guides users to enter `uap_live_…` format
- Empty states direct users to `/signup`, `/account`, or `/checkout`

#### 4. Soft Disclaimer Footer
- Added disclaimer to `Footer.tsx`:
  > "This service is provided as-is for research and open-source use. Not a certified legal entity.
  > No formal Terms of Service or Privacy Policy. Use at your own risk.
  > For production use, consult legal counsel."

### Post-Deployment Steps (Operations)

1. **Generate SHA256 hash of LEAKED_DEFAULT_KEY**:
   ```bash
   # Securely compute hash (not in version control)
   echo -n "uap_live_dev_local_key_change_in_prod" | sha256sum
   # Example output: abc123...def456
   ```

2. **Set environment variable on production servers**:
   ```bash
   # In .env or deployment config
   UAP_KEY_DENYLIST="<hash_of_leaked_key>"
   ```

3. **Rotate leaked key in database** (COO/Ed to coordinate):
   - Identify org_id=1 or affected organizations
   - Generate new API key for those orgs
   - Email new keys to affected users
   - Update any internal systems using the old key

4. **Monitor logs** for "API key revoked" errors after deployment

5. **Verify frontend bundle**:
   - Check new `index-*.js` bundle does NOT contain hardcoded key string
   - Search for literal "uap_live_dev_local_key" in built assets

### Security Verification Checklist

- [ ] No plaintext API keys in frontend bundle
- [ ] Server rejects requests with LEAKED_DEFAULT_KEY (after denylist configured)
- [ ] `/billing` page shows empty state when not authenticated
- [ ] All API key inputs use password masking
- [ ] Disclaimer footer visible on all pages
- [ ] Production env var `UAP_KEY_DENYLIST` configured
- [ ] Affected users notified of key rotation

### Expected Behavior After Deploy + Rotation

**Before denylist + rotation:**
- Old leaked key still works (until added to denylist)
- New users get fresh keys
- Frontend no longer ships with default fallback

**After denylist configured:**
- Requests with leaked key → `401 Unauthorized: API key revoked`
- Unauth users see sign-in prompts on `/billing`
- No auto-fetch of billing data without explicit user key

**After rotation:**
- Affected orgs have new keys
- Old leaked key permanently blocked
- No impact to other users

### Files Modified

**Backend:**
- `web/backend/app/auth.py` - added denylist checks

**Frontend:**
- `web/frontend/src/api.ts` - removed DEFAULT_DEV_KEY, added maskApiKey
- `web/frontend/src/pages/Billing.tsx` - auth-gated with empty state
- `web/frontend/src/pages/Console.tsx` - requires key input
- `web/frontend/src/pages/RunDetail.tsx` - sign-in prompt
- `web/frontend/src/pages/SessionDetail.tsx` - sign-in prompt  
- `web/frontend/src/pages/PackageDetail.tsx` - requires key for actions
- `web/frontend/src/pages/Packages.tsx` - requires key for actions
- `web/frontend/src/pages/ModelsSettings.tsx` - requires key input
- `web/frontend/src/components/Footer.tsx` - added disclaimer

### Testing Locally

```bash
# 1. Set denylist with test key hash
export UAP_KEY_DENYLIST="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"

# 2. Try to use test denied key
curl -H "Authorization: Bearer password" http://localhost:8000/v1/billing/status
# Expected: {"detail":"API key revoked"}

# 3. Build frontend and verify no hardcoded keys
cd web/frontend
npm run build
grep -r "uap_live_dev" dist/
# Expected: no matches
```

### Notes

- The leaked key value is NEVER mentioned in this PR or commit messages
- All references use "LEAKED_DEFAULT_KEY" placeholder
- Denylist uses SHA256 hashes, not plaintext keys
- Key rotation is out-of-band operation, not in this codebase
