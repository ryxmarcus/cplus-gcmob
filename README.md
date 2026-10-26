# CP PLUS gCMOB APK analysis and camera client

`cplus_camera.py` connects to one CP PLUS/Dahua-compatible camera or DVR that you are authorized to access. It uses HTTP Digest authentication for device information and snapshots, and generates the common RTSP endpoint for use with a trusted player.

```powershell
# Password is prompted; it is not stored in shell history.
python .\cplus_camera.py --host 192.0.2.50 --username viewer --device-info
python .\cplus_camera.py --host 192.0.2.50 --username viewer --channels
python .\cplus_camera.py --host 192.0.2.50 --username viewer --channel 1 --snapshot .\output\camera-1.jpg
python .\cplus_camera.py --host 192.0.2.50 --username viewer --channel 1 --print-rtsp-template
```

The `--channels` command authenticates to the recorder and reads its configured channel names through the Dahua-compatible CGI API. The client does not scan networks, guess credentials, expose the RTSP password in output, or save credentials. CP PLUS device firmware can differ; confirm the model supports the CGI/RTSP endpoints before use.

The referenced [CCTV_Viewer](https://github.com/kaushalltiwari/CCTV_Viewer) project uses the same LAN CGI and RTSP protocol. This repository keeps the implementation intentionally small: use a trusted RTSP player with the printed template for live viewing, or fetch a JPEG snapshot directly with `--snapshot`.

## Local web app

Run the dependency-free web interface on a local machine or Codespace:

```bash
python3 web_app.py
```

Open port `8080`, enter the camera/NVR address and credentials, and use **Test connection and list channels**. The web app binds to all interfaces for Codespaces port forwarding, sends credentials only to the selected camera, and does not save them. Use the CLI or a trusted RTSP player for live video; the web interface currently provides channel testing and the existing snapshot workflow.

## APK analysis

This repository contains a reproducible workflow for inspecting a lawfully obtained CP PLUS gCMOB Android APK. It does not contain the original APK, signing keys, credentials, captured user data, or a claim that decompiled output is the original source code.

## Inputs

Place the APK at `input/gcmob.apk`. Record its origin and expected version before analysis. The APK remains ignored by Git.

## Tools

Install current releases of:

- JADX for readable Java/Kotlin-like decompilation
- Apktool for manifest, resources and smali extraction
- Android SDK `apkanalyzer` or `aapt2` for package metadata
- JDK `keytool` for certificate inspection

Make `jadx`, `apktool`, `apkanalyzer` and `keytool` available on `PATH`, then run:

```powershell
.\scripts\analyze-apk.ps1 -ApkPath .\input\gcmob.apk
```

The workflow writes generated files under `output/` and a concise evidence report under `reports/local/`. Review generated content for secrets or personal data before deciding what may be committed. Decompiled code may be incomplete or incorrect because of obfuscation, native libraries, dynamic loading and decompiler limitations.

## Repository policy

Commit only scripts, documentation, independently written findings, and source material you have permission to redistribute. Do not commit the APK or bulk decompiled proprietary code until ownership and redistribution rights are confirmed.
