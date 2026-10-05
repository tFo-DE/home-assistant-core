# Changelog - PV Load Balancer

## [Unreleased] - 2026-05-25

### ✨ Improved - Professional Refactoring

#### Removed Dead Code
- **Removed:** `CONF_WALLBOX_MODBUS_HUB` constant (was never used in coordinator)
- **Removed:** `DEFAULT_WALLBOX_MODBUS_HUB` default value
- **Removed:** Wallbox Modbus Hub text field from config flow

#### Added Proper Configuration
- **Added:** `CONF_WALLBOX_PHASES_SELECT` - Select entity for phase switching (1/3 phases)
- **Added:** `CONF_WALLBOX_MAX_CURRENT_NUMBER` - Number entity for max current control
- **Added:** Entity selectors in config flow for both new fields
- **Added:** Validation for new entities in config flow

#### Refactored Coordinator
- **Changed:** Removed hardcoded entity IDs:
  - `select.alf_ace0195477_alfen_usable_phases2` → configurable
  - `number.alf_ace0195477_alfen_max_current_limit_s2` → configurable
- **Changed:** Entity IDs now read from config entry
- **Improved:** Integration now works with any Alfen wallbox, not just specific device

#### Maintained Compatibility
- **Kept:** `CONF_WALLBOX_SOCKET` for logging purposes
- **Note:** Existing config entries need to be reconfigured via UI to add new entity fields

### 📋 Migration Guide

**For existing installations:**
1. Go to Settings → Devices & Services → PV Load Balancer
2. Click "Configure"
3. Add the new required entities:
   - **Wallbox Phases Select:** `select.alf_ace0195477_alfen_usable_phases2`
   - **Wallbox Max Current Number:** `number.alf_ace0195477_alfen_max_current_limit_s2`
4. Save configuration

### 🎯 Benefits

- ✅ **Reusable:** Works with any Alfen wallbox or compatible device
- ✅ **Maintainable:** No hardcoded entity IDs in code
- ✅ **Clean:** Removed unused configuration options
- ✅ **Professional:** Proper config flow with entity selectors
