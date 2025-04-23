### Installation Command

Right-click inside the folder → Click "Open in Terminal"

OR open Command Prompt or PowerShell, then run:

Run this in your terminal :

```
pip install -r requirements.txt

```


### Install MiKTeX (Recommended for Windows):

Download from: https://miktex.org/download

Run the installer and follow the setup instructions.

During installation, choose the option to install missing packages on-the-fly (recommended).

Ensure `pdflatex` is in PATH:

After installation, MiKTeX usually adds itself to the system `PATH`, but you can check:

Open Command Prompt.

Type `pdflatex --version` to check if it's recognized.

If not, add the MiKTeX `bin` directory to your PATH manually. Example:

```
C:\Program Files\MiKTeX\miktex\bin\x64\

```
### Windows EXE compilation

1. Download the `zip` file, `extract` it to your desktop ( not inside any other folder )
2. Open your terminal App as `administrator` -> Right-click your terminal app (CMD, PowerShell, or VS Code terminal)
3. Navigate to that folder: `cd desktop`  ->  `ls`, then `cd foldername`
4. Use commnad
```
pyinstaller main.py --onefile
```
**or**
```
pyinstaller main.py --distpath build\dist --workpath build\build --specpath build\spec
```
6. Do not close the PowerShell window until the message **'Building EXE from EXE-00.toc completed successfully.'** is displayed
7. Follow for more: `https://github.com/Abhijeetbyte/Python-Script-to-Application`
