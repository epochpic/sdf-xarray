# Installation

```{important}
To install this package, ensure that you are using one of the supported Python
versions [![Supported Python versions](https://img.shields.io/pypi/pyversions/sdf-xarray.svg)](https://github.com/epochpic/sdf-xarray)
```

There are several ways in which you can install <project:#sdf_xarray>. If you are unfamiliar with Python, [follow the guide below](#new-to-python). If you are already familiar with Python and `pip` then you can install this using the following.

Install sdf-xarray from PyPI with:

```bash
pip install sdf-xarray
```

or download this code locally:

```bash
git clone --recursive https://github.com/epochpic/sdf-xarray.git
cd sdf-xarray
pip install .
```

## New to Python?

### Installing uv

We recommend [installing uv](https://docs.astral.sh/uv/getting-started/installation/) which is a command line tool that can install both Python versions and packages. This tool is widely used in the Python community and is significantly faster than other tools that do the same. 

`````{tab-set}
````{tab-item} Linux/MacOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
````

````{tab-item} Windows
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
You might need to change the [execution policy](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.4#powershell-execution-policies) to allow running a script from the internet.
````
`````

You can then check `uv` is correctly installed by running:

```bash
uv --version
```

### Installing Python

If Python is already installed on your system then `uv` will detect and use it. If you don't have python already installed on your machine you can use `uv` to install it:

```console
uv python install 3.14
```
Once installed, it should be possible to run Python using 

```bash
python3.14 --version
```

### Setting up a virtual environment

Now that you've installed `uv` and have a supported Python version you need to create a [virtual environment](https://docs.astral.sh/uv/reference/cli/#uv-venv). You need to do this because Python doesn't allow you to install libraries globally on your system. From a folder of your choosing run the following command to create a subfolder called `.venv` containing all the Python libraries you install.

```bash
uv venv
```

Depending on your operating system you'll need to follow the activation command that appears after running `uv venv`. This will tell Python to use the libraries installed in this package.

### Installing sdf-xarray

Finally we can install <project:#sdf_xarray> to the `venv` using the following command. Any additional packages that can be installed using `pip` can also be installed using this method.

```bash
uv pip install sdf-xarray
```

### Getting an error about a missing `CMAKE_C_COMPILER`?

Are you getting an error that looks like this?

```bash
$ uv pip install sdf-xarray
Resolved 16 packages in 293ms
  x Failed to build `sdf-xarray==0.7.0`
  |-> The build backend returned an error
  `-> Call to `scikit_build_core.build.build_wheel` failed (exit status: 1)

      [stdout]
      *** scikit-build-core 0.12.2 using CMake 4.3.1 (wheel)
      *** Configuring CMake...
      loading initial cache file /tmp/tmp8ch254_2/build/CMakeInit.txt
      -- Configuring incomplete, errors occurred!

      [stderr]
      CMake Error at
      /nix/tmp/debug-tools/.cache/uv/builds-v0/.tmpa3v1oF/lib/python3.14/site-packages/cmake/data/share/cmake-4.3/Modules/CMakeDetermineCCompiler.cmake:48
      (message):
        Could not find the compiler specified in the environment variable CC:

        cc -pthread.
      Call Stack (most recent call first):
        CMakeLists.txt:3 (project)


      CMake Error: CMAKE_C_COMPILER not set, after EnableLanguage

      *** CMake configuration failed

      hint: This usually indicates a problem with the package or the build environment.
```

Don't panic, this error means you've not installed a `C` compiler onto your computer. 

````{tab-set}
```{tab-item} Linux
If you're on a fresh or recent Linux install then there's a good chance you might be missing a it, you can remedy this by running `sudo apt install build-essential` on Debian-based Linux systems such as Ubuntu.
```

```{tab-item} MacOS
Make sure you've installed the [Command Line Tools package](https://developer.apple.com/documentation/xcode/installing-the-command-line-tools/#Install-the-Command-Line-Tools-package-in-Terminal).
```

```{tab-item} Windows
If you've encountered this error then I have no idea... But I strongly recommending installing [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) and running a mini Ubuntu install on your machine instead of fighting windows.
```
````

### How do I run my Python scripts?

As long as you've "activated" your `venv` you can run a Python script from anywhere on your computer.
