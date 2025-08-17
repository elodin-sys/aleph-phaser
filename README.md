# Pictocopter

Deploy Phaser Integration to Aleph

Dependencies:
- install nix, I recommend Determinate installer [here](https://zero-to-nix.com/concepts/nix-installer/).
- setup local cross compile on MacOS via this guide [here](https://github.com/elodin-sys/elodin/blob/main/docs/internal/nix.md).


Connect to a powered Aleph (USB port opposite the B2B connector), test access via ssh:
```sh
ssh root@fde1:2240:a1ef::1
```

Once confirmed, run to build and deploy:
```sh
./deploy.sh -u root
```

Once you've built and deployed, you should be able to deploy without providing root credentials with user key auth (make sure to add the key from `ssh` to your ~/.ssh/ & agent):
```sh
./deploy.sh -u aleph-phaser
```
