# Parakeet Lip Sync

Parakeet Lip Sync is an automatic lip-syncing tool that helps to create 2d mouth animations from the audio recordings.

It is inspired from the existing lip-sync softwares like Papagayo, Yolo and Rhubarb. Currently, the existing lip-sync softwares do not use the latest deep learning techniques to generate the lip-syncs or they are not open-source.

Parakeet Lip Sync is an attempt to solve this problem. It uses the latest deep learning techniques to generate the qood quality lip-syncs and is open-source.

This project is under development. Don't be suprised if it crashes, burns, eats your lunch, or fails to behave as it's supposed to.

A video tutorial on how to use Parakeet Lip sync is coming soon.

## Todos for the project

- [x] A minimalistic GUI.
- [x] Automatic lip-sync.
- [x] Support for exporting Moho Timesheet (.dat).
- [x] Common keyboard shortcuts `ctrl + o`, `ctrl + s`, etc. (Wow!)
- [x] Audio waveform visualization with playback controls.
- [ ] Support for exporting Toei Digital Exposure Sheet (.xdts).
- [ ] A MouthView to view the generated output.
- [ ] Editable waveform timeline.

## How to use

### Using uv (recommended)

```bash
# Install uv if you haven't already
# https://docs.astral.sh/uv/getting-started/installation/

# Clone and run the application
git clone <repo-url>
cd parakeet-lipsync

# Run the application
uv run parakeet
```

### Development setup

```bash
# Sync dependencies
uv sync

# Run in development mode
uv run python -m parakeet_lipsync.main
```

## Keyboard Shortcuts

- `Ctrl+O` - Open audio file
- `Ctrl+S` - Save output
- `Space` - Play/Pause

## Screenshot

![Screentshot](resources/screenshot.png)
