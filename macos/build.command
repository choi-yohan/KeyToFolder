#!/bin/bash
set -e
cd -- "$(dirname -- "$0")/.."
app_bundle="$PWD/KeyToFolder.app"
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT
mkdir -p "$app_bundle/Contents/MacOS" "$app_bundle/Contents/Resources"
for arch in arm64 x86_64; do
    xcrun swiftc macos/Launcher.swift -o "$build_dir/$arch" -target "$arch-apple-macosx11.0" -module-cache-path "$build_dir/cache" -framework Cocoa -framework WebKit
done
xcrun lipo -create "$build_dir/arm64" "$build_dir/x86_64" -output "$app_bundle/Contents/MacOS/KeyToFolder"
cp macos/Info.plist "$app_bundle/Contents/Info.plist"
cp macos/AppIcon.icns "$app_bundle/Contents/Resources/AppIcon.icns"
project_dir="$app_bundle/Contents/Resources/Project"
mkdir -p "$project_dir/macos"
for filename in app.py ui.html launch.command launch.bat requirements.txt LICENSE README.md README.ko-KR.md .gitignore; do
    cp "$filename" "$project_dir/$filename"
done
cp macos/Launcher.swift macos/Info.plist macos/AppIcon.icns macos/build.command "$project_dir/macos/"
xattr -cr "$app_bundle"
codesign --force --sign - "$app_bundle"
echo 'Built KeyToFolder.app'
