Project Requirements: V-See (ACDSee-style photo viewer)
1. Overview and Core Philosophy
Goal: Develop a high-performance desktop photo viewer application that replicates the core "browse, view, and slideshow" functionality of classic ACDSee (specifically version 20, non-subscription).

Primary Pain Point to Solve: The application must eliminate the slow initial loading times seen in modern viewers (like XnView MP or Photos). It must NOT recursively scan folders or build a massive database upon opening a large directory (e.g., a 300GB Camera folder).

Core Philosophy:

Speed is Paramount: Folder listing and image viewing must feel instantaneous.

File-System Based (No Import): The app acts as a direct window to the file system. It reads files where they sit. No "importing" process is required.

Lazy Loading: Only load information (thumbnails, metadata) for files currently visible on screen or imminent.

2. Target Technology Stack (For Cursor Context)
To achieve high-performance desktop GUI rendering and efficient I/O handling, the suggested stack is:

Language: Python 3.x

GUI Framework: PyQt6 (or PySide6) - Essential for native OS look-and-feel, speed, and advanced widgets like TreeViews and GraphicsScenes.

Image Processing: Pillow (PIL) - For fast thumbnail generation on background threads.

3. Functional Requirements
The application will have three main modes of operation, similar to ACDSee: "Manage" (Browser), "View" (Single Image), and "Slideshow".

3.1. "Manage" Mode (The Browser Interface)
Reference: screenshots/image_109.png

This is the default view when launching the application. It must feature a classic three-pane layout, resizable by splitters.

A. Folder Tree Pane (Left)

Display a native hierarchical tree view of the computer's file system.

Must load directory structures lazily (expanding a node only reads that specific folder's children). Does not pre-scan subfolders.

B. File List/Thumbnail Pane (Center/Right)

Display contents of the folder selected in the Tree Pane.

View Modes: Must support at least "Thumbnails" view (grid) and "Details" view (list with columns for Name, Size, Date).

Performance Requirement (Critical): When opening a folder with 10,000 images, the UI must not freeze. Thumbnails must be generated asynchronously on background threads and populate as the user scrolls (virtual scrolling).

Sorting: Ability to sort by Name, Date Modified, Date Taken (EXIF), and Size.

Supported File Types: JPG, PNG, GIF, BMP, TIFF, RAW formats (if feasible via libraries), plus common video containers (MP4, MOV - just show thumbnail icon for now).

C. Preview/Metadata Pane (Bottom Left - Optional for V1)

Show a larger preview of the single file selected in the Thumbnail Pane.

Show basic EXIF data (Camera model, ISO, Shutter speed, Date Taken).

3.2. "View" Mode (Single Image Viewer)
Reference: screenshots/image_108.png

Activated by double-clicking an image in "Manage" mode.

Interface: Clean, dark background, maximizing the image area.

Navigation:

Arrow keys (Left/Right) or on-screen buttons to move to the next/previous image in the current folder.

Mouse wheel to Zoom In / Zoom Out smoothly.

Click and drag to Pan around the image when zoomed in.

Display Options:

"Fit to Screen" (default).

"Actual Size" (1:1 pixel mapping).

Performance: Switching between high-resolution (e.g., 24MP+) images must be nearly instantaneous, using pre-fetching if necessary.

3.3. Slideshow Module
References: screenshots/image_104.png, image_105.png, image_106.png, image_107.png

A configurable slideshow engine launched from the current folder context.

Scope (image_104.png): Launch slideshow using all supported media in the currently selected folder.

Basic Settings (image_105.png):

Set slide duration (e.g., 3 seconds, 5 seconds).

Background music (implemented): Select a music folder independently from the photos folder; choose "No music", "All songs", or start from a specific song. Music auto-starts when slideshow runs. Music stops when slideshow stops, when the viewer closes, or when the main window closes. MP3 player in the main window includes transport controls and volume slider.

Background color selection (usually black).

Transitions: For V1, implement at least "None" (Cut) and "Fade". (Complex 3D transitions like "Cube" are lower priority).

Advanced Settings (image_106.png):

Scaling: Toggle between "Stretch to fit screen" (aspect fit, no distortion) or fill screen.

Loop: Option to restart slideshow after the last image.

Order: Toggle between "Forward" (filename order) and "Shuffle" (random).

Controls during playback:

Spacebar to Pause/Resume.

ESC to exit slideshow and return to View/Manage mode.

(Optional for V1) Text Overlay (image_107.png): Ability to display the Filename or Date Taken in a corner during the slideshow.

4. Non-Functional Requirements (NFRs)
Responsiveness: The application main thread (GUI) must never block for more than ~50ms. All file I/O and image decoding must happen on worker threads.

Memory Usage: The application should be mindful of RAM usage. It should not try to load thousands of full-resolution images into memory at once. It should act as a window, discarding data that scrolls out of view.

Cross-Platform: While initially developed on macOS, the use of Python and Qt should ensure it runs on Windows and Linux with minimal changes.

5. Future Scope (Not for V1)
Batch Renaming/Resizing tools.

Image editing features (crop, rotate, color correction).

Video playback support inside the viewer.

AI-powered features (e.g., "Find similar images").