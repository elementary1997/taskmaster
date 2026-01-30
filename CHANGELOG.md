# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-01-30

### Added
- **Auto-Update System**: 
    - Full update cycle: notification -> download -> safe replacement of the executable.
    - Automatic cleanup of old `.bak` files on the next launch.
    - Direct EXE downloading from GitHub releases.
- **Markdown Update Dialog**:
    - Beautifully formatted changelogs with headers, lists, and bold text support.
    - Integrated download progress bar and status notifications (badge indicator).
- **Task Filtering System**:
    - Added quick-access filters: **All**, **Active**, and Priority-based (🔴 High, 🟡 Medium, 🟢 Low).
- **Improved ToolTips**:
    - Fixed the "black box" issue on some systems.
    - Added rounded corners, padding, and theme-consistent background colors for better readability.
- **Drag & Drop Auto-Expand**: The "Completed Tasks" section now automatically expands when you hover over its header while dragging a task.
- **Improved Task Counting**: Added proper Russian pluralization for task counters (e.g., "1 задача", "2 задачи", "5 задач").
- **Smart UI**: The "Completed Tasks" section now automatically hides itself if there are no completed tasks.

### Changed
- **Build Optimization**: Refactored the Windows build process.
    - Significantly reduced executable size (from ~150MB down to ~60MB).
    - Drastically improved application startup time (from ~10s down to ~2s).
    - Optimized PyInstaller configuration to exclude redundant modules.
- **Smooth Animations**: Improved the collapsing/expanding behavior of the completed tasks section with smoother transitions.

### Fixed
- Fixed drag-and-drop issues where tasks sometimes failed to move to the "Completed" section.
- Fixed layout "jumping" when toggling the visibility of completed tasks.
- Improved error handling for the update system (handling 404 errors when no releases are published yet).
- Corrected various UI alignment and scaling issues in the settings and about dialogs.
