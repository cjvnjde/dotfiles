pacman -Qqe | grep -v "$(pacman -Qqm)" > ./packages/official_packages.txt
pacman -Qqm > ./packages/aur_packages.txt

