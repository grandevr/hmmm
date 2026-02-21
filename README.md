# HMMM 🤔
### Hotline Miami Mod Manager

Simple mod manager for Hotline Miami 2, to make the inconvenient thing a little less inconvenient. Vibe-coded, but fully tested.

Inspired by [Hotline Miami Mod Manager](https://github.com/cds-reis/hotline_miami_mod_manager). *(It didn't have Linux support, so I started working on this. 5 hours before it suddenly updated after 2 years with a Linux build. Sigh.)*

## Features
- **Easy mod installation** - select a music.wad file and/or as many .patchwad mods as you want, and HMMM will install them for you. No more searching for hidden folders to paste your files into.
- **One-click uninstall** - want to go back to vanilla? Just click a button.
- **Switching mods** - installed a bunch of campaigns and want to be able to switch back and forth or revisit them? Just double click another mod. HMMM will restore the vanilla state, and activate your new mod instead. HMMM will keep the others backed up for later.
- **Import and Export mod packages** - zip up however many mods you want, and other users will be able to import the whole pack in one click - with textures, sounds, and music in one file.
- **Cross-platform** - works on Windows and Linux. You can install it from AUR if you use Arch btw.

## Screenshots

## Installation
### Windows
Download the .exe, put it in a folder wherever you like, run it.

###Linux
Download the AppImage, put it in a folder wherever you like, run it.
If you're on Arch or an Arch-based distro like SteamOS, CachyOS, Bazzite etc. you can just pull the hmmm package from AUR (soon).

## Usage
After launching, press a button to find your vanilla hlm2_desktop_music.wad file, which is in your Steam folder (or SteamLibrary folder if you installed HM2 to a different drive), under /Steam/steamapps/common/Hotline Miami 2/
Once you select it, you'll see the manager window, where you'll see your list of mods (once they're installed). To install a mod, just press the button, select the .patchwad(s) and/or music.wad files you downloaded from the custom map's/campaign's Workshop page, name the mod, and press OK.
The installed mod won't be activated by default. To activate a mod, just double click it. To switch to a different mod, double click that one, and your currently active mod will be deactivated. To deactivate your active mod, just press the button on the bottom to revert to vanilla.
You can right click a mod to edit it (lets you rename it and add or delete wad files), delete it from HMMM entirely, or export a mod package. The mod package is just a zip file with the mod name and the .wad files inside it, but it makes mods for complex campaigns easier to share and install.
To import a mod package, just click the button and select a compatible zip file. 
