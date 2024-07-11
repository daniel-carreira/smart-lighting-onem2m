# Smart Lighting over OneM2M Standard

Smart home automation systems have the potential to revolutionize the way we interact with our homes. However, the widespread adoption of these systems has been limited by challenges such as interoperability, security, and ease of use. To address these challenges, we propose a peer-to-peer network-based smart lighting system that utilizes the OneM2M standard for seamless communication among devices. Our proposed approach eliminates the need for a central hub, reducing potential points of failure and enhancing scalability. It also supports a diverse range of devices and protocols, leading to a more comprehensive and flexible smart home automation system.

## Architecture
<img src="/docs/imgs/arch.jpg" style="max-height:50vh;margin-left: auto;margin-right: auto;display: block;"/>

## Web
### > Switch
![Switch](/docs/imgs/switch.jpg)
### > Light Bulb
![Light Bulb](/docs/imgs/bulb.jpg)

## Usage
Supported only by **MacOS** or **Linux**.

1. Start the OneM2M instance **[Every device]**;
    > cd TinyOneM2M
    > makefile
    > ./server

2. Start MQTT instance in **[Switch]**;
3. Run ```python smart-switch.py``` **[Switch]**;
4. Run ```python smart-bulb.py``` **[Light Bulb]**;

## Docs
[Report](/docs/report.pdf)