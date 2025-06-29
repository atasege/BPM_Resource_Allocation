
# run this script in terminal after making it executable

# to innstall system packages
sudo dnf install python3.10 python3-pip gcc -y

# install pipenv from pip
pip3 install --user pipenv

# install pyenv
curl https://pyenv.run | bash

# adding to path
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
export PIPENV_YES=1

# make it permanent
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'export PIPENV_YES=1' >> ~/.bashrc

# install everything from pipfile.lock
pipenv install
