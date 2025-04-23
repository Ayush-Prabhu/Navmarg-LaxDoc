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
